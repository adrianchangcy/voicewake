<template>
    <!-- h-[5.5rem] = h-20 + p-2 -->
    <div class="h-20 text-center place-items-center">
        <TransitionGroupFade>

            <!--when not recording-->
            <div
                v-show="!is_recording"
                class="w-full h-full"
            >
                <VAction
                    @click.prevent="recorderStart()"
                    :propIsEnabled="canStartRecording"
                    propElement="button"
                    type="button"
                    propElementSize="m"
                    :propIsIconOnly="true"
                    class="w-full"
                >
                    <FontAwesomeIcon icon="fas fa-microphone-lines" class="text-4xl mx-auto"/>
                    <span class="sr-only">start recording</span>
                </VAction>
            </div>

            <!--when recording-->
            <div
                v-show="is_recording"
                class="w-full h-full"
            >
                <div class="grid grid-rows-2 grid-cols-4 grid-flow-col gap-x-2">

                    <!--cancel-->
                    <VAction
                        @click.prevent="recorderStopByUserOrWebWorker(true)"
                        propElement="button"
                        type="button"
                        propElementSize="m"
                        :propIsIconOnly="true"
                        class="col-start-1 row-span-2 col-span-1"
                    >
                        <FontAwesomeIcon icon="fas fa-xmark" class="text-2xl mx-auto"/>
                        <span class="sr-only">cancel recording</span>
                    </VAction>

                    <!--timer-->
                    <div class="row-start-1 row-span-1 col-span-2 relative">
                        <span
                            class="absolute w-fit h-fit left-0 right-0 top-0 bottom-0 m-auto text-xl"
                        >
                            -{{current_duration_pretty}}
                        </span>
                    </div>

                    <!--pause/resume-->
                    <VAction
                        @click.prevent="recorderPauseResume()"
                        propElement="button"
                        type="button"
                        propElementSize="s"
                        :propIsIconOnly="true"
                        class="row-start-2 row-span-1 col-span-2 h-full"
                    >
                        <FontAwesomeIcon v-show="recorder_state === 'recording'" icon="fas fa-pause" class="text-2xl mx-auto"/>
                        <FontAwesomeIcon v-show="recorder_state === 'paused'" icon="fas fa-play" class="text-2xl mx-auto"/>
                        <span class="sr-only">{{ getPlayPauseScreenReader }}</span>
                    </VAction>

                    <!--done-->
                    <VAction
                        @click.prevent="recorderStopByUserOrWebWorker(false)"
                        :propIsEnabled="canStopRecording"
                        propElement="button"
                        type="button"
                        propElementSize="m"
                        :propIsIconOnly="true"
                        class="col-start-4 row-span-2 col-span-1"
                    >
                        <FontAwesomeIcon icon="fas fa-check" class="text-2xl mx-auto"/>
                        <span class="sr-only">stop recording</span>
                    </VAction>
                </div>
            </div>
        </TransitionGroupFade>
    </div>
        <!-- currently don't allow file submission, but store file here for final form submit -->
        <!-- for file submission: <form method="POST" enctype="multipart/form-data"></form> -->
        <!-- <input type="file" ref="audio_upload" accept=".mp3, .webm" class="hidden" required> -->
</template>


