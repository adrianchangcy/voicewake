<template>
    <audio
        ref="audio_playback"
        @loadedmetadata="getPlaybackDuration()"
        @timeupdate="updateCurrentPlaybackTime()"
        @ended="pausePlayback()"
        @canplay="current_playback_state = playback_states[3]"
        @waiting="current_playback_state = playback_states[4]"
    ></audio>
    <div
        class="text-center h-[12.5rem] relative"
    >
        <div ref="playback_extras" class="absolute w-full h-fit bottom-0 px-2">
            <!--playback slider-->
            <div
                ref="playback_slider"
                class="w-full h-10 relative top-0 bottom-0 my-auto touch-none"
                @mousedown.stop="[startPlaybackDrag(), doPlaybackDrag($event), troubleshootEventListener('playback_slider mousedown')]"
                @touchstart.stop="[startPlaybackDrag(true), doPlaybackDrag($event), troubleshootEventListener('playback_slider touchstart')]"
            >
            </div>
        </div>
        <!--recording visualiser-->
        <div
            ref="recording_visualiser"
            class="absolute w-[10rem] h-[10rem] left-0 right-0 top-0 m-auto opacity-0 hidden"
        >
            <div class="relative w-full h-full">
                <div
                    ref="recording_visualiser_circle_0"
                    class="absolute w-full h-full scale-0 left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-dominant/60"
                ></div>
                <div
                    ref="recording_visualiser_circle_1"
                    class="absolute w-full h-full scale-0 left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-dominant/40"
                ></div>
                <div
                    ref="recording_visualiser_circle_2"
                    class="absolute w-full h-full scale-0 left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-dominant/20"
                ></div>
            </div>
        </div>
        <!--main-->
        <div ref="playback_main" class="absolute w-full h-[10rem]">
            <div class="w-full h-full relative">
                <!--volume ripples-->
                <div class="w-full h-full absolute px-2">
                    <div
                        ref="slider_dimension_reference"
                        class="w-full h-full relative"
                    >
                        <div ref="playback_slider_needle" class="absolute h-full left-0 opacity-0 hidden">
                            <!--can't implement rounded edges for needle, as it would bleed-->
                            <!--joined needle + knob is not as nice as this-->
                            <div
                                class="w-1 h-full bg-theme-dominant -right-0.5 absolute"
                            ></div>
                            <div
                                class="w-4 h-4 rounded-full bg-theme-dominant -bottom-7 -left-2 my-auto absolute touch-none"
                                @mousedown="[startPlaybackDrag(), doPlaybackDrag($event), troubleshootEventListener('knob mousedown')]"
                                @touchstart="[startPlaybackDrag(true), doPlaybackDrag($event), troubleshootEventListener('knob touchstart')]"
                            ></div>
                        </div>
                        <!--start this with 12.5rem on first render, and 10rem after-->
                        <div
                            ref="volume_ripples_container"
                            class="absolute w-full h-[12.5rem] grid grid-cols-max grid-flow-col gap-1 place-items-center"
                        >
                            <div
                                v-for="volume_ripple in bucket_quantity" :key="volume_ripple"
                                :class="[
                                    (current_playback_state === null ? 'hidden' : ''),
                                    (current_playback_state === playback_states[0] ? 'bg-theme-idle' : ''),
                                    (current_playback_state === playback_states[1] ? 'bg-theme-idle' : ''),
                                    (current_playback_state === playback_states[2] ? 'bg-theme-black' : ''),
                                    (current_playback_state === playback_states[3] ? 'bg-theme-black' : ''),
                                    (current_playback_state === playback_states[4] ? 'bg-theme-black' : ''),
                                    'col-span-1 w-0.5 h-full scale-y-0 top-0 bottom-0 my-auto'
                                ]"
                                ref="volume_ripple"
                            >
                            </div>
                        </div>
                    </div>
                </div>
                <!--options-->
                <div
                    ref="playback_options"
                    class="absolute w-full h-full text-theme-blue-2"
                    tabindex="0"
                    v-show="final_file !== null"
                    @keyup.enter.self.stop="[togglePlaybackOptions(), troubleshootEventListener('playback_options keyup')]"
                    @mouseenter.self.stop="[togglePlaybackOptions(true), troubleshootEventListener('playback_options mouseenter')]"
                    @mouseleave.self.stop="[togglePlaybackOptions(false), troubleshootEventListener('playback_options mouseleave')]"
                    @touchend="[togglePlaybackOptions(true), delayClosePlaybackOptions($event), troubleshootEventListener('playback_options touchend')]"
                >
                    <TransitionFade>
                        <div
                            v-show="
                                is_volume_ripples_available && !is_dragging_playback_slider &&
                                (is_playback_options_open || is_dragging_volume || !is_playing)
                            "
                            class="w-full h-full grid grid-rows-4 grid-cols-4 items-center p-2 gap-1 text-xl rounded-lg backdrop-blur"
                        >
                            <!--backward-->
                            <div class="row-start-2 row-span-2 col-start-1 col-span-1 h-full">
                                <button
                                    @click="skipPlayback(-5, $event)"
                                    @touchend="skipPlayback(-5, $event)"
                                    class="w-full h-full"
                                >
                                    <div class="w-full h-full relative">
                                        <i
                                            ref="playback_go_back_icon"
                                            class="absolute left-0 right-0 top-0 bottom-0 m-auto w-fit h-fit fas fa-rotate-left text-4xl"
                                        ></i>
                                        <span class="absolute left-0 right-0 top-0 bottom-0 m-auto w-fit h-fit text-base font-bold">5</span>
                                    </div>
                                </button>
                            </div>
                            <!--open/close playback volume-->
                            <div
                                ref="playback_volume_opener"
                                class="row-start-4 row-span-1 col-start-2 col-span-1 h-full"
                            >
                                <button
                                    @click.prevent="[togglePlaybackVolumeOptions(), troubleshootEventListener('playback_volume click')]"
                                    @touchend="[togglePlaybackVolumeOptions($event), troubleshootEventListener('playback_volume touchend')]"
                                    class="w-full h-full"
                                >
                                    <i
                                        :class="[
                                            (playback_volume === 0 ? 'fa-volume-xmark' : ''),
                                            (playback_volume <= 0.25 ? 'fa-volume-off' : ''),
                                            (playback_volume <= 0.5 ? 'fa-volume-low' : ''),
                                            (playback_volume <= 1 ? 'fa-volume-high' : ''),
                                            (is_playback_volume_open ? '-rotate-90' : 'rotate-0'),
                                            'fas transition duration-200 ease-in-out'
                                        ]"
                                    ></i>
                                </button>
                            </div>
                            <!--play pause-->
                            <div class="row-start-2 row-span-2 col-start-2 col-span-2 h-full">
                                <button
                                    @click="togglePlaybackPlayPause($event)"
                                    @touchend="togglePlaybackPlayPause($event)"
                                    class="w-full h-full"
                                >
                                    <i
                                        :class="[
                                            is_playing? 'fa-pause' : 'fa-play',
                                            'fas text-6xl'
                                        ]"
                                    ></i>
                                </button>
                            </div>
                            <!--open/close playback speed-->
                            <div
                                ref="playback_speed_options_opener"
                                class="row-start-4 row-span-1 col-start-3 col-span-1 h-full"
                            >
                                <button
                                    @click.prevent="[togglePlaybackSpeedOptions(), troubleshootEventListener('playback_speed click')]"
                                    @touchend="[togglePlaybackSpeedOptions($event), troubleshootEventListener('playback_speed touchend')]"
                                    class="w-full h-full"
                                >
                                    <i
                                        :class="[
                                            is_playback_speed_options_open ? '-rotate-90' : 'rotate-0',
                                            'fas fa-forward transition duration-200 ease-in-out'
                                        ]"
                                    ></i>
                                </button>
                            </div>
                            <!--forward-->
                            <div class="row-start-2 row-span-2 col-start-4 col-span-1 h-full">
                                <button
                                    @click="skipPlayback(5, $event)"
                                    @touchend="skipPlayback(5, $event)"
                                    class="w-full h-full"
                                >

                                    <div class="w-full h-full relative">
                                        <i
                                            ref="playback_go_forward_icon"
                                            class="absolute left-0 right-0 top-0 bottom-0 m-auto w-fit h-fit fas fa-rotate-right text-4xl"
                                        ></i>
                                        <span class="absolute left-0 right-0 top-0 bottom-0 m-auto w-fit h-fit text-base font-bold">5</span>
                                    </div>
                                </button>
                            </div>
                            <!--current duration-->
                            <div
                                class="row-start-4 row-span-1 col-start-1 col-span-1 text-base"
                            >
                                <span>{{pretty_current_playback_time}}</span>
                            </div>
                            <!--total duration-->
                            <div
                                class="row-start-4 row-span-1 col-start-4 col-span-1 text-base"
                            >
                                <span>{{pretty_playback_duration}}</span>
                            </div>
                            <!--playback volume menu-->
                            <!--also no transition to avoid flickering if kept open while playback_options closes and reopens-->
                            <VBox
                                v-show="is_playback_volume_open"
                                :propIsOpaque="false"
                                v-click-outside="{
                                    var_name_for_element_bool_status: 'is_playback_volume_open',
                                    refs_to_exclude: ['playback_volume_opener']
                                }"
                                class="row-start-1 row-span-3 col-start-2 col-span-1 h-full"
                            >
                                    <div class="relative w-full h-full">
                                            <div class="w-full h-full absolute text-center p-2 py-4">
                                                <VSliderYSmall
                                                    ref="volume_slider"
                                                    :propSliderValue="playback_volume"
                                                    @hasNewSliderValue="changePlaybackVolume($event)"
                                                    @hasNewIsDraggingValue="updateIsDraggingVolume($event)"
                                                    class="h-full"
                                                    @touchmove="[clearDelayClosePlaybackOptions(), troubleshootEventListener('touchmove')]"
                                                />
                                            </div>
                                    </div>
                            </VBox>
                            <!--playback rate menu-->
                            <!--also no transition to avoid flickering if kept open while playback_options closes and reopens-->
                            <VBox
                                v-show="is_playback_speed_options_open"
                                :propIsOpaque="false"
                                v-click-outside="{
                                    var_name_for_element_bool_status: 'is_playback_speed_options_open',
                                    refs_to_exclude: ['playback_speed_options_opener']
                                }"
                                class="row-start-1 row-span-3 col-start-3 col-span-1 h-full"
                            >
                                    <div class="relative w-full h-full">
                                        <div
                                            class="
                                                w-full h-full absolute text-center text-theme-black
                                                grid grid-rows-3 divide-y divide-theme-black/5
                                            "
                                        >
                                            <div class="row-span-1">
                                                <button
                                                    @click="changePlaybackRate(1.5, $event)"
                                                    @touchend="changePlaybackRate(1.5, $event)"
                                                    :class="[
                                                        playback_rate === 1.5 ? 'bg-theme-dominant' : 'bg-none' ,
                                                        'w-full h-full transition-colors duration-200 ease-in-out p-1 rounded-t-lg'
                                                    ]"
                                                >
                                                    1.5
                                                </button>
                                            </div>
                                            <div class="row-span-1">
                                                <button
                                                    @click="changePlaybackRate(1, $event)"
                                                    @touchend="changePlaybackRate(1, $event)"
                                                    :class="[
                                                        playback_rate === 1 ? 'bg-theme-dominant' : 'bg-none' ,
                                                        'w-full h-full transition-colors duration-200 ease-in-out p-1'
                                                    ]"
                                                >
                                                    1
                                                </button>
                                            </div>
                                            <div class="row-span-1">
                                                <button
                                                    @click="changePlaybackRate(0.5, $event)"
                                                    @touchend="changePlaybackRate(0.5, $event)"
                                                    :class="[
                                                        playback_rate === 0.5 ? 'bg-theme-dominant' : 'bg-none' ,
                                                        'w-full h-full transition-colors duration-200 ease-in-out p-1 rounded-b-lg'
                                                    ]"
                                                >
                                                    0.5
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                            </VBox>
                        </div>
                    </TransitionFade>
                </div>
            </div>
        </div>
    </div>
