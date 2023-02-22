<template>
    <div class="text-theme-black text-center place-items-center">
        <div class="">

            
            <!--when recording-->
            <div v-if="recorder_state !== null && recorder_state !== 'stopped'">
                <div class="grid grid-rows-2 grid-cols-4 grid-flow-col gap-x-2">

                    <!--cancel-->
                    <VActionButtonMedium
                        @click.prevent="recorderStop(true)"
                        aria-label="end recording"
                        class="col-start-1 row-span-2 col-span-1"
                        :propIsEnabled="is_anime_playback_truly_completed === true && is_recording === true"
                        :propIsDefaultTextSize="false"
                    >
                        <div class="text-2xl">
                            <i class="fas fa-xmark"></i>
                        </div>
                    </VActionButtonMedium>

                    <!--timer-->
                    <div class="row-start-1 row-span-1 col-span-2 relative">
                        <span class="absolute w-fit h-fit left-0 right-0 top-0 bottom-0 m-auto text-2xl">-{{current_duration_pretty}}</span>
                    </div>

                    <!--pause/resume-->
                    <VActionButtonSmall
                        @click.prevent="recorderPauseResume()"
                        :aria-label="pauseResumeAriaLabel"
                        class="row-start-2 row-span-1 col-span-2 h-full"
                        :propIsEnabled="is_anime_playback_truly_completed === true && is_recording === true"
                    >
                        <i
                            :class="[
                                (recorder_state === 'recording' ? 'fas fa-pause' : 'fas fa-pause'),
                                (recorder_state === 'paused' ? 'fas fa-play' : 'fas fa-pause'),
                                ''
                            ]"
                        ></i>
                    </VActionButtonSmall>

                    <!--done-->
                    <VActionButtonMedium
                        @click.prevent="recorderStop(false)"
                        aria-label="end recording"
                        class="col-start-4 row-span-2 col-span-1"
                        :propIsDefaultTextSize="false"
                        :propIsEnabled="is_anime_playback_truly_completed === true && is_recording === true"
                    >
                        <div class="text-2xl">
                            <i class="fas fa-check"></i>
                        </div>
                    </VActionButtonMedium>
                </div>
            </div>

            <!--when not recording-->
            <div v-else>
                <VActionButtonMedium
                    @click.prevent="recorderStart()"
                    aria-label="record"
                    :propIsEnabled="is_anime_playback_truly_completed === true && is_recording === false"
                    class="w-full"
                >
                    <i class="fas fa-microphone-lines"></i>
                </VActionButtonMedium>
            </div>
        </div>
        <!-- currently don't allow file submission, but store file here for final form submit -->
        <!-- for file submission: <form method="POST" enctype="multipart/form-data"></form> -->
        <!-- <input type="file" ref="audio_upload" accept=".mp3, .webm" class="hidden" required> -->
    </div>
</template>


