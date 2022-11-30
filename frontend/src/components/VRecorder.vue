<template>
    <div class="text-theme-black text-center">
        <div class="w-fit h-fit text-left">
            <VInputLabel for="click-to-record">{{propLabelText}}</VInputLabel>
        </div>
        <div class="grid grid-rows-2 grid-cols-4 grid-flow-col place-items-center text-center gap-x-2">
            <VActionButtonMedium
                id="click-to-record"
                @click.prevent="recorderStart()"
                aria-label="record"
                :class="[
                    recorder_state !== undefined && recorder_state !== 'stopped' ? 'col-span-1' : 'col-span-4',
                    'w-full row-span-2 p-2 transition-colors duration-200 ease-in-out'
                ]"
                :propIsDisabled="recorder_state !== undefined && recorder_state !== 'stopped'"
            >
                <div
                    v-if="recorder_state !== undefined && recorder_state !== 'stopped'"
                    class="relative w-full h-full"
                >
                    <div
                        ref="volume_analyser_circle_0"
                        class="w-0 h-0 absolute left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-orange-500/60"
                    ></div>
                    <div
                        ref="volume_analyser_circle_1"
                        class="w-0 h-0 absolute left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-orange-500/40"
                    ></div>
                    <div
                        ref="volume_analyser_circle_2"
                        class="w-0 h-0 absolute left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-orange-500/20"
                    ></div>
                </div>
                <i v-else class="fas fa-microphone-lines"></i>
            </VActionButtonMedium>
            <div
                :class="[
                    recorder_state !== undefined && recorder_state !== 'stopped' ? 'block' : 'hidden',
                    'row-start-1 row-span-1 col-span-2'
                ]"
            >
                <span class="text-xl">{{current_duration_pretty}} ~ {{max_recording_duration_ms_pretty}}</span>
            </div>
            <VActionButtonSmall
                @click.prevent="recorderPauseResume()"
                aria-label="pause or resume"
                :class="[
                    recorder_state !== undefined && recorder_state !== 'stopped' ? 'block' : 'hidden',
                    'row-start-2 row-span-1 col-span-2 w-full'
                ]"
            >
                <i
                    :class="[
                        (recorder_state === 'recording' ? 'fas fa-pause' : 'fas fa-pause'),
                        (recorder_state === 'paused' ? 'fas fa-play' : 'fas fa-pause'),
                        ''
                    ]"
                ></i>
            </VActionButtonSmall>
            <VActionButtonMedium
                @click.prevent="recorderStop()"
                aria-label="end recording"
                :class="[
                    recorder_state !== undefined && recorder_state !== 'stopped' ? 'block' : 'hidden',
                    'col-start-4 row-span-2 col-span-1 w-full p-4'
                ]"
            >
                <i class="fas fa-check"></i>
            </VActionButtonMedium>
        </div>
        <div>
            {{user_recording_input}}
        </div>
        <!-- currently don't allow file submission, but store file here for final form submit -->
        <!-- for file submission: <form method="POST" enctype="multipart/form-data"></form> -->
        <input type="file" ref="audio_upload" accept=".mp3, .webm" class="hidden" required>
    </div>
</template>


<script setup>

    import VActionButtonSmall from './VActionButtonSmall.vue';
    import VActionButtonMedium from './VActionButtonMedium.vue';
    import VInputLabel from './VInputLabel.vue';
</script>

