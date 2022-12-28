<template>
    <audio
        ref="audio_playback"
        @loadedmetadata="getPlaybackDuration()"
        @timeupdate="updateCurrentPlaybackTime()"
        @ended="pausePlayback()"
        @canplay="current_playback_state = playback_states[2]"
        @waiting="current_playback_state = playback_states[3]"
    ></audio>
    <div
        class="text-center h-[15rem] relative"
    >
        <!--extras, h-20 made possible with spacing being inside elements and not outside-->
        <div ref="playback_extras" class="absolute w-full h-20 bottom-0 opacity-0 hidden px-2">
            <!--playback slider-->
            <div
                ref="playback_slider"
                class="w-full h-10 relative top-0 bottom-0 my-auto touch-none"
                @mousedown.stop="[startPlaybackDrag(), doPlaybackDrag($event)]"
                @touchstart.stop="[startPlaybackDrag(true), doPlaybackDrag($event)]"
            >
                <div
                    ref="playback_slider_knob"
                    class="w-4 h-4 rounded-full bg-theme-black top-0 my-auto absolute"
                ></div>
            </div>
            <!--timers-->
            <div class="w-full h-10 text-base items-center grid grid-cols-4 px-2">
                <span class="col-start-1 col-span-1 text-left">{{pretty_current_playback_time}}</span>
                <span class="col-start-4 col-span-1 text-right">{{pretty_playback_duration}}</span>
            </div>
        </div>
        <!--recording visualiser-->
        <div
            ref="recording_visualiser"
            class="absolute w-[10rem] h-[10rem] left-0 right-0 top-0 m-auto opacity-0 hidden"
        >
            <div class="relative w-full h-full">
                <div
                    ref="volume_analyser_circle_0"
                    class="absolute w-0 h-0 left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-dominant/60"
                ></div>
                <div
                    ref="volume_analyser_circle_1"
                    class="absolute w-0 h-0 left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-dominant/40"
                ></div>
                <div
                    ref="volume_analyser_circle_2"
                    class="absolute w-0 h-0 left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-dominant/20"
                ></div>
            </div>
        </div>
        <!--main-->
        <div ref="playback_main" class="absolute w-full h-[15rem]">
            <div class="w-full h-full relative">
                <!--volume ripples-->
                <div class="w-full h-full absolute px-2">
                    <div
                        ref="slider_dimension_reference"
                        class="w-full h-full relative"
                    >
                        <div ref="playback_slider_needle" class="absolute h-full left-0 opacity-0 hidden">
                            <div
                                class="w-1 h-full rounded-full bg-theme-dominant -right-0.5 absolute"
                            ></div>
                        </div>
                        <div class="absolute w-full h-full grid grid-cols-max grid-flow-col gap-1 place-items-center">
                            <div
                                v-for="volume_ripple_container in bucket_quantity" :key="volume_ripple_container"
                                :class="[
                                    (current_playback_state === null ? 'hidden' : ''),
                                    (current_playback_state === playback_states[0] ? 'bg-theme-idle' : ''),
                                    (current_playback_state === playback_states[1] ? 'bg-theme-idle' : ''),
                                    (current_playback_state === playback_states[2] ? 'bg-theme-black' : ''),
                                    (current_playback_state === playback_states[3] ? 'bg-theme-black' : ''),
                                    'col-span-1 w-0.5'
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
                    class="absolute w-full h-full text-theme-black"
                    tabindex="0"
                    @keyup.enter.self.stop="[togglePlaybackOptions(), troubleshootEventListener('b')]"
                    @mouseenter.self.stop="[mouseTogglePlaybackOptions(true), troubleshootEventListener('mouseenter')]"
                    @mouseleave.self.stop="[mouseTogglePlaybackOptions(false), troubleshootEventListener('mouseleave')]"
                    @touchend="[togglePlaybackOptions(true), delayClosePlaybackOptions($event), troubleshootEventListener('touchend')]"
                >
                    <TransitionFade>
                        <VBox
                            v-show="is_playback_options_open && final_file !== null"
                            class="w-full h-full grid grid-rows-5 grid-cols-4 items-center rounded-lg gap-2 p-2 text-xl"
                        >
                            <!--backward-->
                            <div class="row-start-2 row-span-3 col-start-1 col-span-1 h-full">
                                <button
                                    @click.stop="skipPlayback(-10, $event)"
                                    @touchend.stop="skipPlayback(-10, $event)"
                                    :class="[
                                        final_file === null ? 'cursor-not-allowed' : '',
                                        'w-full h-full'
                                    ]"
                                >
                                    <i ref="playback_go_back_icon" class="fas fa-rotate-left"></i>
                                    <br>
                                    <span class="text-base">10</span>
                                </button>
                            </div>
                            <!--play pause-->
                            <div class="row-start-2 row-span-3 col-start-2 col-span-2 h-full">
                                <button
                                    @click.stop="togglePlaybackPlayPause($event)"
                                    @touchend.stop="togglePlaybackPlayPause($event)"
                                    :class="[
                                        final_file === null ? 'cursor-not-allowed' : '',
                                        'w-full h-full'
                                    ]"
                                >
                                    <i
                                        :class="[
                                            is_playing? 'fa-pause' : 'fa-play',
                                            'fas text-4xl'
                                        ]"
                                    ></i>
                                </button>
                            </div>
                            <!--forward-->
                            <div class="row-start-2 row-span-3 col-start-4 col-span-1 h-full">
                                <button
                                    @click.stop="skipPlayback(10, $event)"
                                    @touchend.stop="skipPlayback(10, $event)"
                                    :class="[
                                        final_file === null ? 'cursor-not-allowed' : '',
                                        'w-full h-full'
                                    ]"
                                >
                                    <i ref="playback_go_forward_icon" class="fas fa-rotate-right"></i>
                                    <br>
                                    <span class="text-base">10</span>
                                </button>
                            </div>
                            <!--open/close playback speed-->
                            <div
                                ref="playback_speed_options_opener"
                                class="row-start-5 row-span-1 col-start-2 col-span-1 h-full"
                            >
                                <button
                                    @click.prevent.stop="[togglePlaybackSpeedOptions(), troubleshootEventListener('g')]"
                                    @touchend="[togglePlaybackSpeedOptions($event), troubleshootEventListener('g')]"
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
                            <!--open/close playback volume-->
                            <div
                                ref="playback_volume_opener"
                                class="row-start-5 row-span-1 col-start-3 col-span-1 h-full"
                            >
                                <button
                                    @click.prevent.stop="[togglePlaybackVolumeOptions(), troubleshootEventListener('g')]"
                                    @touchend="[togglePlaybackVolumeOptions($event), troubleshootEventListener('g')]"
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
                            <!--playback speed menu-->
                            <TransitionFade>
                                <VBox
                                    v-show="is_playback_speed_options_open"
                                    v-click-outside="{
                                        var_name_for_element_bool_status: 'is_playback_speed_options_open',
                                        refs_to_exclude: ['playback_speed_options_opener']
                                    }"
                                    class="row-start-1 row-span-4 col-start-2 col-span-1 w-full h-full"
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
                                                    @click.self.stop="changePlaybackRate(1.5, $event)"
                                                    @touchend.self.stop="changePlaybackRate(1.5, $event)"
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
                                                    @click.self.stop="changePlaybackRate(1, $event)"
                                                    @touchend.self.stop="changePlaybackRate(1, $event)"
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
                                                    @click.self.stop="changePlaybackRate(0.5, $event)"
                                                    @touchend.self.stop="changePlaybackRate(0.5, $event)"
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
                            </TransitionFade>
                            <!--playback volume menu-->
                            <TransitionFade>
                                <VBox
                                    v-show="is_playback_volume_open"
                                    v-click-outside="{
                                        var_name_for_element_bool_status: 'is_playback_volume_open',
                                        refs_to_exclude: ['playback_volume_opener']
                                    }"
                                    class="row-start-1 row-span-4 col-start-3 col-span-1 w-full h-full"
                                >
                                    <div
                                        class="relative w-full h-full"
                                        @touchmove="[clearDelayClosePlaybackOptions(), troubleshootEventListener('touchmove')]"
                                    >
                                            <div
                                                class="
                                                    w-full h-full absolute text-center p-2 py-6
                                                "
                                            >
                                                <VSliderYSmall
                                                    ref="volume_slider"
                                                    :propSliderValue="playback_volume"
                                                    @hasNewSliderValue="changePlaybackVolume($event)"
                                                    @hasNewIsDraggingValue="updateIsDraggingVolume($event)"
                                                    class="h-full"
                                                />
                                            </div>
                                    </div>
                                </VBox>
                            </TransitionFade>
                        </VBox>
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

                slider_value: 0,
                is_dragging: false,
                is_slider_touch: false,
                slider_dimension: null,
                slider_knob_anime: null, //we play/pause instead of new anime() to prevent second play off-position
                slider_needle_anime: null, //we play/pause instead of new anime() to prevent second play off-position
                resume_after_stop_dragging: null,    //to know whether to resume after done navigating
                resume_after_stop_skipping: null,   //to know whether to resume after done navigating

                playback_rate: 1,  //accepts 0 to 2
                playback_volume: 0.5, //accepts 0 to 1
                is_repeat: false,

                is_playback_options_open: false,
                is_playback_speed_options_open: false,
                is_playback_volume_open: false,
                is_dragging_volume: false,
                playback_options_timeout: null,

                is_first_time_playback_main: true, //change playback_main height once only
                playback_states: ['empty', 'recording', 'can_play', 'loading'],
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
        },
        beforeUnmount(){

            //remove listeners
            window.removeEventListener('mousemove', this.doPlaybackDrag);
            window.removeEventListener('touchmove', this.doPlaybackDrag);
            window.removeEventListener('mouseup', this.stopPlaybackDrag);
            window.removeEventListener('touchend', this.stopPlaybackDrag);
            window.removeEventListener('resize', this.adjustToNewPlaybackDimension);
        },
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
                        //no need to fire 'can_play' here, <audio> @canplay will do that for us
                        this.attachRecordedAudioToPlayback();
                    })
                    .catch(error => {
                        this.final_file = null;
                        this.current_playback_state = this.playback_states[0];
                        console.log(error);
                    });
            },
            propRecordingVolume(new_value){

                this.animeVolumeAnalyser(new_value);
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
            current_playback_state(){

                this.animePlaybackStates();
            },
            is_playing(new_value){
                console.log('is_playing? '+new_value);
            }
        },
        methods: {
            createSliderNeedleKnobAnime(){

                //to be called one time only at getPlaybackDuration(), or on window resize
                //we can then use .play/.pause/.seek
                //expects to already have accurate this.slider_value

                //check and remove any existing anime
                this.slider_value = 0;

                //calculate starting point of translateX
                const starting_translateX = this.slider_value * this.slider_dimension.width;
                const ending_translateX = this.slider_dimension.width;

                //create new needle anime
                this.slider_needle_anime = anime({
                    targets: this.$refs.playback_slider_needle,
                    easing: 'linear',
                    autoplay: false,
                    loop: false,
                    duration: this.final_file_duration * 1000,
                    translateX: [
                        (starting_translateX).toString() + 'px',
                        (ending_translateX).toString() + 'px'
                    ],
                });

                //create new knob anime, remembering to shift to center
                //8px is for -translate-x-2, cannot use getBoundingClientRect() here
                const knob_distance_to_center = 8;
                this.slider_knob_anime = anime({
                    targets: this.$refs.playback_slider_knob,
                    easing: 'linear',
                    autoplay: false,
                    loop: false,
                    duration: this.final_file_duration * 1000,
                    translateX: [
                        (starting_translateX - knob_distance_to_center).toString() + 'px',
                        (ending_translateX - knob_distance_to_center).toString() + 'px'
                    ],
                });

            },
            adjustToNewPlaybackDimension(){

                //expects playback_slider to have the same width
                //only using this at 'resize' event listener
                this.slider_dimension = this.$refs.slider_dimension_reference.getBoundingClientRect();

                //create/recreate anime
                if(this.final_file !== null){

                    this.createSliderNeedleKnobAnime();
                }
            },
            endPlaybackProperly(){

                if(this.slider_value < 1){

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
            startPlaybackDrag(is_slider_touch=false){

                this.is_dragging = true;
                this.is_slider_touch = is_slider_touch;

                if(this.is_playing === true){

                    this.pausePlayback();
                    this.resume_after_stop_dragging = true;
                }
            },
            doPlaybackDrag(event=null){

                if(this.is_dragging === true && this.slider_dimension !== null){

                    //for mouse, we need these to avoid text highlighting, accidental permanent drag state, etc.
                    //for touch, we need these to avoid mouse firing
                    //best solution now is to let it raise Intervention on console when .cancelable is true on passive events
                    if(event !== null && event.cancelable === true){
                        
                        event.preventDefault();
                    }

                    //can use clientX, screenX, pageX, but pageX is most accurate in this context
                    let user_x = undefined;

                    if(this.is_slider_touch === true){

                        user_x = event.touches[0].clientX;

                    }else{

                        user_x = event.clientX;
                    }

                    if(user_x >= this.slider_dimension.left && user_x <= this.slider_dimension.right){

                        this.slider_value = (user_x - this.slider_dimension.left) / this.slider_dimension.width;

                    }else if(user_x < this.slider_dimension.left){

                        this.slider_value = 0;

                    }else if(user_x > this.slider_dimension.right){

                        this.slider_value = 1;
                    }

                    this.handlePlaybackDrag();

                    //troubleshoot if needed
                    // console.log("==========================");
                    // console.log('user_x: '+user_x);
                    // console.log('slider_top: '+slider_dimension.top);
                    // console.log('slider_bottom: '+slider_dimension.bottom);
                    // console.log(this.slider_value);
                    // console.log("==========================");
                }
            },
            stopPlaybackDrag(){

                if(this.is_dragging === true){

                    //we reset touch detection on every startPlaybackDrag() and stopPlaybackDrag()
                    //so we get latest status of is_slider_touch
                    //some browsers also trigger both touch + mouse events together
                    this.is_slider_touch = false;

                    if(this.slider_value < 1 && this.resume_after_stop_dragging === true){

                        this.playPlayback();
                        this.resume_after_stop_dragging = null;

                    }else if(this.slider_value === 1){

                        this.endPlaybackProperly();
                    }

                    this.is_dragging = false;
                }

            },
            handlePlaybackDrag(){

                //expects slider_value to be float 0 to 1
                const current_duration = this.slider_value * this.final_file_duration;

                //handle slider aesthetics
                //need to set .completed to false, else .play() starts from 0 if it has finished before
                //must be in ms
                this.slider_needle_anime.completed = false;
                this.slider_knob_anime.completed = false;
                this.slider_needle_anime.seek(current_duration * 1000);
                this.slider_knob_anime.seek(current_duration * 1000);

                //handle <audio>
                this.$refs.audio_playback.currentTime = current_duration;

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

                //update slider_value and visuals
                this.slider_value = target.currentTime / target.duration;
                this.handlePlaybackDrag();

                //resume if originally playing
                if(this.resume_after_stop_skipping === true && this.slider_value < 1){

                    this.playPlayback();

                }else if(this.slider_value === 1){

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
            mouseTogglePlaybackOptions(force_open_close=null){

                //clear any existing timeout
                this.clearDelayClosePlaybackOptions();

                //if volume is dragging, we can just prevent changes for playback_options
                if(this.is_dragging_volume === true){

                    return false;
                }

                //close everything in playback_options first
                if(force_open_close === false || (force_open_close === null && this.is_playback_options_open === true)){

                    this.is_playback_speed_options_open = false;
                    this.is_playback_volume_open = false;
                }

                if(force_open_close !== null){

                    this.is_playback_options_open = force_open_close;

                }else{

                    this.is_playback_options_open = !this.is_playback_options_open;
                }
            },
            togglePlaybackOptions(force_open_close=null){

                //clear any existing timeout
                this.clearDelayClosePlaybackOptions();

                //close everything in playback_options first
                if(force_open_close === false || (force_open_close === null && this.is_playback_options_open === true)){

                    this.is_playback_speed_options_open = false;
                    this.is_playback_volume_open = false;
                }

                if(force_open_close !== null){

                    this.is_playback_options_open = force_open_close;

                }else{

                    this.is_playback_options_open = !this.is_playback_options_open;
                }
            },
            resetVolumeAnalyser(){

                const volume_analyser_circles = [
                    this.$refs.volume_analyser_circle_0,
                    this.$refs.volume_analyser_circle_1,
                    this.$refs.volume_analyser_circle_2,
                ];

                anime({
                    targets: volume_analyser_circles,
                    easing: 'linear',
                    loop: false,
                    autoplay: true,
                    width: '0',
                    height: '0',
                    duration: this.fastest_anime_duration_ms,
                });
            },
            animeVolumeAnalyser(new_value){

                const volume_analyser_circles = [
                    this.$refs.volume_analyser_circle_0,
                    this.$refs.volume_analyser_circle_1,
                    this.$refs.volume_analyser_circle_2,
                ];

                //circles have width and height of 20-30, 30-50, 50-80 %
                let base_target_percentage = 10;
                const percentage_increment = 30;
                
                anime.remove(volume_analyser_circles);

                for(let x=0; x < volume_analyser_circles.length; x++){

                    const extra_target_percentage = (x + 1) * percentage_increment;

                    const final_target_percentage = (new_value * extra_target_percentage) + base_target_percentage;

                    anime({
                        targets: volume_analyser_circles[x],
                        width: final_target_percentage.toString() + '%',
                        height: final_target_percentage.toString() + '%',
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
            changePlaybackRate(new_value, event=null){

                if(event !== null && event.cancelable === true){

                    event.preventDefault();
                }

                //note that on every new file loaded into <audio>, playbackRate is reset
                //attachRecordedAudioToPlayback() will handle this inconvenience
                this.$refs.audio_playback.playbackRate = new_value;
                this.playback_rate = new_value;
                window.localStorage.playback_rate = new_value;
            },
            updateIsDraggingVolume(new_value){

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
                if(this.slider_value === 1 && this.$refs.audio_playback.currentTime === this.final_file_duration){

                    //don't need seek(), as when .completed is true, play() restarts
                    this.slider_value = 0;
                    this.slider_needle_anime.completed = true;
                    this.slider_knob_anime.completed = true;

                    //extra thing to do for our drag-to-end trick
                    target.muted = false;
                }

                target.play();
                this.slider_needle_anime.play();
                this.slider_knob_anime.play();
                this.is_playing = true;
            },
            pausePlayback(){
                
                //if playing, call this before drag, then do playPlayback() once done
                //done at startPlaybackDrag() and stopPlaybackDrag()

                const target = this.$refs.audio_playback;

                target.pause();
                //recalculate slider value
                this.slider_value = this.$refs.audio_playback.currentTime / this.final_file_duration;
                this.slider_needle_anime.pause();
                this.slider_knob_anime.pause();
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
            animePlaybackStates(){

                const volume_ripples = this.$refs.volume_ripple;

                //reset all elements
                //reset all translates to 0
                anime.remove([
                    volume_ripples,
                    this.$refs.playback_main,
                    this.$refs.playback_extras,
                    this.$refs.recording_visualiser,
                    this.$refs.volume_analyser_circle_0,
                    this.$refs.volume_analyser_circle_1,
                    this.$refs.volume_analyser_circle_2,
                ]);

                switch(this.current_playback_state){

                    case this.playback_states[0]: {

                        //'empty', a.k.a. initial state

                        //reset volume_analyser if open, animate volume_ripples
                        anime({
                            begin: this.resetVolumeAnalyser,
                            targets: volume_ripples,
                            height: ['0%', '50%'],
                            autoplay: true,
                            loop: false,
                            easing: 'easeInOutCubic',
                            duration: 1000,
                        });
                        anime({
                            targets: volume_ripples,
                            autoplay: true,
                            easing: 'linear',
                            loop: true,
                            translateY: ['0%', '-5%', '5%', '0%'],
                            delay: anime.stagger(100),
                        });
                        
                    }
                    break;
                    case this.playback_states[1]:

                        //'recording'

                        //fade playback_extras and hide, clear volume_ripples, sunset recording_visualiser
                        anime.timeline({
                            easing: 'linear',
                            loop: false,
                            autoplay: true,
                        }).add({
                            targets: [this.$refs.playback_extras, this.$refs.playback_slider_needle],
                            opacity: 0,
                            duration: this.fastest_anime_duration_ms,
                            complete: ()=>{
                                this.$refs.playback_extras.style.display = 'none';
                                this.$refs.playback_slider_needle.style.display = 'none';
                            },
                        }).add({
                            targets: volume_ripples,
                            translateY: ['0%'],
                            height: ['0%'],
                            duration: this.fastest_anime_duration_ms,
                        }).add({
                            begin: ()=>{
                                this.$refs.recording_visualiser.style.display = 'block';
                            },
                            targets: this.$refs.recording_visualiser,
                            opacity: 1,
                            duration: this.fastest_anime_duration_ms,
                        }).add({
                            targets: this.$refs.recording_visualiser,
                            translateY: ['0%', '25%'],
                            duration: 2000
                        });

                    break;
                    case this.playback_states[2]: {

                        //'can_play'

                        //process volume_ripples, fade out recording_visualiser, fade in playback_extras
                        let main_anime = anime.timeline({
                            easing: 'linear',
                            loop: false,
                            autoplay: true,
                        });
                        
                        //if first time, adjust playback_main
                        if(this.is_first_time_playback_main === true){

                            main_anime.add({
                                targets: this.$refs.playback_main,
                                height: '10rem',
                                duration: this.fastest_anime_duration_ms
                            });

                            this.is_first_time_playback_main = false;
                        }

                        //continue
                        main_anime.add({
                            begin: this.resetVolumeAnalyser,
                            targets: this.$refs.recording_visualiser,
                            translateY: ['0%'],
                            duration: this.fastest_anime_duration_ms
                        }).add({
                            targets: this.$refs.recording_visualiser,
                            opacity: 0,
                            duration: this.fastest_anime_duration_ms,
                            complete: ()=>{
                                this.$refs.recording_visualiser.style.display = 'hidden';
                                this.adjustVolumeRipples();
                            },
                        }).add({
                            targets: [this.$refs.playback_extras, this.$refs.playback_slider_needle],
                            begin: ()=>{
                                this.$refs.playback_extras.style.display = 'block';
                                this.$refs.playback_slider_needle.style.display = 'block';
                            },
                            opacity: 1,
                            duration: this.fastest_anime_duration_ms,
                        });

                    }
                    break;
                    case this.playback_states[3]:

                        //'loading'
                        
                        //only reposition volume_ripples, then show that it is loading
                        anime({
                            targets: volume_ripples,
                            translateY: ['0%'],
                            duration: 0,    //must be 0, no other solutions in this context
                            autoplay: true,
                            loop: false,
                            easing: 'linear',
                        });
                        anime({
                            targets: volume_ripples,
                            translateY: ['0%', '-10%', '10%', '0%'],
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

                let current_height = 0;

                for(let x=0; x < this.bucket_quantity; x++){

                    // if(this.file_volumes[x] < 0){
                        
                    //     current_height = (1 - (this.file_volumes[x] * -1)) * 50;

                    // }else{

                    //     current_height = 50 + (this.file_volumes[x] * 50);
                    // }

                    //expected volume range is -1 to 0, but our peaks at 0 audio is still -0.0001...
                    //so we recalibrate from lower and upper 50 to full 100
                    //instead of <0 ... =0, if you prefer 0 to be visible, do <0.05 ... =5
                    //UPDATE: non-zero feels more functional for end user
                    if(this.file_volumes[x] < 0.05){

                        current_height = 5;

                    }else if(this.file_volumes[x] > 1){

                        current_height = 100;

                    }else{

                        current_height = this.file_volumes[x] * 100;
                    }
                        
                    //add the deficit
                    // current_height += volume_range_deficit;

                    //this performs fine, so do not add Tailwind transition, else it interferes
                    anime({
                        targets: this.$refs.volume_ripple[x],
                        height: current_height.toString() + '%',
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
                    this.createSliderNeedleKnobAnime();
                }

                //don't try to access this.final_file_duration precisely here, as something is async
                //you'll get 0, but if you check via watch, the value does change
                //put your code in handler instead if you need to run something else
            },

        }
    }
</script>