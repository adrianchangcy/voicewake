<template>
    <div class="w-2/4 h-fit p-4 mx-auto border-2 border-theme-black flex flex-col gap-y-2">
        <audio ref="audio_playback" controls></audio>
        <VActionButton @click.self="recorderStart()">RECORD</VActionButton>
        <div class="grid grid-cols-2 grid-flow-col">
            <VActionButton @click.prevent="recorderPauseResume()" class="col-span-1">PAUSE OR RESUME</VActionButton>
            <VActionButton @click.prevent="recorderStop()" class="col-span-1">DONE</VActionButton>
        </div>
        <!-- for file submission: <form method="POST" enctype="multipart/form-data"></form> -->
        <input type="file" ref="audio_upload" accept=".mp3, .webm" required>
    </div>
</template>


<script setup>

    import VActionButton from './VActionButton.vue';
</script>

<script>

    const RecordRTC = require('/node_modules/recordrtc/RecordRTC.min.js');

    export default {
        data(){
            return {
                stream: undefined,  //for defining recorder instances
                recorder: undefined,
                final_blob: null,
                final_file: null,

                //default values
                //webm, despite being able to contain video media, is seamlessly handled by <audio>
                max_audio_file_size_mb: 200,
                audio_file_extensions_allowed: ['mp3','webm'],
                // max_recording_duration_ms: 1000 * 60 * 2,    //2 minutes
                max_recording_duration_ms: 5000,    //2 minutes
            };
        },
        mounted(){

        },
        methods: {
            async initiateStream(){

                //if not undefined, i.e. has clicked 'record' before, destroy the instance
                //probably not necessary, but doing this for slight precaution on memory management
                if(this.recorder !== undefined){

                    this.recorder.destroy();
                }

                try{

                    //getUserMedia is a Promise
                    this.stream = await navigator.mediaDevices.getUserMedia({video: false, audio: true});

                }catch(error){

                    switch(error.name){

                        case 'NotFoundError':
                            console.log('No input device detected.');
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

                //reinitiate stream
                //ensures user has device ready on every recording instance
                if(await this.initiateStream() === false){

                    return false;
                }

                //https://github.com/muaz-khan/RecordRTC
                //note that RecordRTC uses Promise in some parts
                this.recorder = RecordRTC(this.stream, {
            
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
                    // timeSlice: 1000,
                
                    // requires timeSlice above
                    // returns blob via callback function
                    // ondataavailable: function(blob) {},
                
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
                this.recorder.setRecordingDuration(this.max_recording_duration_ms)
                    .onRecordingStopped(this.recorderStop);
                
                this.recorder.startRecording();
                return true;
            },
            recorderPauseResume(){
                if(this.recorder.state == 'recording'){

                    this.recorder.pauseRecording();

                }else if(this.recorder.state == 'paused'){

                    this.recorder.resumeRecording();
                }

                return true;
            },
            recorderStop(){

                //attach recorded audio to file input and playback
                try{

                    if(this.recorder.state === 'stopped'){
                        
                        //if auto-stop, state will be 'stopped'
                        this.saveRecorderAudioAsFile();
                        this.attachRecordedAudioToInput();
                        this.attachRecordedAudioToPlayback();

                    }else{

                        //stopRecording() bug dictates that we must run codes in it to getBlob() properly
                        this.recorder.stopRecording( () => {
                            this.saveRecorderAudioAsFile();
                            this.attachRecordedAudioToInput();
                            this.attachRecordedAudioToPlayback();
                        });
                    }

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
                    return true;

                }catch(error){

                    alert('Could not retrieve recorded audio.');
                    console.log(error);
                    return false;
                }
            },
            attachRecordedAudioToInput(){
                    
                //create new container to replace <input type="file"> container later
                let container = new DataTransfer();

                //add
                container.items.add(this.final_file);

                //replace files of <input type="file"> with DataTransfer() files
                this.$refs.audio_upload.files = container.files;

                return true;
            },
            attachRecordedAudioToPlayback(){

                //attach file into <audio>
                this.$refs.audio_playback.src = URL.createObjectURL(this.final_file);

                this.$refs.audio_playback.onload = function(){
                    //free the memory
                    return URL.revokeObjectURL(this.$refs.audio_playback.src);
                };

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
                    this.attachRecordedAudioToPlayback();

                    return true;
                }
            },
            //to be called from parent as ultimate function
            retrieveFileForInputAttach(){
                
                //create new container to replace <input type="file"> container later
                let container = new DataTransfer();

                container.items.add(this.final_file);

                //validate
                if(this.doFinalValidation() === false){

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

</script>