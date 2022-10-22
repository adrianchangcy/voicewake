<template>
    <audio id="audio_playback" controls></audio>
    <button type="button" id="start_recording_btn" class="bg-red-400">RECORD</button>
    <div class="grid grid-cols-2 grid-flow-col">
        <button id="pause_resume_recording_btn" class="col-span-1 bg-red-400">PAUSE OR RESUME</button>
        <button id="stop_recording_btn" class="col-span-1 bg-red-400">DONE</button>
    </div>
    <!-- for file submission: <form method="POST" enctype="multipart/form-data"> -->
</template>


<script>
    export default {
        data(){
            return {
                stream: undefined,  //for defining recorder instances
                recorder: undefined,
                final_blob: null,
                final_file: null,
            };
        },
        props: {
            propMaxAudioFileSizeMb: Number,
            propAudioFileExtensionsAllowed: Array,
            propMaxRecordingDurationMs: Number,
        },
        mounted(){

            //script, npm install when ready
            let recorderRTCScript = document.createElement('script');
            recorderRTCScript.setAttribute('src', 'https://cdnjs.cloudflare.com/ajax/libs/RecordRTC/5.6.2/RecordRTC.js');
            document.head.appendChild(recorderRTCScript);

            //default prop values
            //webm, despite being able to contain video media, is seamlessly handled by <audio>
            this.propMaxAudioFileSizeMb = 200;
            this.propAudioFileExtensionsAllowed = ['mp3','webm'];
            this.propMaxRecordingDurationMs = 1000 * 60 * 2;    //2 minutes

            //get stream ready to create recorder instances from it
            this.initiate_stream();
        },
        methods: {

            initiate_stream(){

                try{

                    this.stream = navigator.mediaDevices.getUserMedia({video: false, audio: true});

                }catch(error){

                    switch(error.name){

                        case 'NotFoundError':
                            console.log('No input device detected.');
                            break;

                        default:
                            console.log(error.name);
                            console.log(error.message);
                            break;
                    };

                    return false;
                };

                return true;
            },
            recorder_start(){

                //if not undefined, i.e. has clicked 'record' before, destroy the instance
                //probably not necessary, but doing this for slight precaution on memory management
                if(this.recorder !== undefined){

                    this.recorder.destroy();
                }

                //reinitiate stream
                //ensures user has device ready on every recording instance
                if(this.initiate_stream() === false){

                    return false;
                }

                //https://github.com/muaz-khan/RecordRTC
                //note that RecordRTC uses Promise in some parts
                recorder = RecordRTC(stream, {
            
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
                    recorderType: MediaStreamRecorder,
                
                    // disable logs
                    disableLogs: false,
                
                    // get intervals based blobs
                    // value in milliseconds
                    //timeSlice: 1000,
                
                    // requires timeSlice above
                    // returns blob via callback function
                    //ondataavailable: function(blob) {},
                
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
                    // previewStream: function(stream) {},
                
                    // used by StereoAudioRecorder
                    // the range 22050 to 96000.
                    //recommended lower limit of 32000 for vocal-only
                    sampleRate: 32000,
                
                    // used by StereoAudioRecorder
                    // the range 22050 to 96000.
                    desiredSampRate: 32000,
                
                    // used by StereoAudioRecorder
                    // Legal values are (256, 512, 1024, 2048, 4096, 8192, 16384).
                    bufferSize: 1024,
                
                    // used by StereoAudioRecorder
                    // 1 or 2
                    //recommended lower limit of 1 for vocal-only
                    numberOfAudioChannels: 2,
                
                    // used by WebAssemblyRecorder
                    frameRate: 30,
                
                    // used by WebAssemblyRecorder
                    bitrate: 192000,
                
                    // used by MultiStreamRecorder - to access HTMLCanvasElement
                    elementClass: 'multi-streams-mixer',
                });

                //set hard limit on recording duration for auto-stop
                //this will still execute after .stopRecording() (not good), but it is already taken care of
                this.recorder.setRecordingDuration(propMaxRecordingDurationMs)
                    .onRecordingStopped(recorder_stop);

                this.recorder.startRecording();

                return true;
            },
            recorder_pause_resume(){

                if(this.recorder.state == 'recording'){

                    this.recorder.pauseRecording();

                }else if(this.recorder.state == 'paused'){

                    this.recorder.resumeRecording();
                }

                return true;
            },
            recorder_stop(){

                //get file
                this.final_file = save_and_get_recorder_audio_as_file();

                //attach recorded audio to file input and playback
                    attach_recorded_audio_to_file_input(file);
                    this.attach_file_to_playback();

                try{

                    if(this.recorder.state === 'stopped'){
                        
                        //if auto-stop, state will be 'stopped'
                        this.handle_recorder_stop();

                    }else{

                        //stopRecording() bug dictates that we must run codes in it to getBlob() properly
                        this.recorder.stopRecording( () => { handle_recorder_stop(); });
                    }

                    return true;

                }catch(error){

                    console.log(error);
                    return false;
                }        
            },
            save_and_get_recorder_audio_as_file(){

                //transform blob into file
                try{

                    this.final_blob = this.recorder.getBlob();
                    this.final_file = new File([this.final_blob], 'this_recording.webm', {
                                    type: 'audio/webm'
                                });

                    return this.final_file;

                }catch(error){

                    alert('Could not retrieve recorded audio.');
                    console.log(error);
                    return false;
                }
            },
            attach_recorded_audio_to_file_input(file){
                    
                //create new container to replace <input type="file"> container later
                let container = new DataTransfer();

                //add
                container.items.add(file);

                //replace files of <input type="file"> with DataTransfer() files
                audio_file_upload.files = container.files;

                return true;
            },
            attach_file_to_playback(){

                //attach file into <audio>
                audio_playback.src = URL.createObjectURL(file);

                audio_playback.onload = function(){
                    //free the memory
                    return URL.revokeObjectURL(audio_playback.src);
                };

                return true;
            },
            check_file_size_is_valid(file=this.final_file, max_size_mb=this.propMaxAudioFileSizeMb){
                
                //works with File() and files uploaded through <input type="file">

                let file_size_mb = file.size / (1000 * 1000);   //** not supported in IE browser

                if(file_size_mb > max_size_mb){

                    return false;
                }
                
                return true;
            },
            check_file_type_is_valid(file=this.final_file, extensions_allowed=this.propAudioFileExtensionsAllowed){

                //handles names with no extension, and names that start with '.', while also being most performant
                
                let file_name =  file.name;
                let file_extension = (file_name.slice((file_name.lastIndexOf(".") - 1 >>> 0) + 2)).toLowerCase();

                if(!extensions_allowed.includes(file_extension)){
                    
                    return false;
                }

                return true;
            },
            do_final_validation(file=this.final_file){

                //check file size
                if(check_file_size_is_valid() === false){

                    alert('Uploaded file has exceeded limit of '+MAX_AUDIO_FILE_SIZE_MB+'MB!');
                    return false;
                }

                //check file format
                if(check_file_type_is_valid() === false){

                    let temp_string = '';

                    for(let x = 0; x < propAudioFileExtensionsAllowed.length; x++){
            
                        temp_string += propAudioFileExtensionsAllowed[x].toUpperCase();
            
                        if(x < propAudioFileExtensionsAllowed.length - 1){
            
                            temp_string += ', ';
                        }
                    }

                    alert('Uploaded file type is not supported. Please use one of the following: '+temp_string);
                    audio_file_upload.value = null;
                    return false;
                }

                //ok
                alert('Success! Uploaded file meets requirements.');
            },
            //to be called from parent as ultimate function
            retrieve_file_for_input_file_attach(){
                
                //create new container to replace <input type="file"> container later
                let container = new DataTransfer();

                container.items.add(this.final_file);

                //validate
                if(this.do_final_validation() === false){

                    return false;
                }

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

<script>