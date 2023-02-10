<template>
    <audio
        ref="audio_playback"
        @loadedmetadata="getPlaybackDuration()"
        @timeupdate="updateCurrentPlaybackTime()"
        @canplay="current_playback_state = playback_states[3]"
        @waiting="current_playback_state = playback_states[4]"
        @ended="pausePlayback()"
    ></audio>

    <!--size priority: playback_main, then ripples, then everything else-->
    <div
        :class="[
            propIsSticky ? 'bg-theme-light/60 backdrop-blur border-t border-theme-black/5' : '',
            'h-[6.25rem] text-center relative'
        ]"
    >

        <!--recording visualiser-->
        <div
            ref="recording_visualiser"
            class="absolute w-[6.25rem] h-[6.25rem] left-0 right-0 top-0 bottom-0 m-auto opacity-0 hidden"
        >
            <div class="relative w-full h-full">
                <div
                    ref="recording_visualiser_circle_0"
                    class="absolute w-full h-full scale-0 left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-yellow/60"
                ></div>
                <div
                    ref="recording_visualiser_circle_1"
                    class="absolute w-full h-full scale-0 left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-yellow/40"
                ></div>
                <div
                    ref="recording_visualiser_circle_2"
                    class="absolute w-full h-full scale-0 left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-yellow/20"
                ></div>
            </div>
        </div>

        <!--
            ACTUAL VAUDIOPLAYBACK
            ripples, slider, volume, play/pause, rate, timers
            we want it like this to be able to hide everything when needed
        -->
        <div
            ref="playback_main"
            :class="[
                final_file === null ? 'border-theme-light-gray/10' : 'border-theme-light-gray',
                'w-full h-fit absolute left-0 right-0 top-0 bottom-0 m-auto text-theme-black border-2 rounded-2xl p-2'
            ]"
        >
            <!--ripples, slider-->
            <div
                :class="[
                    final_file === null ? 'opacity-10 cursor-default' : 'opacity-100 cursor-pointer',
                    'h-10 w-full relative'
                ]"
            >
                <!--ripples-->
                <div
                    ref="volume_ripples_container"
                    class="w-full h-6 absolute top-0 flex flex-row justify-evenly"
                >
                    <div
                        v-for="volume_ripple in bucket_quantity" :key="volume_ripple"
                        ref="volume_ripple"
                        class="h-full scale-y-0 origin-bottom"
                    >
                        <div
                            :class="[
                                (current_playback_state === playback_states[0] ? 'outline-1 outline outline-theme-dark-gray' : ''),
                                (current_playback_state === playback_states[1] ? 'outline-1 outline outline-theme-dark-gray' : ''),
                                (current_playback_state === playback_states[2] ? 'bg-theme-black' : ''),
                                (current_playback_state === playback_states[3] ? 'bg-theme-black' : ''),
                                (current_playback_state === playback_states[4] ? 'bg-theme-black' : ''),
                                'left-0 right-0 mx-auto w-0.5 h-full'
                            ]"
                        ></div>
                    </div>
                </div>
                <!--slider-->
                <div class="left-2 right-2 m-auto h-10 absolute bottom-0">
                    <div
                        ref="playback_slider"
                        :class="[
                            final_file !== null ? 'touch-none' : '',
                            'h-full relative'
                        ]"
                        @mouseenter.stop="is_playback_slider_hover = true"
                        @mouseleave.stop="is_playback_slider_hover = false"
                        @mousedown.stop="[startPlaybackDrag(), doPlaybackDrag($event)]"
                        @touchstart.stop="[startPlaybackDrag(true), doPlaybackDrag($event)]"
                    >
                        <!--for reference, since playback_slider_progress cannot give full width at start-->
                        <div
                            ref="playback_slider_width"
                            class="h-0 absolute opacity-0 left-0 right-0 top-0 bottom-0 m-auto"
                        ></div>
                        <div
                            :class="[
                                is_playback_slider_hover && final_file !== null ? 'double-height-when-hover' : 'scale-y-100',
                                'h-1 absolute bg-theme-medium-gray/50 left-0 right-0 top-5 bottom-0 m-auto transition-transform duration-150 ease-in-out'
                            ]"
                        ></div>
                        <div
                            ref="playback_slider_progress"
                            class="h-1 absolute bg-theme-lead left-0 right-0 top-5 bottom-0 m-auto scale-x-0 origin-left"
                        ></div>
                        <div
                            ref="playback_slider_knob"
                            class="w-4 h-4 absolute rounded-full bg-theme-black top-5 bottom-0 -left-2 m-auto"
                        ></div>
                    </div>
                </div>
            </div>

            <!--volume, play/pause, rate, timers-->
            <div
                :class="[
                    final_file === null ? 'opacity-10' : 'opacity-100',
                    'mx-2 h-10 grid grid-rows-1 grid-cols-5'
                ]"
            >
                <!--current duration-->
                <div class="row-start-1 row-span-1 col-start-1 col-span-1 relative text-base font-medium">
                    <span class="absolute w-10 h-fit left-0 top-0 bottom-0 m-auto">{{pretty_current_playback_time}}</span>
                </div>
                <!--volume-->
                <div
                    v-if="propIsForRecording === false"
                    ref="playback_volume_opener"
                    class="row-start-1 row-span-1 col-start-2 col-span-1 h-full text-xl relative"
                >
                    <!--open/close volume-->
                    <button
                        @click="togglePlaybackVolumeOptions()"
                        class="w-full h-full shade-when-hover transition-colors duration-200 ease-in-out rounded-md"
                        :disabled="final_file === null"
                        type="button"
                    >
                        <i
                            :class="[
                                (playback_volume === 0 ? 'fa-volume-xmark' : ''),
                                (playback_volume <= 0.5 ? 'fa-volume-low' : ''),
                                (playback_volume <= 1 ? 'fa-volume-high' : ''),
                                (is_playback_volume_open ? '-rotate-90' : 'rotate-0'),
                                'fas transition-transform duration-200 ease-in-out'
                            ]"
                        ></i>
                    </button>
                    <!--volume menu-->
                    <TransitionFade>
                        <VBox
                            v-show="is_playback_volume_open"
                            :propIsOpaque="true"
                            v-click-outside="{
                                var_name_for_element_bool_status: 'is_playback_volume_open',
                                refs_to_exclude: ['playback_volume_opener']
                            }"
                            class="w-full h-[300%] absolute left-0 right-0 bottom-[110%] m-auto"
                        >
                            <VSliderYSmall
                                ref="volume_slider"
                                @hasNewSliderValue="changePlaybackVolume($event)"
                                class="w-full h-full"
                            />
                        </VBox>
                    </TransitionFade>
                </div>
                <!--play/pause-->
                <div class="row-start-1 row-span-1 col-start-3 col-span-1 h-full text-3xl">
                    <button
                        ref="play_pause_button"
                        @click="togglePlaybackPlayPause()"
                        class="w-full h-full shade-when-hover transition-colors duration-200 ease-in-out rounded-md"
                        :disabled="final_file === null"
                        type="button"
                    >
                        <i
                            :class="[
                                is_playing? 'fa-pause' : 'fa-play',
                                'fas'
                            ]"
                        ></i>
                    </button>
                </div>
                <!--rate-->
                <div
                    v-if="propIsForRecording === false"
                    ref="playback_speed_options_opener"
                    class="row-start-1 row-span-1 col-start-4 col-span-1 h-full text-xl relative"
                >
                    <!--open/close rate-->
                    <button
                        @click="togglePlaybackSpeedOptions()"
                        class="w-full h-full shade-when-hover transition-colors duration-200 ease-in-out rounded-md"
                        :disabled="final_file === null"
                        type="button"
                    >
                        <i
                            :class="[
                                is_playback_speed_options_open ? '-rotate-90' : 'rotate-0',
                                'fas fa-forward transition-transform duration-200 ease-in-out'
                            ]"
                        ></i>
                    </button>
                    <!--rate menu-->
                    <TransitionFade>
                        <VBox
                            v-show="is_playback_speed_options_open"
                            :propIsOpaque="true"
                            v-click-outside="{
                                var_name_for_element_bool_status: 'is_playback_speed_options_open',
                                refs_to_exclude: ['playback_speed_options_opener']
                            }"
                            class="w-full h-[300%] absolute left-0 right-0 bottom-[110%] m-auto"
                        >
                            <div
                                class="
                                    w-full h-full text-center text-theme-black p-1
                                    grid grid-rows-3 divide-y divide-theme-black/5
                                "
                            >
                                <div class="row-span-1">
                                    <button
                                        @click="changePlaybackRate(1.5)"
                                        :class="[
                                            playback_rate === 1.5 ? 'bg-theme-lead' : 'bg-none shade-when-hover',
                                            'w-full h-full transition-colors duration-200 ease-in-out p-1 rounded-sm'
                                        ]"
                                        type="button"
                                    >
                                        1.5
                                    </button>
                                </div>
                                <div class="row-span-1">
                                    <button
                                        @click="changePlaybackRate(1)"
                                        :class="[
                                            playback_rate === 1 ? 'bg-theme-lead' : 'bg-none shade-when-hover',
                                            'w-full h-full transition-colors duration-200 ease-in-out p-1 rounded-sm'
                                        ]"
                                        type="button"
                                    >
                                        1
                                    </button>
                                </div>
                                <div class="row-span-1">
                                    <button
                                        @click="changePlaybackRate(0.5)"
                                        :class="[
                                            playback_rate === 0.5 ? 'bg-theme-lead' : 'bg-none shade-when-hover',
                                            'w-full h-full transition-colors duration-200 ease-in-out p-1 rounded-sm'
                                        ]"
                                        type="button"
                                    >
                                        0.5
                                    </button>
                                </div>
                            </div>
                        </VBox>
                    </TransitionFade>
                </div>
                <!--total duration-->
                <div class="row-start-1 row-span-1 col-start-5 col-span-1 relative text-base font-medium">
                    <span class="absolute w-fit h-fit right-0 top-0 bottom-0 m-auto">{{pretty_playback_duration}}</span>
                </div>
            </div>
        </div>
    </div>