<script>

    const recordRTC = require('/node_modules/recordrtc/RecordRTC.min.js');
    import anime from 'animejs';

    export default {
        data(){
            return {
                stream: undefined,  //for defining recorder instances
                volume_analyser: undefined,
                volume_analyser_interval: undefined,
                recorder: undefined,
                time_interval: 200, //milliseconds
                recorder_state: undefined,
                user_recording_input: null,
                final_blob: null,
                final_file: null,
                is_recording: false,
                current_duration: 0,    //milliseconds
                current_duration_pretty: '00:00',

                //default values
                //webm, despite being able to contain video media, is seamlessly handled by <audio>
                max_audio_file_size_mb: 10,
                audio_file_extensions_allowed: ['mp3','webm'],
                max_recording_duration_ms: 1000 * 60 * 2,    //2 minutes
                max_recording_duration_ms_pretty: new Date(1000 * 60 * 2).toISOString().substring(14, 19),
            };
        },
        mounted(){

            //NOTE
            //no need to be alarmed if it picks up nothing from browser audio
        },
        components: {
            VActionButtonSmall,
            VActionButtonMedium,
            VInputLabel,
        },
        props: {
            propLabelText: String,
        },
        watch: {
            final_file(new_value){

                this.$emit('hasNewRecording', new_value);
            },
            is_recording(new_value){

                this.$emit('isRecording', new_value);
            },
        },
        emits: ['hasNewRecording', 'isRecording'],
        methods: {
            handleVolumeAnalyser(){

                const volumes = new Uint8Array(this.volume_analyser.frequencyBinCount);
                this.volume_analyser.getByteFrequencyData(volumes);

                let volume_sum = 0;
                for(const volume of volumes){

                    volume_sum += volume;
                }
                
                // Value range: 127 = analyser.maxDecibels - analyser.minDecibels;
                const average_volume = volume_sum / volumes.length;
                const true_volume = average_volume / 127;
                this.animeVolumeAnalyser(true_volume);
            },
            animeVolumeAnalyser(new_value){

                if(new_value >= 0 && new_value <= 1){

                    //ok

                }else{

                    return false;
                }

                new_value = new_value.toFixed(2).toString();

                const targets = [
                    this.$refs.volume_analyser_circle_0,
                    this.$refs.volume_analyser_circle_1,
                    this.$refs.volume_analyser_circle_2,
                ];

                //circles have width and height of 20-30, 30-50, 50-80 %
                let base_target_percentage = 10;
                const percentage_increment = 30;
                
                for(let x=0; x < targets.length; x++){
                    
                    anime.remove(targets[x]);

                    const extra_target_percentage = (x + 1) * percentage_increment;

                    const final_target_percentage = (new_value * extra_target_percentage) + base_target_percentage;

                    anime({
                        targets: targets[x],
                        width: final_target_percentage.toString() + '%',
                        height: final_target_percentage.toString() + '%',
                        autoplay: true,
                        easing: 'linear',
                        loop: false,
                        duration: this.time_interval,
                    });
                }
            },
            async initiateVolumeAnalyser(){

                if(this.stream === undefined){

                    return false;
                }

                try{

                    const audio_context = new AudioContext();
                    const audio_source = audio_context.createMediaStreamSource(this.stream);
                    this.volume_analyser = audio_context.createAnalyser();

                    this.volume_analyser.fftSize = 512;
                    this.volume_analyser.minDecibels = -127;
                    this.volume_analyser.maxDecibels = 0;
                    this.volume_analyser.smoothingTimeConstant = 0.4;

                    audio_source.connect(this.volume_analyser);

                }catch(error){

                    console.log(error.name);
                    console.log(error.message);
                    return false;
                }

                return true;
            },
            startVolumeAnalyser(){

                this.volume_analyser_interval = setInterval(this.handleVolumeAnalyser, this.time_interval);
            },
            stopVolumeAnalyser(){

                if(this.volume_analyser_interval !== null){

                    clearInterval(this.volume_analyser_interval);
                    this.volume_analyser_interval = null;
                    this.animeVolumeAnalyser(0);
                }
            },
            async handleRecordingInput(){

                //you can pass 'blob' here, but currently removed as it is not needed

                //handle time elapsed
                this.current_duration += this.time_interval;
                this.current_duration_pretty = new Date(this.current_duration).toISOString().substring(14, 19);

                //give user instant visual feedback on recording input
            },
            async initiateStream(){

                //if not undefined, i.e. has clicked 'record' before, destroy the instance
                //probably not necessary, but doing this for slight precaution on memory management
                if(this.recorder !== undefined){

                    this.recorder.destroy();
                    this.recorder = undefined;  //need to do this, else TypeError when record->stop->record
                }

                try{

                    //getUserMedia is a Promise
                    this.stream = await navigator.mediaDevices.getUserMedia({video: false, audio: true});
                    
                }catch(error){

                    switch(error.name){

                        case 'NotFoundError':
                            alert(
                                'No recording device detected.'
                                +' Please select your recording device as input at your system settings.'
                            );
                            break;

                        default:

                            console.log(error.name);
                            console.log(error.message);
                            break;
                    }

                    return false;
                }

                return true;
            },
            async recorderStart(){

                //clear previous recording
                this.final_blob = null;
                this.final_file = null;

                //initiate and reinitiate stream
                //ensures user has device ready on every recording instance
                if(await this.initiateStream() === false){

                    return false;
                }

                //once stream is established, initiate volume analyser
                await this.initiateVolumeAnalyser()
                .then(() => this.startVolumeAnalyser());

                
                //https://github.com/muaz-khan/RecordRTC
                //note that RecordRTC uses Promise in some parts
                this.recorder = recordRTC(this.stream, {
            
                    // audio, video, canvas, gif
                    type: 'audio',
                
                    // audio/webm
                    // audio/webm;codecs=pcm
                    // video/mp4
                    // video/webm;codecs=vp9
                    // video/webm;codecs=vp8
                    // video/webm;codecs=h264
                    // video/x-matroska;codecs=avc1
                    // video/mpeg -- NOT supported by any browser, yet
                    // audio/wav
                    // audio/ogg  -- ONLY Firefox
                    // demo: simple-demos/isTypeSupported.html
                    mimeType: 'audio/webm',
                
                    // MediaStreamRecorder, StereoAudioRecorder, WebAssemblyRecorder
                    // CanvasRecorder, GifRecorder, WhammyRecorder
                    recorderType: this.MediaStreamRecorder,
                
                    // disable logs
                    disableLogs: false,
                
                    // get intervals based blobs
                    // value in milliseconds
                    timeSlice: this.time_interval,
                
                    // requires timeSlice above
                    // returns blob via callback function
                    ondataavailable: async () => { await this.handleRecordingInput()},
                
                    // auto stop recording if camera stops
                    checkForInactiveTracks: false,
                
                    // requires timeSlice above
                    // onTimeStamp: function(timestamp) {},
                
                    // both for audio and video tracks
                    bitsPerSecond: 128000,
                
                    // only for audio track
                    // ignored when codecs=pcm
                    audioBitsPerSecond: 192000,
                
                    // if you are recording multiple streams into single file
                    // this helps you see what is being recorded
                    // previewStream: function(this.stream) {},
                
                    // used by StereoAudioRecorder
                    // the range 22050 to 96000.
                    //recommended lower limit of 32000 for vocal-only
                    // sampleRate: 32000,
                
                    // used by StereoAudioRecorder
                    // the range 22050 to 96000.
                    // desiredSampRate: 32000,
                
                    // used by StereoAudioRecorder
                    // Legal values are (256, 512, 1024, 2048, 4096, 8192, 16384).
                    // bufferSize: 1024,
                
                    // used by StereoAudioRecorder
                    // 1 or 2
                    //recommended lower limit of 1 for vocal-only
                    // numberOfAudioChannels: 2,
                
                    // used by WebAssemblyRecorder
                    // frameRate: 30,
                
                    // used by WebAssemblyRecorder
                    // bitrate: 192000,
                
                    // used by MultiStreamRecorder - to access HTMLCanvasElement
                    // elementClass: 'multi-streams-mixer',
            
                });

                //set hard limit on recording duration for auto-stop
                //this will still execute after .stopRecording() (not good), but it is already taken care of
                this.recorder.setRecordingDuration(this.max_recording_duration_ms)
                    .onRecordingStopped(this.recorderStop);
                
                this.recorder.startRecording();
                this.recorder_state = this.recorder.state;
                this.is_recording = true;

                return true;
            },
            recorderPauseResume(){
                
                if(this.recorder.state == 'recording'){

                    this.recorder.pauseRecording();
                    this.stopVolumeAnalyser();

                }else if(this.recorder.state == 'paused'){

                    this.recorder.resumeRecording();
                    this.startVolumeAnalyser();
                }

                this.recorder_state = this.recorder.state;
                return true;
            },
            recorderStop(){

                //attach recorded audio to file input and playback
                try{

                    if(this.recorder.state === 'stopped'){
                        
                        //if auto-stop, state will be 'stopped'
                        this.saveRecorderAudioAsFile();
                        this.stream.stop();
                        this.stopVolumeAnalyser();

                    }else{

                        //stopRecording() bug dictates that we must run codes in it to getBlob() properly
                        this.recorder.stopRecording( () => {
                            this.saveRecorderAudioAsFile();
                            this.stream.stop();
                            this.stopVolumeAnalyser();
                        });
                    }
                    
                    //we manually store 'stopped' instead of this.recorder.state
                    //fix for bug where on pause->stop, you get 'recording'
                    this.recorder_state = 'stopped';
                    this.is_recording = false;
                    this.current_duration = 0;
                    this.current_duration_pretty = '00:00';

                    return true;

                }catch(error){

                    console.log(error);
                    return false;
                }
            },
            saveRecorderAudioAsFile(){

                //to use getBlob(), you must run it in either onRecordingStopped() or stopRecording()
                //else your first blob is unplayable (too small), and user has to click a second time

                //transform blob into file
                try{

                    this.final_blob = this.recorder.getBlob();
                    this.final_file = new File([this.final_blob], 'this_recording.webm', {
                        type: 'audio/webm'
                    });
                    this.attachRecordedAudioToInput();

                }catch(error){

                    alert(
                        'Unexpectedly unable to retrieve recorded audio.'
                        +' Our developers have been notified.'
                        +' Please refresh the page.'
                    );
                    console.log(error);
                    return false;
                }
            },
            attachRecordedAudioToInput(){

                if(this.final_file === null){

                    alert('Could not attach your file for upload because the file is empty.');
                    return false;
                }
                    
                //create new container to replace <input type="file"> container later
                let container = new DataTransfer();

                //add
                container.items.add(this.final_file);

                //replace files of <input type="file"> with DataTransfer() files
                this.$refs.audio_upload.files = container.files;

                return true;
            },
            checkFileSizeIsValid(file=this.final_file, max_size_mb=this.max_audio_file_size_mb){

                //mks with File() and files uploaded through <input type="file">

                let file_size_mb = file.size / (1000 * 1000);   //** not supported in IE browser

                if(file_size_mb > max_size_mb){

                    return false;
                }
                
                return true;
            },
            checkFileTypeIsValid(file=this.final_file, extensions_allowed=this.audio_file_extensions_allowed){

                //handles names with no extension, and names that start with '.', while also being most performant
                
                let file_name =  file.name;
                let file_extension = (file_name.slice((file_name.lastIndexOf(".") - 1 >>> 0) + 2)).toLowerCase();

                if(!extensions_allowed.includes(file_extension)){
                    
                    return false;
                }

                return true;
            },
            validateInputUpload(){
                
                if(this.$refs.audio_upload.files.length > 0){
                    
                    this.final_file = this.$refs.audio_upload.files.item(0);
                    
                    //check file size
                    if(this.checkFileSizeIsValid() === false){

                        alert('Uploaded file has exceeded limit of '+this.max_audio_file_size_mb+'MB!');
                        this.$refs.audio_upload.value = null;
                        return false;
                    }

                    //check file format
                    if(this.checkFileTypeIsValid() === false){

                        let temp_string = '';

                        for(let x = 0; x < this.audio_file_extensions_allowed.length; x++){
            
                            temp_string += this.audio_file_extensions_allowed[x].toUpperCase();
            
                            if(x < this.audio_file_extensions_allowed.length - 1){
            
                                temp_string += ', ';
                            }
                        
                        }

                        alert('Uploaded file type is not supported. Please use one of the following: '+temp_string);
                        this.$refs.audio_upload.value = null;
                        return false;
                    }

                    //ok
                    alert('Success! Uploaded file meets requirements.');

                    //attach recorded audio to playback
                    // this.attachRecordedAudioToPlayback();

                    return true;
                }
            },
            //to be called from parent as ultimate function
            retrieveFileForInputAttach(){
                
                //create new container to replace <input type="file"> container later
                let container = new DataTransfer();

                container.items.add(this.final_file);

                //validate

                //if not undefined, i.e. has clicked 'record' before, destroy the instances
                //not sure if necessary for preventing memory leak
                if(this.recorder !== undefined){

                    this.stream = undefined;
                    this.recorder.destroy();
                }

                //replace files of <input type="file"> with DataTransfer() files
                //to do so
                    //file_element.files = container.files;
                //to handle
                    //file_element.files.items(0);
                    // file_element.value = null;

                return container;
            },
        }
    }

</script>