</template>


<script setup>

    import VSliderYSmall from './VSliderYSmall.vue';
    import VBox from './VBox.vue';
    import TransitionFade from '/src/transitions/TransitionFade.vue';
</script>

<script>

    import anime from 'animejs';

    export default{
        data(){
            return {
                final_file: null,
                final_file_duration: 0, //float seconds
                pretty_current_playback_time: '00:00',
                pretty_playback_duration: '00:00',
                is_playing: false,
                is_volume_ripples_available: false,
                anime_instance: null,   //to store animePlaybackStates() anime
                
                playback_slider_value: 0,
                is_dragging_playback_slider: false,
                is_playback_slider_touch: false,
                playback_slider_dimension: null,
                playback_slider_needle_anime: null, //we play/pause instead of new anime() to prevent second play off-position
                resume_after_stop_dragging: null,    //to know whether to resume after done navigating
                resume_after_stop_skipping: null,   //to know whether to resume after done navigating

                playback_rate: 1,   //allows 0 to 2, but we handle 0.5, 1, 1.5
                playback_volume: 0.5, //accepts 0 to 1
                is_repeat: false,

                is_playback_options_open: false,
                is_playback_speed_options_open: false,
                is_playback_volume_open: false,
                is_dragging_volume: false,
                playback_options_timeout: null,

                playback_states: ['empty', 'recording', 'attaching', 'can_play', 'loading'],
                current_playback_state: null,
                bucket_quantity: 30,
                file_volumes: [],

                fastest_anime_duration_ms: 100, //to change anime durations easily
            };
        },
        components: {
            VSliderYSmall,
            VBox,
            TransitionFade,
        },
        mounted(){

            //playback speed, accepts 0 to 2, default 1
            //also convert from localStorage's String back to Float
            if(window.localStorage.playback_rate === undefined){

                this.playback_rate = 1;

            }else{

                this.playback_rate = parseFloat(window.localStorage.playback_rate);
            }
            this.$refs.audio_playback.playbackRate = this.playback_rate;
            
            //playback speed, accepts 0 to 1, default 0.5
            //also convert from localStorage's String back to Float
            if(window.localStorage.playback_volume === undefined){

                this.playback_volume = 0.5;

            }else{

                this.playback_volume = parseFloat(window.localStorage.playback_volume);
            }
            this.$refs.audio_playback.volume = this.playback_volume;

            //initialise with 'empty' state
            this.current_playback_state = this.playback_states[0];

            //get playback_width for first time
            this.adjustToNewPlaybackDimension();

            //attach listeners to window for mouse Y
            window.addEventListener('mousemove', this.doPlaybackDrag);
            window.addEventListener('touchmove', this.doPlaybackDrag);
            window.addEventListener('mouseup', this.stopPlaybackDrag);
            window.addEventListener('touchend', this.stopPlaybackDrag);
            window.addEventListener('resize', this.adjustToNewPlaybackDimension);
            document.addEventListener('visibilitychange', this.syncSliderNeedleAnimeAfterSuspend);
        },
        beforeUnmount(){

            //remove listeners
            window.removeEventListener('mousemove', this.doPlaybackDrag);
            window.removeEventListener('touchmove', this.doPlaybackDrag);
            window.removeEventListener('mouseup', this.stopPlaybackDrag);
            window.removeEventListener('touchend', this.stopPlaybackDrag);
            window.removeEventListener('resize', this.adjustToNewPlaybackDimension);
            document.removeEventListener('visibilitychange', this.syncSliderNeedleAnimeAfterSuspend);
        },
        emits: [
            'isAnimePlaybackCompleted',
        ],
        props: {
            propFile: Object,
            propIsRecording: Boolean,
            propRecordingVolume: Number,    //0-1
            propTimeInterval: Number,  //based on VRecorder time_interval, needed for analyser during recording
        },
        watch: {
            async propFile(new_value){

                this.final_file = new_value;

                if(new_value === null){

                    return false;
                }

                const audio_context = new AudioContext();

                await new_value.arrayBuffer()
                    .then(buffer => audio_context.decodeAudioData(buffer))
                    .then(decoded_audio => decoded_audio.getChannelData(0)) //only 1 channel as expected
                    .then(audio_data => this.getVolumes(audio_data))
                    .then(() => {
                        this.attachRecordedAudioToPlayback();
                        this.current_playback_state = this.playback_states[2];
                    })
                    .catch(error => {
                        this.final_file = null;
                        this.current_playback_state = this.playback_states[0];
                        console.log(error);
                    });
            },
            propRecordingVolume(new_value){

                this.animeRecordingVisualiser(new_value);
            },
            propIsRecording(new_value){

                if(new_value === false){

                    return false;

                }

                //reset most things when recording a new instance
                //others will be automatically handled on new data
                if(this.is_playing === true){

                    this.pausePlayback();
                }

                this.current_playback_state = this.playback_states[1];
            },
            current_playback_state(new_value){

                if(
                    this.is_volume_ripples_available === true &&
                    (new_value === this.playback_states[3] || new_value === this.playback_states[4])
                ){

                    //for those that are not one-time, put here
                    this.animePlaybackStates();

                }else{

                    //for those that are one-time, put here, and we can disable/enable elements with this
                    this.emitIsAnimePlaybackCompleted(false);

                    this.animePlaybackStates();

                    this.anime_instance.finished.then(()=>{

                        this.emitIsAnimePlaybackCompleted(true);
                    });
                }
            },
        },
        methods: {
            syncSliderNeedleAnimeAfterSuspend(){

                //we need this because anime.suspendDocumentWhenHidden=false does not work
                //basically just to reposition slider anime to playback, else it doesn't do that
                //must call pause() first, else seek() is inaccurate
                if(document.visibilityState === 'visible' && this.playback_slider_needle_anime !== null){

                    const resume_later = this.is_playing;

                    if(this.is_playing === true){

                        //reminder that pausePlayback() also updates this.playback_slider_value
                        this.pausePlayback();
                    }

                    this.playback_slider_needle_anime.seek(this.playback_slider_value * this.playback_slider_needle_anime.duration);

                    if(resume_later === true){

                        const target = this.$refs.audio_playback;

                        //we want to mute to avoid the rare slight spike at certain db
                        target.muted = true;
                        this.playPlayback();
                        target.muted = false;
                    }
                }
            },
            createSliderNeedleKnobAnime(){
            
                //to be called during getPlaybackDuration(), window resize, changePlaybackRate()
                //we can then use .play/.pause/.seek
                //expects to already have accurate this.playback_slider_value

                //if playback_slider_needle is not involved in any other anime,
                //we are safe to remove its own anime for the purpose of re-do
                //during window resize or playback rate change
                if(this.is_volume_ripples_available === true){

                    anime.remove(this.$refs.playback_slider_needle);
                }

                //calculate starting point of translateX
                const ending_translateX = this.playback_slider_dimension.width;

                //calculate duration based on playback_rate
                const anime_duration = this.getRealDurationAfterPlaybackRate() * 1000;

                //create new needle anime
                this.playback_slider_needle_anime = anime({
                    targets: this.$refs.playback_slider_needle,
                    easing: 'linear',
                    autoplay: false,
                    loop: false,
                    duration: anime_duration,
                    translateX: [
                        '0px',
                        ending_translateX.toString() + 'px'
                    ],
                });
            },
            adjustToNewPlaybackDimension(){

                //expects playback_slider to have the same width
                //only using this at 'resize' event listener
                this.playback_slider_dimension = this.$refs.slider_dimension_reference.getBoundingClientRect();

                //create/recreate anime
                if(this.final_file !== null && this.playback_slider_needle_anime !== null){

                    this.createSliderNeedleKnobAnime();
                    this.syncSliderNeedleAnimeAfterSuspend();
                }
            },
            endPlaybackProperly(){

                if(this.playback_slider_value < 1){

                    return false;
                }

                //when <audio> .currentTime is dragged to absolute end, @ended does not fire
                //then, when play, it will fire @play then @ended
                //this is the fix, provided that you have loop=false
                //0.999 is better than 0.99
                const target = this.$refs.audio_playback;
                target.currentTime = 0.999 * this.final_file_duration;
                target.muted = true;    //we will undo this at playPlayback()
                target.play();
            },
            startPlaybackDrag(is_playback_slider_touch=false){

                if(this.final_file === null || this.is_volume_ripples_available === false){

                    return false;
                }

                this.is_dragging_playback_slider = true;
                this.is_playback_slider_touch = is_playback_slider_touch;

                if(this.is_playing === true){

                    this.pausePlayback();
                    this.resume_after_stop_dragging = true;
                }
            },
            doPlaybackDrag(event=null){

                if(this.is_dragging_playback_slider === true && this.playback_slider_dimension !== null){

                    //for mouse, we need these to avoid text highlighting, accidental permanent drag state, etc.
                    //for touch, we need these to avoid mouse firing
                    //best solution now is to let it raise Intervention on console when .cancelable is true on passive events
                    if(event !== null && event.cancelable === true){
                        
                        event.preventDefault();
                    }

                    //can use clientX, screenX, pageX, but pageX is most accurate in this context
                    let user_x = undefined;

                    if(this.is_playback_slider_touch === true){

                        user_x = event.touches[0].clientX;

                    }else{

                        user_x = event.clientX;
                    }

                    if(user_x >= this.playback_slider_dimension.left && user_x <= this.playback_slider_dimension.right){

                        this.playback_slider_value = (user_x - this.playback_slider_dimension.left) / this.playback_slider_dimension.width;

                    }else if(user_x < this.playback_slider_dimension.left){

                        this.playback_slider_value = 0;

                    }else if(user_x > this.playback_slider_dimension.right){

                        this.playback_slider_value = 1;
                    }

                    this.handlePlaybackDrag();

                    //troubleshoot if needed
                    // console.log("==========================");
                    // console.log('user_x: '+user_x);
                    // console.log('slider_top: '+playback_slider_dimension.top);
                    // console.log('slider_bottom: '+playback_slider_dimension.bottom);
                    // console.log(this.playback_slider_value);
                    // console.log("==========================");
                }
            },
            stopPlaybackDrag(){

                if(this.is_dragging_playback_slider === true){

                    //we reset touch detection on every startPlaybackDrag() and stopPlaybackDrag()
                    //so we get latest status of is_playback_slider_touch
                    //some browsers also trigger both touch + mouse events together
                    this.is_playback_slider_touch = false;

                    if(this.playback_slider_value < 1 && this.resume_after_stop_dragging === true){

                        this.playPlayback();
                        this.resume_after_stop_dragging = null;

                    }else if(this.playback_slider_value === 1){

                        this.endPlaybackProperly();
                    }

                    this.is_dragging_playback_slider = false;
                }

            },
            handlePlaybackDrag(){

                //expects playback_slider_value to be float 0 to 1

                //duration is the same regardless of playbackRate
                const jumped_anime_duration = this.playback_slider_value * this.playback_slider_needle_anime.duration;
                //duration changes when playbackRate changes
                const jumped_playback_duration = this.playback_slider_value * this.$refs.audio_playback.duration;

                //handle slider aesthetics
                //need to set .completed to false, else .play() starts from 0 if it has finished before
                //must be in ms
                this.playback_slider_needle_anime.completed = false;
                this.playback_slider_needle_anime.seek(jumped_anime_duration);

                //handle <audio>
                this.$refs.audio_playback.currentTime = jumped_playback_duration;

                //handle timer
                this.updateCurrentPlaybackTime();
            },
            skipPlayback(seconds=0, event=null){

                //+10 for forward, -10 for backward

                if(event !== null && event.cancelable === true){

                    event.preventDefault();
                }

                //do this instead of relying on :disabled, as :disabled makes sliders bug out
                if(seconds === 0 || this.final_file === null){

                    return false;
                }

                //check if audio is playing
                if(this.is_playing === true){

                    this.pausePlayback();
                    this.resume_after_stop_skipping = true;
                }

                const target = this.$refs.audio_playback;
                let updated_time = target.currentTime + seconds;

                if(updated_time < 0){

                    target.currentTime = 0;

                }else if(updated_time > this.final_file_duration){

                    target.currentTime = this.final_file_duration;

                }else{

                    target.currentTime = updated_time;
                }

                //update playback_slider_value and visuals
                this.playback_slider_value = target.currentTime / target.duration;
                this.handlePlaybackDrag();

                //resume if originally playing
                if(this.resume_after_stop_skipping === true && this.playback_slider_value < 1){

                    this.playPlayback();

                }else if(this.playback_slider_value === 1){

                    this.endPlaybackProperly();
                }

                this.resume_after_stop_skipping = null;
            },
            clearDelayClosePlaybackOptions(){

                //clear delay
                if(this.playback_options_timeout !== null){

                    clearTimeout(this.playback_options_timeout);
                    this.playback_options_timeout = null;
                }
            },
            delayClosePlaybackOptions(event=null){

                //intended only for touch events

                //as usual, close nothing if paused
                if(this.is_playing === false){

                    return false;
                }

                if(event !== null && event.cancelable === true){
                    
                    //Vue creates passive=false touch events for us
                    //we are safe, since our events using this function do not involve scrolling directly
                    event.preventDefault();
                }

                //clear any existing timeout
                this.clearDelayClosePlaybackOptions();

                this.playback_options_timeout = setTimeout(()=>{
                    this.togglePlaybackOptions(false);
                }, 3000);
            },
            togglePlaybackOptions(force_open_close=null){

                //force_open_close is true for open, false for close
                //force_open_close and !this.is_playback_options_open are not final
                //we also want to show playback_options when (1) volume_ripples are rendered, (2) volume is dragging,
                //and (3) is paused
                //we hide if user is dragging playback_slider or is playing

                //clear any existing timeout
                this.clearDelayClosePlaybackOptions();

                let should_close = null;

                //this statement covers all "should close" conditions
                if(force_open_close === null){

                    should_close = this.is_playback_options_open;

                }else{

                    should_close = !force_open_close;
                }

                //now we weigh in other conditions
                //as we want to close inner menus first, but only appropriately
                if(
                    this.should_close === true &&
                    this.is_volume_ripples_available === true && this.is_dragging_playback_slider === false &&
                    (this.is_dragging_volume === true || this.is_playing === false)
                ){

                    this.is_playback_speed_options_open = false;
                    this.is_playback_volume_open = false;
                }

                //conclude
                this.is_playback_options_open = !should_close;
            },
            resetRecordingVisualiser(){

                const recording_visualiser_circles = [
                    this.$refs.recording_visualiser_circle_0,
                    this.$refs.recording_visualiser_circle_1,
                    this.$refs.recording_visualiser_circle_2,
                ];

                //scale does not accept % or px, only percentage digit
                anime({
                    targets: recording_visualiser_circles,
                    easing: 'linear',
                    loop: false,
                    autoplay: true,
                    scaleX: '0',
                    scaleY: '0',
                    duration: this.fastest_anime_duration_ms,
                });
            },
            animeRecordingVisualiser(new_value){

                const recording_visualiser_circles = [
                    this.$refs.recording_visualiser_circle_0,
                    this.$refs.recording_visualiser_circle_1,
                    this.$refs.recording_visualiser_circle_2,
                ];

                //scale works with values from 0 to 1
                const base_target_percentage = 0.1;
                const percentage_increment = 0.3;
                
                anime.remove(recording_visualiser_circles);

                for(let x=0; x < recording_visualiser_circles.length; x++){

                    const extra_target_percentage = (x + 1) * percentage_increment;
                    const final_target_percentage = (new_value * extra_target_percentage) + base_target_percentage;

                    //scale does not accept % or px, only percentage digit
                    anime({
                        targets: recording_visualiser_circles[x],
                        scaleX: final_target_percentage.toString(),
                        scaleY: final_target_percentage.toString(),
                        autoplay: true,
                        easing: 'linear',
                        loop: false,
                        duration: this.propTimeInterval,
                    });
                }
            },
            updateCurrentPlaybackTime(){

                const target = this.$refs.audio_playback;

                //timer
                this.pretty_current_playback_time = new Date(
                    target.currentTime * 1000
                ).toISOString().substring(14, 19);
            },
            getRealDurationAfterPlaybackRate(){

                //note that when <audio> playbackRate changes, .duration is still the same
                return this.final_file_duration / this.playback_rate;
            },
            changePlaybackRate(new_value, event=null){

                if(event !== null && event.cancelable === true){

                    event.preventDefault();
                }

                //note that on every new file loaded into <audio>, playbackRate is reset
                //attachRecordedAudioToPlayback() will handle this inconvenience
                this.$refs.audio_playback.playbackRate = new_value;
                this.playback_rate = new_value;
                window.localStorage.playback_rate = new_value;

                //adjust anime
                const resume_later = this.is_playing;
                this.pausePlayback();
                this.createSliderNeedleKnobAnime();
                this.playback_slider_needle_anime.seek(this.playback_slider_value * this.playback_slider_needle_anime.duration);
                if(resume_later === true){

                    this.playPlayback();
                }
            },
            updateIsDraggingVolume(new_value){

                //we want this to pevent mouseleave from closing playback_options via mouseTogglePlaybackOptions()
                this.is_dragging_volume = new_value;
            },
            changePlaybackVolume(new_value){
                
                this.$refs.audio_playback.volume = new_value;
                this.playback_volume = new_value;
                window.localStorage.playback_volume = new_value;
            },
            togglePlaybackSpeedOptions(event=null){
                
                if(event !== null && event.cancelable === true){

                    event.preventDefault();
                }

                this.is_playback_speed_options_open = !this.is_playback_speed_options_open;
            },
            toggleRepeat(){

                this.is_repeat = !this.is_repeat;
            },
            togglePlaybackVolumeOptions(event=null){

                //note that slider malfunctions over :disabled elements, i.e. backward/forward, etc.

                if(event !== null && event.cancelable === true){

                    event.preventDefault();
                }

                this.is_playback_volume_open = !this.is_playback_volume_open;
            },
            playPlayback(){

                //using play/pause instead of remove+create prevents slight off-position on second play
                //our new anime position is already settled by handlePlaybackDrag()

                const target = this.$refs.audio_playback;

                //ended, so reset
                if(this.playback_slider_value === 1 && this.$refs.audio_playback.currentTime === this.final_file_duration){

                    //don't need seek(), as when .completed is true, play() restarts
                    this.playback_slider_value = 0;
                    this.playback_slider_needle_anime.completed = true;

                    //extra thing to do for our drag-to-end trick
                    target.muted = false;
                }

                //although redundant, we put target.muted=false here to guarantee it
                //as there has been a rare instance where playback had no audio unintentionally until the next replay
                target.muted = false;
                target.play();
                this.playback_slider_needle_anime.play();
                this.is_playing = true;
            },
            pausePlayback(){
                
                //if playing, call this before drag, then do playPlayback() once done
                //done at startPlaybackDrag() and stopPlaybackDrag()

                const target = this.$refs.audio_playback;

                target.pause();
                //recalculate slider value
                this.playback_slider_value = target.currentTime / this.final_file_duration;
                this.playback_slider_needle_anime.pause();
                this.is_playing = false;
            },
            togglePlaybackPlayPause(event=null){

                //we let everything stay at the end if playback truly ended
                //reset is only triggered on next play
                if(event !== null && event.cancelable === true){

                    event.preventDefault();
                }

                //do this instead of relying on :disabled, as :disabled makes sliders bug out
                if(this.final_file === null){

                    return false;
                }

                //check if playback is not playing
                if(this.is_playing === false){
                    
                    this.playPlayback();

                }else{

                    this.pausePlayback();
                }
            },
            emitIsAnimePlaybackCompleted(is_completed){

                this.$emit('isAnimePlaybackCompleted', is_completed);
            },
            animePlaybackStates(){

                const volume_ripples = this.$refs.volume_ripple;

                //reset all elements
                //reset all translates to 0

                switch(this.current_playback_state){

                    case this.playback_states[0]: {

                        //'empty', a.k.a. initial state

                        //remove related anime
                        anime.remove([
                            volume_ripples,
                            this.$refs.recording_visualiser,
                        ]);

                        //timeline will not work here
                        this.anime_instance = anime({
                            begin: ()=>{
                                //remove sunset
                                this.resetRecordingVisualiser();
                                //bring volume_ripples_container back to full height
                                this.$refs.volume_ripples_container.style.height = '12.5rem';
                            },
                            targets: volume_ripples,
                            scaleY: ['0', '0.9'],
                            autoplay: true,
                            loop: false,
                            easing: 'easeInOutCubic',
                            duration: 1000,
                            complete: ()=>{
                                //add ripple effect
                                anime({
                                    targets: volume_ripples,
                                    autoplay: true,
                                    easing: 'linear',
                                    loop: true,
                                    translateY: ['0%', '-5%', '5%', '0%'],
                                    delay: anime.stagger(100),
                                });
                            }
                        });
                    }
                    break;
                    case this.playback_states[1]:{

                        //'recording'

                        //remove related anime
                        anime.remove([
                            volume_ripples,
                            this.$refs.recording_visualiser,
                            this.$refs.playback_slider_needle,
                            this.$refs.recording_visualiser_circle_0,
                            this.$refs.recording_visualiser_circle_1,
                            this.$refs.recording_visualiser_circle_2,
                        ]);

                        this.anime_instance = anime.timeline({
                            easing: 'linear',
                            loop: false,
                            autoplay: true,
                        }).add({
                            begin: ()=>{
                                //playback_options depends on this,
                                //so set to false since it will be removed
                                this.is_volume_ripples_available = false;
                            },
                            //remove playback_slider_needle
                            targets: [this.$refs.playback_slider_needle],
                            opacity: 0,
                            duration: this.fastest_anime_duration_ms,
                            complete: ()=>{
                                this.$refs.playback_slider_needle.style.display = 'none';
                                this.playback_slider_needle_anime = null;
                            },
                        }).add({
                            //remove volume_ripples
                            targets: volume_ripples,
                            scaleY: ['0'],
                            translateY: ['0%'],
                            duration: this.fastest_anime_duration_ms,
                        }).add({
                            //make sunset available
                            begin: ()=>{
                                this.$refs.recording_visualiser.style.display = 'block';
                            },
                            targets: this.$refs.recording_visualiser,
                            opacity: 1,
                            duration: this.fastest_anime_duration_ms,
                            complete: ()=>{
                                //translateY the sunset to the right position
                                anime({
                                    targets: this.$refs.recording_visualiser,
                                    translateY: ['0%', '25%'],
                                    duration: 2000,
                                    easing: 'easeOutQuad'
                                });
                            }
                        });
                    }
                    break;
                    case this.playback_states[2]: {

                        //'attaching'
                        //run once only

                        //remove related anime
                        anime.remove([
                            volume_ripples,
                            this.$refs.recording_visualiser,
                            this.$refs.playback_slider_needle,
                            this.$refs.recording_visualiser_circle_0,
                            this.$refs.recording_visualiser_circle_1,
                            this.$refs.recording_visualiser_circle_2,
                        ]);

                        this.anime_instance = anime.timeline({
                            easing: 'linear',
                            loop: false,
                            autoplay: true,
                        }).add({
                            //translateY sunset back to top
                            begin: this.resetRecordingVisualiser,
                            targets: this.$refs.recording_visualiser,
                            translateY: ['0%'],
                            duration: this.fastest_anime_duration_ms
                        }).add({
                            //remove sunset
                            targets: this.$refs.recording_visualiser,
                            opacity: 0,
                            duration: this.fastest_anime_duration_ms,
                            complete: ()=>{
                                this.$refs.recording_visualiser.style.display = 'hidden';
                                //12.5rem to 10rem once is sufficient, but re-running is fine
                                this.$refs.volume_ripples_container.style.height = '10rem';
                                //set volume_ripples
                                this.adjustVolumeRipples();
                            },
                        }).add({
                            //make playback_slider_needle available
                            targets: [this.$refs.playback_slider_needle],
                            begin: ()=>{
                                this.$refs.playback_slider_needle.style.display = 'block';
                            },
                            opacity: 1,
                            duration: this.fastest_anime_duration_ms * 2,
                            complete: ()=>{
                                //we want the entire anime to finish before this condition unlocks other actions
                                //to delay this (so users can enjoy the anime), we don't use setTimeout
                                //we multiply duration above instead, so that we can still fully rely on anime's .finished.then()
                                this.is_volume_ripples_available = true;
                            }
                        });
                    }
                    break;
                    case this.playback_states[3]: {

                        //'can_play'
                        //will trigger after 'loading', so this is basically to undo 'loading' state
                        //they fire on file load and on every start-from-beginning play

                        //remove related anime
                        anime.remove([
                            volume_ripples,
                        ]);

                        this.anime_instance = anime({
                            targets: volume_ripples,
                            translateY: ['0%'],
                            duration: 0,    //must be 0, no other solutions in this context
                            autoplay: true,
                            loop: false,
                            easing: 'linear',
                        });
                    }
                    break;
                    case this.playback_states[4]:

                        //'loading'
                        
                        //remove related anime
                        anime.remove([
                            volume_ripples,
                        ]);

                        //create fast ripple effect for volume_ripples to show that it is loading
                        this.anime_instance = anime({
                            targets: volume_ripples,
                            translateY: ['0%', '-5%', '5%', '0%'],
                            autoplay: true,
                            loop: true,
                            easing: 'linear',
                            delay: anime.stagger(20),
                        });
                    break;
                    default:
                        
                        console.log('State is currently null or not one of the declared playback_states.');
                        return false;
                }
            },
            getVolumes(audio_data){

                let bucket_peaks = [];
                let bucket_threshold = Math.round(audio_data.length / this.bucket_quantity);
                //-1 to adjust for for-loop and lets us run code on last sample of each bucket (avoids < _ -1)
                let bucket_threshold_count = bucket_threshold - 1;
                let bucket_max = 0;

                for(let x = 0; x < audio_data.length; x++){

                    //check if we are at last sample of current bucket
                    if(x === bucket_threshold_count){

                        //store max peak
                        bucket_peaks.push(bucket_max);

                        //reset
                        bucket_max = 0;

                        //shift to next bucket
                        bucket_threshold_count += bucket_threshold;
                    }
                    
                    //evaluate max peak in current bucket
                    if(audio_data[x] > bucket_max){

                        bucket_max = audio_data[x];
                    }
                }

                //if file is too short or cannot be equally divided, fill up with 0 to meet bucket_quantity target
                while(bucket_peaks.length < this.bucket_quantity){

                    bucket_peaks.push(0);
                }

                //store highest peaks
                this.file_volumes = bucket_peaks;

                //we don't calculate volume range because it is unnecessary
                //0.1-0.2 is not 55%-60% but 0%-100%
                //min and max range is also -1 to 1, so need extra 'if' statements
                //lastly, we expect -1 to 1, but at 0 audio, we get only -0.0001
            },
            adjustVolumeRipples(){

                //we calculate height relative to most quiet and loudest parts
                //samples are expected to be between -1 and 1, but we get -0.0001 when no audio


                // //now we find the highest volume, and its distance from max height
                // //we will shift everything based on this difference
                // let volume_range_deficit = 0;
                // let highest_file_volume = null;

                // highest_file_volume = this.arrayMax(this.file_volumes);

                // if(highest_file_volume < 0){

                //     volume_range_deficit = 100 - 50 - (((highest_file_volume * -1) / volume_range) * 100);
                    
                // }else{

                //     volume_range_deficit = 100 - ((highest_file_volume / volume_range) * 100);
                // }

                //shift half to make it readable, not full, else it'll be globally inconsistent for user
                // volume_range_deficit = volume_range_deficit / 2;

                let scaleY_percentage = 0;

                for(let x=0; x < this.bucket_quantity; x++){

                    // if(this.file_volumes[x] < 0){
                        
                    //     scaleY_percentage = (1 - (this.file_volumes[x] * -1)) * 50;

                    // }else{

                    //     scaleY_percentage = 50 + (this.file_volumes[x] * 50);
                    // }

                    //expected volume range is -1 to 0, but our peaks at 0 audio is still -0.0001...
                    //so we recalibrate from lower and upper 50 to full 100
                    //instead of <0 ... =0, if you prefer 0 to be visible, do <0.05 ... =5
                    //UPDATE: non-zero feels more functional for end user
                    if(this.file_volumes[x] < 0.05){

                        scaleY_percentage = 0.05;

                    }else if(this.file_volumes[x] > 0.9){

                        //we max at 0.9 to make space for -+5% translateY anime
                        scaleY_percentage = 0.9;

                    }else{

                        scaleY_percentage = this.file_volumes[x];
                    }
                        
                    //add the deficit
                    // scaleY_percentage += volume_range_deficit;

                    //this performs fine, so do not add Tailwind transition, else it interferes
                    anime({
                        targets: this.$refs.volume_ripple[x],
                        scaleY: scaleY_percentage.toString(),
                        autoplay: true,
                        loop: false,
                        easing: 'easeInOutQuad',
                        duration: 200,
                    });
                }
            },
            attachRecordedAudioToPlayback(){

                if(this.final_file === null){

                    return false;
                }

                //attach file into <audio>
                this.$refs.audio_playback.src = URL.createObjectURL(this.final_file);

                //free the memory
                this.$refs.audio_playback.onload = function(){
                    return URL.revokeObjectURL(this.$refs.audio_playback.src);
                };

                //no updating current_playback_state here, we rely on <audio> for that

                //on every new file loaded into <audio>, playbackRate is reset
                this.$refs.audio_playback.playbackRate = this.playback_rate;

                return true;
            },
            getPlaybackDuration(){

                //there's a bug that gives us 'Infinity'
                //this is how we fix it
                //https://stackoverflow.com/a/69512775
                if(this.$refs.audio_playback.duration == 'Infinity'){

                    const handler = ()=>{

                        this.$refs.audio_playback.currentTime = 0;
                        this.$refs.audio_playback.removeEventListener('timeupdate', handler);
                        this.final_file_duration = this.$refs.audio_playback.duration;

                        //create anime
                        this.playback_slider_value = 0;
                        this.createSliderNeedleKnobAnime();

                        //mm:ss
                        //only for duration display we will use floor
                        this.pretty_playback_duration = 
                            new Date(Math.floor(this.final_file_duration) * 1000).toISOString().substring(14, 19);
                    };

                    this.$refs.audio_playback.currentTime = 1e101;
                    this.$refs.audio_playback.addEventListener('timeupdate', handler);

                }else{

                    this.final_file_duration = this.$refs.audio_playback.duration;

                    //create anime
                    this.playback_slider_value = 0;
                    this.createSliderNeedleKnobAnime();
                }

                //don't try to access this.final_file_duration precisely here, as something is async
                //you'll get 0, but if you check via watch, the value does change
                //put your code in handler instead if you need to run something else
            },

        }
    }
</script>