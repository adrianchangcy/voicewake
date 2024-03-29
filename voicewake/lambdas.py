#py
import json
import subprocess
import re
import math
import functools
import os
from datetime import datetime

#Django
from django.core.files.base import ContentFile

#AWS
import boto3
from botocore.exceptions import ClientError
# from botocore.config import Config



#every lambda has ._sample_lambda_code() to show what to write



class AWSLambdaNormaliseAudioClips:

    #context
        #let backend API determine file extensions of processed/unprocessed keys
        #no need to immediately delete unprocessed object
            #expiry of S3 URL =/= expiry of reply
            #URL can still be used for upload within their time difference
    #process
        #normalise --> copy to new bucket --> return info
    #how to troubleshoot
        #at subprocess, do check=False, then get subprocess.run().stderr

    def __init__(
        self,
        is_lambda:bool,
        s3_region_name:str='',
        s3_aws_access_key_id:str='',
        s3_aws_secret_access_key:str='',
        unprocessed_object_key:str='',
        processed_object_key:str='',
        unprocessed_bucket_name:str='',
        processed_bucket_name:str='',
        processed_file_extension:str='mp3',
        subprocess_timeout_s:int=10,
        use_timer:bool=False,
    ):

        self.is_lambda = is_lambda
        self.s3_region_name = s3_region_name
        self.unprocessed_object_key = unprocessed_object_key
        self.processed_object_key = processed_object_key
        self.unprocessed_bucket_name = unprocessed_bucket_name
        self.processed_bucket_name = processed_bucket_name
        self.processed_file_extension = processed_file_extension
        self.subprocess_timeout_s = subprocess_timeout_s
        self.use_timer = use_timer

        #task duration
        self.lambda_timers_s = {}

        if is_lambda is True:

            #with ffmpeg-arm64.zip/bin/ffmpeg, stored in S3, and loading as Layer in Lambda
            self.ffprobe_path = '/opt/bin/ffprobe'
            self.ffmpeg_path = '/opt/bin/ffmpeg'

        else:

            #with Windows environment variables
            self.ffprobe_path = 'ffprobe'
            self.ffmpeg_path = 'ffmpeg'

        #in the case of mp3, both codec and format/container are the same
        #mp3 can only choose 32000/44100/48000 sample rate
        #mp3 sample rate of 44100 and 48000 has big difference in quality with minimal size difference, as long as small
        self.desired_codec = self.processed_file_extension
        self.desired_format = self.processed_file_extension
        self.desired_sample_rate = "48k"

        #dBFS has max 0dB (loudest), min of approx. 6dB per bit, e.g. 16-bit will have 96dB floor
        # >0 will cause clipping
        #since we need 0 to 1 to draw peaks at frontend, but we don't know our floor (lack of bit depth info),
        #we assume via ffmpeg's silencedetect of default -60dB
        #update 2023-08-22: -60 is too high, with peaks near 1, so trying -99
        self.dbfs_floor = -99

        self.bucket_quantity = 20

        #other data
        self.audio_file = None
        self.audio_file_duration_s = None
        self.audio_volume_peaks = None

        #s3

        try:

            if is_lambda is True:

                self.s3_client = boto3.client(
                    service_name='s3',
                    region_name=s3_region_name,
                )

            else:

                self.s3_client = boto3.client(
                    service_name='s3',
                    region_name=s3_region_name,
                    aws_access_key_id=s3_aws_access_key_id,
                    aws_secret_access_key=s3_aws_secret_access_key,
                )

        except ClientError:

            raise


    def _start_task_timer(self, task_name:str):

        self.lambda_timers_s[task_name] = datetime.now()


    def _stop_task_timer(self, task_name:str):

        self.lambda_timers_s[task_name] = (
            datetime.now() - self.lambda_timers_s[task_name]
        ).total_seconds()


    @staticmethod
    def task_timer_decorator(passed_function):

        @functools.wraps(passed_function)
        def inner(*args, **kwargs):

            self = args[0]

            if self.use_timer is False:

                return passed_function(*args, **kwargs)

            #must make sure _stop_task_timer() is always called after _start_task_timer()
            #else we end up with just datetime object, and Lambda will fail to serialize it

            self._start_task_timer(passed_function.__name__)

            try:

                result = passed_function(*args, **kwargs)

                self._stop_task_timer(passed_function.__name__)

                return result

            except:

                self._stop_task_timer(passed_function.__name__)
                raise

        return inner


    @staticmethod
    def create_return_response_on_ping():

        #check via lambda_event.get('is_ping') is True

        return {
            'lambda_status_code': 200,
            'lambda_message': '',
        }


    def test_retrieve_unprocessed_audio_file_local(self, audio_file_path:str):

        with open(audio_file_path, 'rb+') as target_file:

            self.audio_file = target_file.read()


    def test_store_processed_audio_file_local(self, audio_file_path:str):

        with open(audio_file_path, 'w') as target_file_to_overwrite:

            target_file_to_overwrite.seek(0)

            for chunk in ContentFile(self.audio_file).chunks():

                #remove bytes starting from position 0
                target_file_to_overwrite.truncate(0)

                #write
                target_file_to_overwrite.write(chunk)


    @task_timer_decorator
    def retrieve_unprocessed_audio_file(self):

        response = self.s3_client.get_object(
            Bucket=self.unprocessed_bucket_name,
            Key=self.unprocessed_object_key
        )

        #StreamingBody can only use .read() once, and does not contain .seek()
        #since our files are not large, we can load all into memory in this way
        self.audio_file = response['Body'].read()


    @task_timer_decorator
    def prepare_info_before_normalise(self):

        #format
            #this gets all keys, compared to 'format=duration', which returns only duration

        result = subprocess.run(
            [
                self.ffprobe_path,
                '-v', 'error',
                '-show_entries', 'format',
                '-show_streams',
                '-select_streams', 'a',
                '-of', 'json',
                '-i', 'pipe:0',
            ],
            input=self.audio_file,
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        self.audio_file_info = json.loads(result.stdout)

        #validate everything
        self._validate_info_before_normalise()


    def _validate_info_before_normalise(self):

        if self.audio_file_info is None:

            raise ValueError('No self.audio_file_info to validate.')
        
        #audio_file_info['streams'] can have multiple dicts if there's not only audio in it
        #e.g. a flac file from an album for test has a jpeg in it with ['index'] == 1
        #don't know whether the index order is always fixed, hence the loop

        #we don't care about codec
        #we have "-select_streams a" to tell us that no audio stream exists
        if len(self.audio_file_info['streams']) == 0:

            raise ValueError('No audio stream found.')


    @task_timer_decorator
    def normalise_and_overwrite_audio_file(self):

        #"loudnorm=I=-16:TP=-1.5:LRA=11" is from loudnorm docs on EBU R 128
        #"loudnorm=I=-23:LRA=7:TP=-2" is from ffmpeg-normalize on EU's LUFS -23 regulation
        loudnorm_args = "loudnorm=I=-23:TP=-2:LRA=7"

        #I is LUFS
        #LRA is loudness range, i.e. range between softest and loudest parts
        #TP is true peak, -2 seems common, just be sure to give enough headroom towards 0, and never over 0

        #first pass, get measurement
        ffmpeg_cmd = subprocess.run(
            [
                self.ffmpeg_path,
                "-i", "pipe:0",
                "-af", loudnorm_args + ":print_format=json",
                '-f', "null", "/dev/null"
            ],
            input=self.audio_file,
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        #get print string from stderr
        first_pass_data = ffmpeg_cmd.stderr.decode()

        #construct our json string
        #this will work as long as entire print string only has one {}
        first_pass_dict = re.search(r"(\{[\s\S]*\})", first_pass_data)[0]

        if first_pass_dict is None:

            raise ValueError("Regex could not find the data needed for first_pass_dict")

        #transform into proper dict
        first_pass_dict = json.loads(first_pass_dict)
        first_pass_dict = dict(first_pass_dict)

        #prepare -af values for second pass
        #can't directly .format() here, must call the variable again
        ffmpeg_cmd_af = loudnorm_args +\
            ":measured_I={0}" +\
            ":measured_LRA={1}" +\
            ":measured_TP={2}" +\
            ":measured_thresh={3}" +\
            ":offset={4}" +\
            ":linear=true:print_format=summary"
        
        ffmpeg_cmd_af = ffmpeg_cmd_af.format(
            first_pass_dict["input_i"],
            first_pass_dict["input_lra"],
            first_pass_dict["input_tp"],
            first_pass_dict["input_thresh"],
            first_pass_dict["target_offset"]
        )
        
        #do second pass, get file
        ffmpeg_cmd = subprocess.run(
            [
                self.ffmpeg_path,
                "-i", "pipe:0",
                "-af", ffmpeg_cmd_af,
                "-ar", self.desired_sample_rate,           #sample rate; mp3 can only choose 32000/44100/48000
                # "-b:a", "124k",         #bit rate, not sure if safe/redundant/necessary
                "-c:a", self.desired_codec,          #codec; a is audio, v is video
                "-f", self.desired_format, "pipe:1"   #f is format; for disk files, can just write "my_folder/file.mp3"
            ],
            input=self.audio_file,
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        self.audio_file = ffmpeg_cmd.stdout


    @task_timer_decorator
    def get_duration_after_normalise(self):

        #we have to do this only after passing through ffmpeg, e.g. normalisation
        #otherwise, some original files will error when seeking via '-read_intervals' and arbitary '999999'

        #'-show_packets', '-read_intervals' + '999999'
            #for file duration, getting from packets is more reliable than metadata such as format=duration:
            #guarantee that -read_intervals, in seconds, is >= file duration, via arbitrarily large value
            #absolute single value will become absolute start position, so start from last packet
            #will fall back to last packet when value is too big
            #this is better than loading all packets into memory just to get [-1]
        #format
            #this gets all keys, compared to 'format=duration', which returns only duration
        #'-show_entries', 'format'
            #not affected by us skipping packets via -read_intervals

        result = subprocess.run(
            [
                self.ffprobe_path,
                '-v', 'error',
                '-show_entries', 'format',
                '-show_packets',
                '-read_intervals', '999999',
                '-show_streams',
                '-select_streams', 'a',
                '-of', 'json',
                '-i', 'pipe:0',
            ],
            input=self.audio_file,
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        audio_file_info = json.loads(result.stdout)

        #determine audio_file_duration_s via last packet's pts_time
        #round off duration to int, floor is preferred for frontend slider
        self.audio_file_duration_s = math.floor(
            float(audio_file_info['packets'][-1]['pts_time'])
        )


    @task_timer_decorator
    def get_peaks_by_buckets(self) -> list[float]:

        #call this after normalisation

        #get duration
        #get sample rate
        #asetnsamples = (duration / x buckets) * sample rate
        #expect x + 1 buckets output, so compare second last and last bucket and select the one with higher peak

        #to get highest peak per x, add "asetnsamples=x" after amovie, i.e. chunk size, e.g. "amovie=...,asetnsamples=x,..."
        #e.g. if file is 48000Hz frequency, i.e. 48000 samples/sec, asetnsamples=48000 gives you 1 sec/bucket

        #get necessary info
        sample_rate = int(self.audio_file_info['streams'][0]['sample_rate'])

        #calculate appropriate sample rate to get bucket_quantity + 1
        #math.floor() is important to guarantee we always get surplus buckets, i.e. just compare last buckets
        #compared to math.ceil(), which may give us less buckets than we need, i.e. must maybe create last fake bucket
        asetnsamples = math.floor(self.audio_file_duration_s / self.bucket_quantity * sample_rate)
        
        #must escape ":"
        ffprobe_i = 'amovie=pipe\\\\:0,asetnsamples=%s,astats=metadata=1:reset=1' % (str(asetnsamples))

        #get peaks
        result = subprocess.run(
            [
                self.ffprobe_path,
                '-v', 'error',
                '-f', 'lavfi',
                '-i', ffprobe_i,
                '-show_entries', 'frame_tags=lavfi.astats.Overall.Peak_level',
                '-of', 'json'
            ],
            input=self.audio_file,
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        result = json.loads(result.stdout)

        #extract peaks
        audio_volume_peaks = []

        for count in range(self.bucket_quantity):

            #we fill the bucket to full first, then use last stored bucket to evaluate extra buckets
            peak_to_store = 0

            #value is in dBFS, max 0, min is approx. 6dB per bit depth
            #so bigger negative value means more quiet
            peak_to_store = float(result['frames'][count]['tags']['lavfi.astats.Overall.Peak_level'])

            #prevent exceeding floor
            if peak_to_store < self.dbfs_floor:

                peak_to_store = self.dbfs_floor

            #should never have > 0dB (will produce audio clipping)
            if peak_to_store > 0:
                
                raise ValueError('Audio normalisation had failed, as there were above 0dBFS peaks detected.')

            #get percentage
            # -x / -y will always be positive
            peak_to_store = peak_to_store / self.dbfs_floor

            #invert percentage
            peak_to_store = 1 - peak_to_store

            #get 0 to 1 value
            peak_to_store = peak_to_store * 1

            #truncate
            peak_to_store = float(round(peak_to_store, 2))

            #while audio_volume_peaks is not yet full, fill until full
            if count < self.bucket_quantity:

                audio_volume_peaks.append(peak_to_store)
                continue

            #handle extra buckets
            #store the higher peak between last stored peak and current peak
            if audio_volume_peaks[self.bucket_quantity] < peak_to_store:

                audio_volume_peaks[self.bucket_quantity] = peak_to_store

        self.audio_volume_peaks = audio_volume_peaks

        return audio_volume_peaks


    @task_timer_decorator
    def store_processed_audio_file(self):

        return self.s3_client.put_object(
            Bucket=self.processed_bucket_name,
            Key=self.processed_object_key,
            Body=self.audio_file
        )


    def get_default_return_response(self):

        response = {
            'lambda_status_code': 200,
            'lambda_message': '',
            'lambda_timers_s': self.lambda_timers_s,
            'audio_volume_peaks': self.audio_volume_peaks,
            'audio_duration_s': self.audio_file_duration_s,
            'lambda_dump': {},
        }

        return response


    @staticmethod
    def _sample_lambda_code():

        return '''
            import os
            import json
            import subprocess
            import re
            import math
            import boto3
            import functools
            from datetime import datetime
            from botocore.exceptions import ClientError

            #copy & paste class here

            def lambda_handler(event, context):
                
                #check if just pinging
                
                if event.get('is_ping') is True:
                    
                    return AWSLambdaNormaliseAudioClips.create_return_response_on_ping()
                
                #proceed

                normalise_class = AWSLambdaNormaliseAudioClips(
                    is_lambda=True,
                    s3_region_name=event.get('s3_region_name'),
                    s3_aws_access_key_id='',
                    s3_aws_secret_access_key='',
                    unprocessed_object_key=event.get('unprocessed_object_key'),
                    processed_object_key=event.get('processed_object_key'),
                    unprocessed_bucket_name=event.get('unprocessed_bucket_name'),
                    processed_bucket_name=event.get('processed_bucket_name'),
                    processed_file_extension=os.environ.get('AUDIO_CLIP_PROCESSED_FILE_EXTENSION', 'mp3'),
                    subprocess_timeout_s=int(os.environ.get('AWS_LAMBDA_NORMALISE_TIMEOUT_S', 10)),
                    use_timer=event.get('use_timer', False),
                )
                
                return normalise_class.main()
        '''


    def main(self):

        #made no sense to check if processed audio_file exists,
        #since logic only calls ffmpeg when checked to not be processed
        #if processed audio_file already exists, but disaster happened, and output wasn't recorded,
        #then there's no othe way but to run ffmpeg again to get required info

        try:

            self.retrieve_unprocessed_audio_file()
            self.prepare_info_before_normalise()
            self.normalise_and_overwrite_audio_file()
            self.get_duration_after_normalise()
            self.get_peaks_by_buckets()
            self.store_processed_audio_file()

            return self.get_default_return_response()

        except ClientError as e:

            error_response = self.get_default_return_response()

            error_response['lambda_status_code'] = e.response['ResponseMetadata']['HTTPStatusCode']
            error_response['lambda_message'] = e.response['Error']['Message']
            error_response['lambda_dump'] = e.response

            return error_response

        except subprocess.CalledProcessError as e:

            error_response = self.get_default_return_response()

            error_response['lambda_status_code'] = 400
            error_response['lambda_message'] = "Uploaded file could not be processed."

            return error_response

        except Exception as e:

            raise