<script setup lang="ts">
    import VAction from '@/components/small/VAction.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faMicrophoneLines } from '@fortawesome/free-solid-svg-icons/faMicrophoneLines';
    import { faXmark } from '@fortawesome/free-solid-svg-icons/faXmark';
    import { faPlay } from '@fortawesome/free-solid-svg-icons/faPlay';
    import { faPause } from '@fortawesome/free-solid-svg-icons/faPause';
    import { faCheck } from '@fortawesome/free-solid-svg-icons/faCheck';

    library.add(faMicrophoneLines, faXmark, faPlay, faPause, faCheck);
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import { useVPlaybackStore } from '@/stores/VPlaybackStore';
    //fixes native recorded webm's missing/buggy duration
    import fixWebmDuration from 'fix-webm-duration';
    //fixes web worker import not working when fetched from another origin
    import '@/patches/cors_worker_patch';
    import RecordRTC from 'recordrtc';

    type recorderStates = "inactive" | "recording" | "stopped" | "paused" | "destroyed";

    export default defineComponent({
        data(){
            return {
                vplayback_store: useVPlaybackStore(),

                stream: null as MediaStream | null,  //for defining recorder instances
                volume_analyser: null as AnalyserNode | null,
                volume_analyser_interval: null as number | null,
                recorder: null as RecordRTC | null,   //recordRTC object, but lazy to find a solution
                recorder_state: 'inactive' as recorderStates,
                recording_interval_worker: null as Worker | null,

                is_recording: false,    //is not affected by pause/resume
                current_duration: 0,    //milliseconds
                current_duration_pretty: '00:00',
            };
        },
        props: {
            propIntervalMs: {
                type: Number,
                required: true,
                default: 100,
            },
            propMaxDurationMs: {
                type: Number,
                required: true,
            },
            propIsOpen: Boolean,
            propCanRecord: Boolean,
        },
        watch: {
            is_recording(new_value){

                this.$emit('isRecording', new_value);

                this.vplayback_store.triggerPause();
            },
            propIsOpen(new_value){

                //if recording when closed, pause
                if(new_value === false && this.recorder_state === 'recording'){

                    this.recorderPauseResume('pause');
                }
            },
        },
        computed: {
            getPlayPauseScreenReader() : string {

                if(this.is_recording === true){

                    return 'pause recording';

                }else{

                    return 'resume recording';
                }
            },
            canStartRecording() : boolean {

                if(this.propCanRecord === true && this.is_recording === false){

                    return true;

                }else{

                    return false;
                }
            },
            canStopRecording() : boolean {

                //minimum 1 second
                return this.current_duration > 1000;
            },
        },
        emits: ['newRecording', 'isRecording', 'isCancelled', 'newVolumeAnalyserPulse'],
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
            createRecordingIntervalWorker(){

                this.recording_interval_worker = new Worker(
                    new URL('@/workers/IntervalTimer.ts', import.meta.url),
                );
            },
            startRecordingIntervalWorker(){

                //set up web worker to stop recording appropriately, even when tabbed out
                //expect {'action': 'start/stop', 'interval_ms: 0, 'starting_ms': 0}
                //we have webpack 5, so we do not need worker-loader package

                if(this.recording_interval_worker === null){

                    this.createRecordingIntervalWorker();
                }

                //start web worker
                this.recording_interval_worker!.postMessage({
                    'action': 'start',
                    'interval_ms': this.propIntervalMs,
                    'starting_ms': this.current_duration
                });

                this.recording_interval_worker!.onmessage = (event:MessageEvent)=>{

                    //can do ===, but feels safer with >=
                    if(event.data >= this.propMaxDurationMs){

                        this.recorderStopByUserOrWebWorker(false);
                    }

                    //we do this here instead of RecordRTC's ondataavailable
                    //blob duration is more reliable here, in the context of tabbed out while recording
                    this.countdownRecordingTime();
                }

                this.recording_interval_worker!.onerror = ()=>{

                    alert('Uh oh, the recorder had an unexpected issue.');
                };

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

                //emit to VPlayback for recording visualiser
                this.$emit('newVolumeAnalyserPulse', true_volume);

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
                this.volume_analyser_interval = window.setInterval(this.handleVolumeAnalyser, this.propIntervalMs);
            },
            stopVolumeAnalyser() : void {

                if(this.volume_analyser_interval !== null){

                    clearInterval(this.volume_analyser_interval);
                    this.volume_analyser_interval = null;
                }
            },
            countdownRecordingTime() : void {

                //we need this because ondataavailable runs one more time after stopRecording()
                //UPDATE: unreliable for timing, rely on web worker instead
                //e.g. if max dura. 20s then auto-stopped at -3s, if max dura. 40s then auto-stopped at -6s

                //handle time elapsed
                this.current_duration += this.propIntervalMs;
                this.current_duration_pretty = new Date(
                    this.propMaxDurationMs - this.current_duration
                ).toISOString().substring(14, 19);

                //give user instant visual feedback on recording input
            },
            async initiateStream() : Promise<boolean> {

                try{

                    //getUserMedia is a Promise
                    //navigator.mediaDevices is unefined in insecure context, i.e. not HTTPS
                    await navigator.mediaDevices.getUserMedia({
                        video: false,
                        audio: true,
                    }).then((stream:MediaStream)=>{

                        this.stream = stream;
                        this.stream.addTrack(stream.getTracks()[0]);
                    });

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
                                'To record, please allow browser permissions for your recording device.'
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

                if(this.canStartRecording === false){

                    return false;
                }

                //initiate and reinitiate stream
                //ensures user has device ready on every recording instance
                if(await this.initiateStream() === false || this.stream === null){

                    return false;
                }

                //once stream is established, initiate volume analyser
                await this.initiateVolumeAnalyser()
                .then(() => this.startVolumeAnalyser());

                
                //https://github.com/muaz-khan/RecordRTC
                //note that RecordRTC uses Promise in some parts
                this.recorder = new RecordRTC(this.stream, {
            
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
                    //FYI
                        //audio/webm;codecs=pcm has huge file size
                    mimeType: "audio/webm",
                
                    // MediaStreamRecorder, StereoAudioRecorder, WebAssemblyRecorder
                    // CanvasRecorder, GifRecorder, WhammyRecorder
                    recorderType: RecordRTC.MediaStreamRecorder,
                
                    // disable logs
                    disableLogs: import.meta.env.NODE_ENV === 'production',
                
                    // get intervals based blobs
                    // value in milliseconds
                    // timeSlice: this.propIntervalMs,
                
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
                this.recorder.setRecordingDuration(this.propMaxDurationMs)
                    .onRecordingStopped(this.recorderStopAsCallback);
                this.recorder.startRecording();
                this.startRecordingIntervalWorker();
                this.recorder_state = this.recorder.getState() as recorderStates;
                this.is_recording = true;

                return true;
            },
            recorderPauseResume(force_state:'pause'|'resume'|null=null) : void {

                if(this.is_recording === false || this.recorder === null){

                    return;
                }

                if(this.recorder.getState() == 'recording' || force_state === 'pause'){

                    this.recorder.pauseRecording();
                    this.stopRecordingIntervalWorker();
                    this.stopVolumeAnalyser();
                    this.$emit('newVolumeAnalyserPulse', 0);

                }else if(this.recorder.getState() == 'paused'){

                    this.recorder.resumeRecording();
                    this.startRecordingIntervalWorker();
                    this.startVolumeAnalyser();
                }

                this.recorder_state = this.recorder.getState() as recorderStates;
            },
            resetWhenRecorderStop() : void {

                //convenient to use in callback of recordRTC.stopRecording() at recorderStop()
                //because doing it outside of recordRTC.stopRecording() would be too early

                //we manually store 'stopped' instead of this.recorder.getState()
                //fix for bug where on pause->stop, you get 'recording'
                this.recorder_state = 'stopped';
                this.is_recording = false;
                this.current_duration = 0;
                this.current_duration_pretty = '00:00';
                this.$emit('newVolumeAnalyserPulse', 0);
            },
            recorderStopAsCallback(callback_blob_url:string='') : void {

                if(callback_blob_url === ''){

                    return;
                }

                //RecordRTC's .onRecordingStopped() passes URL blob string as first arg to your callback
                //i.e. auto-stopped
                //https://github.com/muaz-khan/RecordRTC/issues/167
                //clear it, because it cannot be used for Blob object processing
                URL.revokeObjectURL(callback_blob_url);

                this.stopRecordingIntervalWorker();

                if(this.stream !== null){
                    //MediaStream.stop() deprecated, use getTracks()[0] for MediaStreamTrack.stop()
                    //https://developer.chrome.com/blog/mediastream-deprecations/
                    this.stream.getTracks()[0].stop();
                }

                this.stopVolumeAnalyser();

                //if stopped as callback, this.recorder.getState() === 'stopped' is true
                if(this.recorder !== null && this.recorder.getState() === 'stopped'){

                    this.emitNewRecording();

                }else{

                    //not sure if it'll reach here, but just in case
                    this.$emit('isCancelled', true);
                }

                this.resetWhenRecorderStop();
            },
            recorderStopByUserOrWebWorker(is_cancelled:boolean) : void {

                //bug fix lore
                    //recorderStopByUserOrWebWorker() and recorderStopAsCallback() used to be combined
                    //.onRecordingStopped() passes URL blob string to is_cancelled param above
                    //since the web worker and .onRecordingStopped() is at a no-risk race condition,
                    //URL blob string was able to reach the stage where .arrayBuffer is applied, causing the error

                if(this.is_recording === false || this.recorder === null){

                    return;
                }

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
                    if(is_cancelled === false){

                        this.emitNewRecording();

                    }else{

                        this.$emit('isCancelled', true);
                    }

                    this.resetWhenRecorderStop();
                });
            },
            emitNewRecording() : void {

                //to use getBlob(), you must run it within the context of a callback
                //the callback will be passed into either onRecordingStopped() or stopRecording()
                //else your first blob is unplayable (too small), and user has to click a second time

                if(this.recorder === null){

                    return;
                }

                try{

                    // let new_recording = new File([this.recorder.getBlob()], 'this_recording.webm', {
                    //     type: 'audio/webm'
                    // });

                    //ensures these data are available before async runs
                    const new_blob = this.recorder.getBlob();
                    const new_duration = this.current_duration;

                    //always async, as per docs
                    //will log "duration section is missing" if so
                    fixWebmDuration(new_blob, new_duration, (fixed_blob) => {
                        this.$emit('newRecording', {
                            'blob' : fixed_blob,
                            'blob_duration' : new_duration,
                        });
                    }, {
                        logger: false
                    });

                }catch(error:any|unknown){

                    alert('Unexpectedly unable to retrieve recorded audio.');
                    console.log(error);
                }
            },
        },
        mounted(){

            //create earlier, in case there is a wait time
            //we want the waiting to occur here, and not when user wants to record
            this.createRecordingIntervalWorker();
        },
        beforeUnmount(){

            this.recorderStopByUserOrWebWorker(true);
        },
    });
</script>