</template>


<script setup lang="ts">
    import VBox from '/src/components/small/VBox.vue';
    import VSliderYSmall from '/src/components/small/VSliderYSmall.vue';
    import TransitionFade from '/src/transitions/TransitionFade.vue';

</script>


<script lang="ts">
    import { DefineComponent, defineComponent } from 'vue';
    import anime from 'animejs';

    export default defineComponent({
        data(){
            return {
                final_file: null as File | null,
                final_file_duration: 0, //float seconds
                pretty_current_playback_time: '00:00',
                pretty_playback_duration: '00:00',
                is_playing: false,
                is_buffering: false,    //for 'waiting' and 'can_play'
                is_volume_ripples_available: false,
                main_anime: null as InstanceType<typeof anime> | null,   //to store animePlaybackStates() anime
                
                playback_slider_value: 0,
                is_playback_slider_drag: false,
                is_playback_slider_touch: false,
                is_playback_slider_hover: false,
                playback_slider_width: null as DOMRect | null,
                playback_slider_knob_anime: null as InstanceType<typeof anime> | null, //we play/pause instead of new anime() for best results
                playback_slider_progress_anime: null as InstanceType<typeof anime> | null, //we play/pause instead of new anime() for best results
                resume_after_stop_dragging: null as boolean | null,    //to know whether to resume after done navigating
                resume_after_stop_skipping: null as boolean | null,   //to know whether to resume after done navigating

                playback_rate: 1,   //allows 0 to 2, but we handle 0.5, 1, 1.5
                playback_volume: 0, //accepts 0 to 1
                is_repeat: false,

                is_playback_options_open: false,
                is_playback_speed_options_open: false,
                is_playback_volume_open: false,

                playback_states: ['empty', 'recording', 'attaching', 'can_play', 'loading'],
                current_playback_state: null as string | null,
                bucket_quantity: 20,
                file_volumes: [] as number[],

                fastest_anime_duration_ms: 100, //to change anime durations easily
            };
        },
        mounted(){

            //handle rate and volume differently
            if(this.propIsForRecording === true){

                //we set rate to 1 and volume to max, and hide them
                //there is no need for them if intended for recording, for best feedback
                this.playback_volume = 1;
                (this.$refs.audio_playback as HTMLAudioElement).playbackRate = this.playback_rate;
                (this.$refs.audio_playback as HTMLAudioElement).volume = this.playback_volume;

            }else{

                //set rate to saved value
                if(window.localStorage.playback_rate !== undefined){

                    this.playback_rate = parseFloat(window.localStorage.playback_rate);
                }

                //set volume to saved value
                if(window.localStorage.playback_volume !== undefined){

                    this.playback_volume = parseFloat(window.localStorage.playback_volume);
                }
            }

            //set initial value for volume slider
            (this.$refs.volume_slider as DefineComponent).mainUpdateSlider(this.playback_volume);


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
            window.addEventListener('keydown', (event) => {
                this.handleKeyboardEvent(event);
            });
            window.addEventListener('keyup', (event) => {
                this.handleKeyboardEvent(event);
            });
            document.addEventListener('visibilitychange', this.syncSliderAnimeAfterSuspend);
        },
        beforeUnmount(){

            //remove listeners
            window.removeEventListener('mousemove', this.doPlaybackDrag);
            window.removeEventListener('touchmove', this.doPlaybackDrag);
            window.removeEventListener('mouseup', this.stopPlaybackDrag);
            window.removeEventListener('touchend', this.stopPlaybackDrag);
            window.removeEventListener('resize', this.adjustToNewPlaybackDimension);
            window.addEventListener('keydown', (event) => {
                this.handleKeyboardEvent(event);
            });
            window.removeEventListener('keyup', (event) => {
                this.handleKeyboardEvent(event);
            });
            document.removeEventListener('visibilitychange', this.syncSliderAnimeAfterSuspend);
        },
        emits: [
            'isAnimePlaybackCompleted',
        ],
        props: {
            propIsSticky: {
                type: Boolean,
                default: false,
            },
            propFile: Object,
            propIsRecording: Boolean,
            propRecordingVolume: Number,    //0-1
            propTimeInterval: Number,  //based on VRecorder time_interval, needed for analyser during recording
            propIsForRecording: {
                type: Boolean,
                default: false
            },
        },
        watch: {
            async propFile(new_value){

                this.final_file = new_value;

                if(new_value === null){

                    return false;
                }

                const audio_context = new AudioContext();

                await new_value.arrayBuffer()
                    .then((buffer:ArrayBuffer) => audio_context.decodeAudioData(buffer))
                    .then((decoded_audio:AudioBuffer) => decoded_audio.getChannelData(0)) //only 1 channel as expected
                    .then((audio_data:Float32Array) => this.getVolumes(audio_data))
                    .then(() => {
                        this.attachRecordedAudioToPlayback();
                        this.current_playback_state = this.playback_states[2];
                    })
                    .catch((error:any|Error) => {
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

                if(this.is_playing === true){

                    this.pausePlayback();
                }

                this.final_file = null;
                this.final_file_duration = 0;
                this.is_volume_ripples_available = false;
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

                    this.main_anime.finished.then(()=>{

                        this.emitIsAnimePlaybackCompleted(true);
                    });
                }
            },
        },
        methods: {
            handleKeyboardEvent(event:KeyboardEvent) : void {

                //one function, for both keydown and keyup
                //some keyup events are too late for .preventDefault(), so they use keydown

                //these keys affect only playback, so no point if there's no file
                if(this.final_file === null){

                    return;
                }

                //don't let this function affect text input
                if(
                    event.target !== document.body &&
                    !(this.$refs.playback_main as HTMLElement).contains(event.target as Node)
                ){

                    return;
                }

                //keyCode is deprecated, use .key
                    //.code is different on different types of keyboards, but .key will be consistent
                //https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/key
                switch(event.key){

                    case 'ArrowLeft':

                        if(event.type !== 'keydown'){

                            break;
                        }

                        //go backwards playback
                        this.skipPlayback(-5);
                        break;

                    case 'ArrowRight':

                        if(event.type !== 'keydown'){

                            break;
                        }

                        //go forward playback
                        this.skipPlayback(5);
                        break;

                    case ' ':

                        if(event.type !== 'keyup'){

                            break;
                        }

                        //play/pause
                        this.togglePlaybackPlayPause();
                        break;

                    case 'm':

                        //mute/unmute
                        //when for recording, no volume option
                        //we use localStorage for backup value from mute to unmute
                        {
                            if(event.type !== 'keyup' || this.propIsForRecording === true){

                                break;
                            }

                            let audio_element = (this.$refs.audio_playback as HTMLAudioElement);
                            const stored_volume = parseFloat(window.localStorage.playback_volume);

                            if(this.playback_volume === stored_volume){

                                //mute
                                this.playback_volume = 0;
                                audio_element.volume = 0;

                            }else{

                                //unmute
                                this.playback_volume = stored_volume;
                                audio_element.volume = stored_volume;
                            }
                            (this.$refs.volume_slider as DefineComponent).mainUpdateSlider(this.playback_volume);
                        }
                        break;

                    case 'ArrowUp':

                        //increase volume if volume_slider is open
                        {
                            if(
                                event.type !=='keydown' ||
                                this.is_playback_volume_open === false
                            ){

                                break;
                            }

                            event.preventDefault();
                            let new_playback_volume = this.playback_volume + 0.2;
                            new_playback_volume = parseFloat(new_playback_volume.toFixed(2));
                            
                            if(new_playback_volume > 1){

                                this.changePlaybackVolume(1);

                            }else{

                                this.changePlaybackVolume(new_playback_volume);
                            }
                        
                            //update volume_slider
                            (this.$refs.volume_slider as DefineComponent).mainUpdateSlider(this.playback_volume);
                            break;
                        }

                        case 'ArrowDown':

                            //decrease volume if volume_slider is open
                            {
                                if(
                                    event.type !== 'keydown' ||
                                    this.is_playback_volume_open === false
                                ){

                                    break;
                                }

                                event.preventDefault();
                                let new_playback_volume = this.playback_volume - 0.2;
                                new_playback_volume = parseFloat(new_playback_volume.toFixed(2));
                                
                                if(new_playback_volume <= 0){

                                    this.changePlaybackVolume(0);

                                }else{

                                    this.changePlaybackVolume(new_playback_volume);
                                }

                                //update volume_slider
                                (this.$refs.volume_slider as DefineComponent).mainUpdateSlider(this.playback_volume);
                                break;
                            }

                    default:

                        break;
                }
            },
            syncSliderAnimeAfterSuspend() : void {

                //we need this because anime.suspendDocumentWhenHidden=false does not work
                //basically just to reposition slider anime to playback, else it doesn't do that
                //must call pause() first, else seek() is inaccurate
                if(
                    document.visibilityState === 'visible' &&
                    this.playback_slider_knob_anime !== null && this.playback_slider_progress_anime !== null
                ){

                    let resume_later = null;

                    if(this.is_playing === true){

                        //reminder that pausePlayback() also updates this.playback_slider_value
                        this.pausePlayback();
                        resume_later = true;
                    }

                    this.playback_slider_knob_anime.seek(this.playback_slider_value * this.playback_slider_knob_anime.duration);
                    this.playback_slider_progress_anime.seek(this.playback_slider_value * this.playback_slider_progress_anime.duration);

                    if(resume_later === true){

                        const target = (this.$refs.audio_playback as HTMLAudioElement);

                        //we want to mute to avoid the rare slight spike at certain db
                        target.muted = true;
                        this.playPlayback();
                        target.muted = false;
                    }
                }
            },
            createPlaybackSliderAnime() : void {

                //to be called during getPlaybackDuration(), window resize, changePlaybackRate()
                //we can then use .play/.pause/.seek
                //expects to already have accurate this.playback_slider_value

                //remove
                anime.remove([
                    this.$refs.playback_slider_knob,
                    this.$refs.playback_slider_progress
                ]);
                this.playback_slider_knob_anime = null;
                this.playback_slider_progress_anime =null;

                //calculate starting point of translateX
                const ending_translateX = (this.playback_slider_width as DOMRect).width;

                //calculate duration based on playback_rate
                const anime_duration = this.getRealDurationAfterPlaybackRate() * 1000;

                //create new anime
                this.playback_slider_knob_anime = anime({
                    targets: this.$refs.playback_slider_knob,
                    easing: 'linear',
                    autoplay: false,
                    loop: false,
                    duration: anime_duration,
                    translateX: [
                        '0px',
                        ending_translateX.toString() + 'px'
                    ],
                });
                this.playback_slider_progress_anime = anime({
                    targets: this.$refs.playback_slider_progress,
                    easing: 'linear',
                    autoplay: false,
                    loop: false,
                    duration: anime_duration,
                    scaleX: ['0', '1'],
                });
            },
            adjustToNewPlaybackDimension() : void {

                if((this.$refs.playback_main as HTMLElement).style.display === 'none'){

                    return;
                }

                //expects playback_slider to have the same width
                //use not only during 'resize' event, but when playback_states[2] is ready
                //as 'resize' may occur when element is display:none
                this.playback_slider_width = (this.$refs.playback_slider_width as HTMLElement).getBoundingClientRect();

                //create/recreate anime
                if(this.final_file !== null){

                    this.createPlaybackSliderAnime();
                    this.syncSliderAnimeAfterSuspend();
                }
            },
            endPlaybackProperly() : void {

                //when paused and dragged to end, html media seems to still want you to play once to truly end
                //handle only the media here, the rest are already settled
                const target = (this.$refs.audio_playback as HTMLAudioElement);
                target.muted = true;
                target.play();
            },
            startPlaybackDrag(is_playback_slider_touch=false) : void {

                if(this.final_file === null || this.is_volume_ripples_available === false){

                    return;
                }

                this.is_playback_slider_drag = true;
                this.is_playback_slider_touch = is_playback_slider_touch;

                if(this.is_playing === true){

                    this.pausePlayback();
                    this.resume_after_stop_dragging = true;
                }

                //we want to also resume if started from end
                if(this.playback_slider_value === 1){

                    this.resume_after_stop_dragging = true;
                }
            },
            doPlaybackDrag(event:MouseEvent|TouchEvent) : void {

                if(this.is_playback_slider_drag === true && this.playback_slider_width !== null){

                    //for mouse, we need these to avoid text highlighting, accidental permanent drag state, etc.
                    //for touch, we need these to avoid mouse firing
                    //best solution now is to let it raise Intervention on console when .cancelable is true on passive events
                    if(event !== null && event.cancelable === true){
                        
                        event.preventDefault();
                    }

                    //can use clientX, screenX, pageX, but pageX is most accurate in this context
                    let user_x = undefined;

                    if(this.is_playback_slider_touch === true){

                        user_x = (event as TouchEvent).touches[0].clientX;

                    }else{

                        user_x = (event as MouseEvent).clientX;
                    }

                    if(user_x >= this.playback_slider_width.left && user_x <= this.playback_slider_width.right){

                        this.playback_slider_value = (user_x - this.playback_slider_width.left) / this.playback_slider_width.width;

                    }else if(user_x < this.playback_slider_width.left){

                        this.playback_slider_value = 0;

                    }else if(user_x > this.playback_slider_width.right){

                        this.playback_slider_value = 1;
                    }

                    this.handlePlaybackDrag();

                    //troubleshoot if needed
                    // console.log("==========================");
                    // console.log('user_x: '+user_x);
                    // console.log('slider_top: '+playback_slider_width.top);
                    // console.log('slider_bottom: '+playback_slider_width.bottom);
                    // console.log(this.playback_slider_value);
                    // console.log("==========================");
                }
            },
            stopPlaybackDrag() : void {

                if(this.is_playback_slider_drag === true){

                    //we reset touch detection on every startPlaybackDrag() and stopPlaybackDrag()
                    //so we get latest status of is_playback_slider_touch
                    //some browsers also trigger both touch + mouse events together
                    this.is_playback_slider_touch = false;

                    if(this.playback_slider_value < 1 && this.resume_after_stop_dragging === true){

                        this.playPlayback();

                    }else if(this.playback_slider_value === 1){

                        this.endPlaybackProperly();
                    }

                    this.resume_after_stop_dragging = null;
                    this.is_playback_slider_drag = false;
                }

            },
            handlePlaybackDrag() : void {

                //expects playback_slider_value to be float 0 to 1

                //duration is the same regardless of playbackRate
                const jumped_anime_duration = this.playback_slider_value * this.playback_slider_knob_anime.duration;
                //duration changes when playbackRate changes
                const jumped_playback_duration = this.playback_slider_value * this.final_file_duration;

                //handle slider aesthetics
                //need to set .completed to false, else .play() starts from 0 if it has finished before
                //must be in ms
                this.playback_slider_knob_anime.completed = false;
                this.playback_slider_progress_anime.completed = false;
                this.playback_slider_knob_anime.seek(jumped_anime_duration);
                this.playback_slider_progress_anime.seek(jumped_anime_duration);

                //handle <audio>
                (this.$refs.audio_playback as HTMLAudioElement).currentTime = jumped_playback_duration;

                //handle timer
                this.updateCurrentPlaybackTime();
            },
            skipPlayback(seconds=0) : void {

                //+x for forward, -x for backward

                //do this instead of relying on :disabled, as :disabled makes sliders bug out
                if(seconds === 0 || this.final_file === null){

                    return;
                }

                if(this.is_playing === true){

                    this.pausePlayback();
                    this.resume_after_stop_skipping = true;
                }

                const target = (this.$refs.audio_playback as HTMLAudioElement);
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
            resetRecordingVisualiser() : void {

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
            animeRecordingVisualiser(new_value:number) : void {

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
            updateCurrentPlaybackTime() : void {

                const target = (this.$refs.audio_playback as HTMLAudioElement);

                //timer
                this.pretty_current_playback_time = new Date(
                    target.currentTime * 1000
                ).toISOString().substring(14, 19);
            },
            getRealDurationAfterPlaybackRate() : number{

                //note that when <audio> playbackRate changes, .duration is still the same
                return this.final_file_duration / this.playback_rate;
            },
            changePlaybackRate(new_value:number) : void {

                if(new_value === this.playback_rate){

                    return;
                }

                //note that on every new file loaded into <audio>, playbackRate is reset
                //attachRecordedAudioToPlayback() will handle this inconvenience
                (this.$refs.audio_playback as HTMLAudioElement).playbackRate = new_value;
                this.playback_rate = new_value;
                window.localStorage.playback_rate = new_value;

                if((this.$refs.audio_playback as HTMLAudioElement).src !== ''){

                    //adjust anime
                    const resume_later = this.is_playing;
                    this.pausePlayback();
                    this.createPlaybackSliderAnime();
                    this.playback_slider_knob_anime.seek(this.playback_slider_value * this.playback_slider_knob_anime.duration);
                    this.playback_slider_progress_anime.seek(this.playback_slider_value * this.playback_slider_progress_anime.duration);
                    if(resume_later === true){

                        this.playPlayback();
                    }
                }
            },
            changePlaybackVolume(new_value:number) : void {
                
                (this.$refs.audio_playback as HTMLAudioElement).volume = new_value;
                this.playback_volume = new_value;
                window.localStorage.playback_volume = new_value;
            },
            togglePlaybackSpeedOptions() : void {
                
                this.is_playback_speed_options_open = !this.is_playback_speed_options_open;
            },
            togglePlaybackVolumeOptions() : void {

                //note that slider malfunctions over :disabled elements, i.e. backward/forward, etc.

                this.is_playback_volume_open = !this.is_playback_volume_open;
            },
            playPlayback() : void {

                //using play/pause instead of remove+create prevents slight off-position on second play
                //our new anime position is already settled by handlePlaybackDrag()

                const target = (this.$refs.audio_playback as HTMLAudioElement);

                //although redundant, we put target.muted=false here to guarantee it
                //as there has been a rare instance where playback had no audio unintentionally until the next replay
                target.muted = false;
                target.play();
                this.playback_slider_knob_anime.play();
                this.playback_slider_progress_anime.play();
                this.is_playing = true;
            },
            pausePlayback() : void {
                
                //if playing, call this before drag, then do playPlayback() once done
                //done at startPlaybackDrag() and stopPlaybackDrag()

                const target = (this.$refs.audio_playback as HTMLAudioElement);

                //also recalculate slider value
                target.pause();
                this.playback_slider_knob_anime.pause();
                this.playback_slider_progress_anime.pause();
                this.playback_slider_value = target.currentTime / this.final_file_duration;
                this.is_playing = false;
            },
            togglePlaybackPlayPause() : void {

                //we let everything stay at the end if playback truly ended
                //reset is only triggered on next play

                //do this instead of relying on :disabled, as :disabled makes sliders bug out
                if(this.final_file === null){

                    return;
                }

                //check if playback is not playing
                if(this.is_playing === false){

                    this.playPlayback();

                }else{

                    this.pausePlayback();
                    
                    //when we pause right at the end, our anime may finish earlier than playback
                    //we end the actual playback in this case
                    if(
                        this.playback_slider_knob_anime.completed === true ||
                        this.playback_slider_progress_anime.completed === true
                    ){
                        
                        this.endPlaybackProperly();
                    }
                }
            },
            emitIsAnimePlaybackCompleted(is_completed:boolean) : void {

                this.$emit('isAnimePlaybackCompleted', is_completed);
            },
            animePlaybackStates() : void {

                const volume_ripples = (this.$refs.volume_ripple as HTMLElement[]);
                const recording_visualiser = (this.$refs.recording_visualiser as HTMLElement);
                const playback_main = (this.$refs.playback_main as HTMLElement);

                //reset all elements
                //reset all translates to 0

                switch(this.current_playback_state){

                    case this.playback_states[0]:

                        {
                            //'empty', a.k.a. initial state
                            //this is also used for hard reset

                            //remove related anime
                            anime.remove([
                                volume_ripples,
                                recording_visualiser,
                            ]);

                            //timeline will not work here
                            this.main_anime = anime({
                                begin: ()=>{
                                    //remove sunset
                                    recording_visualiser.style.opacity = '0';
                                    recording_visualiser.style.display = 'none';
                                    this.resetRecordingVisualiser();
                                },
                                targets: volume_ripples,
                                scaleY: ['0', '0.9'],
                                autoplay: true,
                                loop: false,
                                easing: 'easeInOutCubic',
                                duration: 200,
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

                    case this.playback_states[1]:

                        {
                            //'recording'

                            //remove related anime
                            anime.remove([
                                volume_ripples,
                                recording_visualiser,
                                this.$refs.playback_slider_knob,
                                playback_main,
                                this.$refs.recording_visualiser_circle_0,
                                this.$refs.recording_visualiser_circle_1,
                                this.$refs.recording_visualiser_circle_2,
                            ]);

                            this.main_anime = anime.timeline({
                                easing: 'linear',
                                loop: false,
                                autoplay: true,
                            }).add({
                                //remove volume_ripples
                                targets: volume_ripples,
                                scaleY: ['0'],
                                translateY: ['0%'],
                                duration: this.fastest_anime_duration_ms,
                            }).add({
                                //remove playback_main
                                targets: playback_main,
                                opacity: 0,
                                duration: this.fastest_anime_duration_ms,
                                complete: ()=>{
                                    playback_main.style.display = 'none';
                                    this.playback_slider_knob_anime = null;
                                    this.playback_slider_progress_anime = null;
                                },
                            }).add({
                                //make sunset available
                                begin: ()=>{
                                    recording_visualiser.style.display = 'block';
                                },
                                targets: recording_visualiser,
                                opacity: 1,
                                duration: this.fastest_anime_duration_ms,
                            });
                        }
                        break;

                    case this.playback_states[2]:

                        {
                            //'attaching'
                            //run once only

                            //remove related anime
                            anime.remove([
                                volume_ripples,
                                recording_visualiser,
                                playback_main,
                                this.$refs.recording_visualiser_circle_0,
                                this.$refs.recording_visualiser_circle_1,
                                this.$refs.recording_visualiser_circle_2,
                            ]);

                            this.main_anime = anime.timeline({
                                easing: 'linear',
                                loop: false,
                                autoplay: true,
                            }).add({
                                //remove sunset
                                begin: ()=>{
                                    this.resetRecordingVisualiser();
                                },
                                targets: recording_visualiser,
                                opacity: 0,
                                delay: 100,
                                duration: this.fastest_anime_duration_ms,
                                complete: ()=>{
                                    recording_visualiser.style.display = 'none';
                                },
                            }).add({
                                //make playback_main available
                                targets: playback_main,
                                begin: ()=>{
                                    playback_main.style.display = 'block';
                                },
                                opacity: 1,
                                duration: this.fastest_anime_duration_ms * 2,
                                //we want the entire anime to finish before this condition unlocks other actions
                                //to delay this, we don't use setTimeout
                                //we multiply duration above instead, so that we can still fully rely on anime's .finished.then()
                                complete: ()=>{
                                    //set volume_ripples
                                    this.adjustVolumeRipples();
                                }
                            });
                        }
                        break;

                    case this.playback_states[3]:

                        {
                            //'can_play'
                            //will trigger after 'loading', so this is basically to undo 'loading' state
                            //they fire on file load and on every start-from-beginning play

                            //we resume slider anime after buffering while playing
                            //we put is_buffering outside since 'can_play' always means no longer buffering
                            if(
                                this.is_playing === true && this.is_buffering === true
                            ){

                                this.playback_slider_progress_anime.play();
                                this.playback_slider_knob_anime.play();
                            }
                            this.is_buffering = false;

                            //remove related anime
                            anime.remove([
                                volume_ripples,
                            ]);

                            this.main_anime = anime({
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

                        {
                            //'loading'

                            //we pause slider anime when buffering while playing
                            if(this.is_playing === true){

                                this.is_buffering = true;
                                this.playback_slider_progress_anime.pause();
                                this.playback_slider_knob_anime.pause();
                            }

                            //remove related anime
                            anime.remove([
                                volume_ripples,
                            ]);

                            //create fast ripple effect for volume_ripples to show that it is loading
                            this.main_anime = anime({
                                targets: volume_ripples,
                                translateY: ['0%', '-5%', '5%', '0%'],
                                autoplay: true,
                                loop: true,
                                easing: 'linear',
                                delay: anime.stagger(20),
                            });
                        }
                        break;

                    default:
                        
                        console.log('State is currently null or not one of the declared playback_states.');
                        return;
                }
            },
            getVolumes(audio_data:Float32Array) : void {

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
            adjustVolumeRipples() : void {

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
                        targets: (this.$refs.volume_ripple as HTMLElement[])[x],
                        scaleY: scaleY_percentage.toString(),
                        autoplay: true,
                        loop: false,
                        easing: 'easeInOutQuad',
                        duration: 200,
                    });

                    this.is_volume_ripples_available = true;
                }
            },
            attachRecordedAudioToPlayback() : boolean {

                if(this.final_file === null){

                    return false;
                }

                const audio_playback = (this.$refs.audio_playback as HTMLAudioElement);

                //attach file into <audio>
                audio_playback.src = URL.createObjectURL(this.final_file);

                //free the memory
                audio_playback.onload = function(){
                    return URL.revokeObjectURL(audio_playback.src);
                };

                //no updating current_playback_state here, we rely on <audio> for that

                //on every new file loaded into <audio>, playbackRate is reset by default
                //this is the fix
                audio_playback.playbackRate = this.playback_rate;

                return true;
            },
            getPlaybackDuration() : void {

                const audio_playback = (this.$refs.audio_playback as HTMLAudioElement);

                //there's a bug that gives us 'Infinity'
                //this is how we fix it
                //https://stackoverflow.com/a/69512775
                if((audio_playback.duration as number|string) == 'Infinity'){

                    const handler = ()=>{

                        audio_playback.currentTime = 0;
                        audio_playback.removeEventListener('timeupdate', handler);
                        this.final_file_duration = audio_playback.duration;

                        //create anime
                        this.playback_slider_value = 0;
                        this.createPlaybackSliderAnime();

                        //mm:ss
                        //only for duration display we will use floor
                        this.pretty_playback_duration = 
                            new Date(Math.floor(this.final_file_duration) * 1000).toISOString().substring(14, 19);
                    };

                    audio_playback.currentTime = 1e101;
                    audio_playback.addEventListener('timeupdate', handler);

                }else{

                    this.final_file_duration = audio_playback.duration;

                    //create anime
                    this.playback_slider_value = 0;
                    this.createPlaybackSliderAnime();
                }

                //don't try to access this.final_file_duration precisely here, as something is async
                //you'll get 0, but if you check via watch, the value does change
                //put your code in handler instead if you need to run something else
            },
        }
    });
</script>