<script setup lang="ts">
    import VActionButtonSmall from '/src/components/small/VActionButtonSmall.vue';
    import VActionButtonMedium from '/src/components/small/VActionButtonMedium.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    // import anime from 'animejs';
    const recordRTC = require('/node_modules/recordrtc/RecordRTC.min.js');

    export default defineComponent({
        data(){
            return {
                stream: null as MediaStream | null,  //for defining recorder instances
                volume_analyser: null as AnalyserNode | null,
                volume_analyser_interval: null as number | null,
                recorder: null as any | null,   //recordRTC object, but lazy to find a solution
                recorder_state: null as 'recording' | 'paused' | 'stopped' | null,
                recording_volume: 0,    //0-1, only changes when recording
                recording_interval_worker: null as Worker | null,

                is_recording: false,    //is not affected by pause/resume
                current_duration: 0,    //milliseconds
                current_duration_pretty: '00:00',
                is_anime_playback_truly_completed: false,   //from recording visualiser at VPlayback to prevent actions until ready
            };
        },
        mounted(){

            //NOTE
            //no need to be alarmed if it picks up nothing from browser audio
        },
        beforeUnmount(){

            //just in case
            this.stopRecordingIntervalWorker();
        },
        props: {
            propTimeInterval: {
                type: Number,
                required: true,
                default: 200,
            },
            propMaxDuration: {
                type: Number,
                required: true,
            },
            propIsOpen: Boolean,
            propIsAnimePlaybackCompleted: Boolean,
        },
        watch: {
            is_recording(new_value){

                //reset to false before incoming anime, as there will be anime for both is_recording=true/false
                this.is_anime_playback_truly_completed = false;

                this.$emit('isRecording', new_value);
            },
            propIsAnimePlaybackCompleted(new_value){

                //relying on prop alone isn't enough, because when is_recording is changed, it is still true
                //here, we get the final true
                this.is_anime_playback_truly_completed = new_value;
            },
            propIsOpen(new_value){

                //if recording when closed, pause
                if(new_value === false && this.recorder_state === 'recording'){

                    this.recorderPauseResume('pause');
                }
            },
        },
        computed: {
            pauseResumeAriaLabel() : string {

                if(this.is_recording === true){

                    return 'pause recording';

                }else{

                    return 'resume recording';
                }
            },
        },
        emits: ['newRecording', 'isRecording', 'newRecordingVolume'],
        methods: {
            stopRecordingIntervalWorker(){

                if(this.recording_interval_worker !== null){

                    this.recording_interval_worker.postMessage({
                        'action': 'stop'
                    });

                    this.recording_interval_worker.terminate();
                    this.recording_interval_worker = null;
                }
            },
            startRecordingIntervalWorker(){

                //set up web worker to stop recording appropriately, even when tabbed out
                //expect {'action': 'start/stop', 'interval_ms: 0, 'starting_ms': 0}
                //we have webpack 5, so we do not need worker-loader package

                if(this.recording_interval_worker === null){

                    this.recording_interval_worker = new Worker(
                        new URL('/src/workers/IntervalTimer.ts', import.meta.url)
                    );
                }

                this.recording_interval_worker.postMessage({
                    'action': 'start',
                    'interval_ms': this.propTimeInterval,
                    'starting_ms': this.current_duration
                });

                this.recording_interval_worker.onmessage = (event)=>{

                    //can do ===, but feels safer with >=
                    if(event.data >= this.propMaxDuration){

                        this.recorderStop(false);
                    }

                    this.countdownRecordingTime();
                }

            },
            async handleVolumeAnalyser() : Promise<boolean> {

                if(this.volume_analyser === null){

                    return false;
                }

                const volumes = new Uint8Array(this.volume_analyser.frequencyBinCount);
                this.volume_analyser.getByteFrequencyData(volumes);

                let volume_sum = 0;
                for(const volume of volumes){

                    volume_sum += volume;
                }
                
                // Value range: 127 = analyser.maxDecibels - analyser.minDecibels;
                const average_volume = volume_sum / volumes.length;
                let true_volume = average_volume / 127;

                //we can still exceed expected max volume of 1, e.g. 1.01
                //we cap it at 1
                if(true_volume > 1){

                    true_volume = 1;
                }

                this.recording_volume = true_volume;

                //emit to VPlayback for recording visualiser
                this.$emit('newRecordingVolume', this.recording_volume);

                return true;
            },
            async initiateVolumeAnalyser() : Promise<boolean> {

                if(this.stream === null){

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

                }catch(error:any|unknown){

                    console.log(error.name);
                    console.log(error.message);
                    return false;
                }

                return true;
            },
            startVolumeAnalyser() : void {

                //using window for number typing
                this.volume_analyser_interval = window.setInterval(this.handleVolumeAnalyser, this.propTimeInterval);
            },
            stopVolumeAnalyser() : void {

                if(this.volume_analyser_interval !== null){

                    clearInterval(this.volume_analyser_interval);
                    this.volume_analyser_interval = null;
                    this.recording_volume = 0;
                }
            },
            countdownRecordingTime() : void {

                //we need this because ondataavailable runs one more time after stopRecording()
                //UPDATE: unreliable for timing, rely on web worker instead
                //e.g. if max dura. 20s then auto-stopped at -3s, if max dura. 40s then auto-stopped at -6s
                // if(this.is_recording === false){
                    
                //     return false;
                // }

                //handle time elapsed
                this.current_duration += this.propTimeInterval;
                this.current_duration_pretty = new Date(
                    this.propMaxDuration - this.current_duration
                ).toISOString().substring(14, 19);

                //give user instant visual feedback on recording input
            },
            async initiateStream() : Promise<boolean> {

                try{

                    //getUserMedia is a Promise
                    this.stream = await navigator.mediaDevices.getUserMedia({video: false, audio: true});
                    
                }catch(error:any|unknown){

                    switch(error.name){

                        case 'NotFoundError':
                            alert(
                                'No recording device detected.'
                                +' Please select your recording device as input at your system settings.'
                            );
                            break;

                        case 'NotAllowedError':
                            alert(
                                'Please allow permissions for your recording device on your browser.'
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
            async recorderStart() : Promise<boolean> {

                if(this.is_anime_playback_truly_completed === false || this.is_recording === true){

                    return false;
                }

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
                    recorderType: recordRTC.MediaStreamRecorder,
                
                    // disable logs
                    disableLogs: false,
                
                    // get intervals based blobs
                    // value in milliseconds
                    // timeSlice: this.propTimeInterval,
                
                    // requires timeSlice above
                    // returns blob via callback function
                    // ondataavailable: this.countdownRecordingTime,
                
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
                this.recorder.setRecordingDuration(this.propMaxDuration)
                    .onRecordingStopped(this.recorderStop);
                
                this.recorder.startRecording();
                this.startRecordingIntervalWorker();
                this.recorder_state = this.recorder.state;
                this.is_recording = true;

                return true;
            },
            recorderPauseResume(force_state:'pause'|'resume'|null=null) : void {
                
                if(this.is_recording === false){

                    return;
                }

                if(this.recorder.state == 'recording' || force_state === 'pause'){

                    this.recorder.pauseRecording();
                    this.stopRecordingIntervalWorker();
                    this.stopVolumeAnalyser();
                    this.$emit('newRecordingVolume', 0);

                }else if(this.recorder.state == 'paused'){

                    this.recorder.resumeRecording();
                    this.startRecordingIntervalWorker();
                    this.startVolumeAnalyser();
                }

                this.recorder_state = this.recorder.state;
            },
            resetWhenRecorderStop() : void {

                //convenient to use in callback of recordRTC.stopRecording() at recorderStop()
                //because doing it outside of recordRTC.stopRecording() would be too early

                //we manually store 'stopped' instead of this.recorder.state
                //fix for bug where on pause->stop, you get 'recording'
                this.recorder_state = 'stopped';
                this.is_recording = false;
                this.current_duration = 0;
                this.current_duration_pretty = '00:00';
            },
            recorderStop(is_cancelled:boolean) : void {
                
                if(this.is_anime_playback_truly_completed === false || this.is_recording === false){

                    return;
                }

                //attach recorded audio to file input and playback
                try{

                    //if auto-stop, state will be 'stopped'
                    if(this.recorder.state === 'stopped'){

                        this.stopRecordingIntervalWorker();

                        if(this.stream !== null){
                            //MediaStream.stop() deprecated, use getTracks()[0] for MediaStreamTrack.stop()
                            //https://developer.chrome.com/blog/mediastream-deprecations/
                            this.stream.getTracks()[0].stop();
                        }

                        this.stopVolumeAnalyser();
                        
                        //emit
                        if(is_cancelled !== true){

                            this.emitNewRecording();
                        }

                        this.resetWhenRecorderStop();

                    }else{

                        //stopRecording() bug dictates that we must run codes in it to getBlob() properly
                        this.recorder.stopRecording( () => {

                            this.stopRecordingIntervalWorker();

                            if(this.stream !== null){
                                //MediaStream.stop() deprecated, use getTracks()[0] for MediaStreamTrack.stop()
                                //https://developer.chrome.com/blog/mediastream-deprecations/
                                this.stream.getTracks()[0].stop();
                            }

                            this.stopVolumeAnalyser();

                            //emit
                            if(is_cancelled !== true){

                                this.emitNewRecording();
                            }

                            this.resetWhenRecorderStop();
                        });
                    }

                    return;

                }catch(error:any|unknown){

                    console.log(error);
                    return;
                }
            },
            emitNewRecording() : void {

                //to use getBlob(), you must run it in either onRecordingStopped() or stopRecording()
                //else your first blob is unplayable (too small), and user has to click a second time

                //transform blob into file
                try{

                    let new_recording = new File([this.recorder.getBlob()], 'this_recording.webm', {
                        type: 'audio/webm'
                    });

                    this.$emit('newRecording', {
                        'final_file' : new_recording,
                        'file_duration' : this.current_duration
                    });

                }catch(error:any|unknown){

                    alert(
                        'Unexpectedly unable to retrieve recorded audio.'
                        +' Please refresh the page.'
                    );
                    console.log(error);
                }
            },
        }
    });
</script>