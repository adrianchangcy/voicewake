<template>
    <div>
        <!--add @timeupdate at mounted(), not here, as beforeUnmount() cannot remove it, and it'll still fire after unmount-->
        <audio
            ref="audio_element"
            @loadedmetadata="handleHasMetadata()"
            @canplay="is_loading=false"
            @waiting="is_loading=true"
            @ended="pausePlayback(), was_paused=true"
        ></audio>

        <!--size priority: playback_main, then ripples, then everything else-->
        <!--if you want to modify aesthetics, consider doing it at playback_main and not this parent div-->
        <div class="h-20 text-center relative">

            <!--recording visualiser-->
            <!--need inline CSS to prevent jolting from anime if without it-->
            <div
                ref="recording_visualiser"
                class="absolute w-20 h-20 left-0 right-0 top-0 bottom-0 m-auto"
            >
                <div class="relative w-full h-full">
                    <div
                        ref="recording_visualiser_circle_0"
                        class="absolute w-full h-full left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-lead/60"
                        style="transform: scaleX(0) scaleY(0);"
                    ></div>
                    <div
                        ref="recording_visualiser_circle_1"
                        class="absolute w-full h-full left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-lead/40"
                        style="transform: scaleX(0) scaleY(0);"
                    ></div>
                    <div
                        ref="recording_visualiser_circle_2"
                        class="absolute w-full h-full left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-lead/20"
                        style="transform: scaleX(0) scaleY(0);"
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
                    propEventTone === null ? 'grid-cols-3 pr-4' : 'grid-cols-4',
                    propHasHighlight === true ? 'border-2' : 'border',
                    'w-full h-full absolute grid grid-rows-2 left-0 right-0 top-0 bottom-0 m-auto text-theme-black rounded-lg border-theme-light-gray opacity-0'
                ]"
            >
                <!--play/pause-->
                <div class="row-start-1 row-span-2 col-start-1 col-span-1 text-4xl relative">
                    <button
                        ref="play_pause_button"
                        @click="togglePlaybackPlayPause()"
                        class="absolute left-2 right-2 top-2 bottom-2 shade-text-when-hover transition-colors duration-200 ease-in-out rounded-md"
                        :disabled="has_all_data_for_play === false"
                        type="button"
                    >
                        <i
                            :class="[
                                is_playing? 'fa-pause' : 'fa-play',
                                'fas mb-0.5'
                            ]"
                        ></i>
                        <span v-if="is_playing" class="sr-only">
                            pause
                        </span>
                        <span v-else class="sr-only">
                            play
                        </span>
                    </button>
                </div>
                <!--ripples, slider, do left-2 right-2 m-auto if you want outermost knob to be within bounds-->
                <div
                    :class="[
                        (has_all_data_for_play === true && is_playback_slider_ready === true ? 'cursor-pointer' : 'cursor-default'),
                        'row-start-1 row-span-1 col-start-2 col-span-2 relative'
                    ]"
                >
                    <!--ripples-->
                    <!--need inline CSS to prevent jolting from anime if without it-->
                    <div
                        ref="volume_ripples_container"
                        class="w-full h-4 absolute top-2 flex flex-row justify-evenly"
                    >
                        <div
                            v-for="volume_ripple in propBucketQuantity" :key="volume_ripple"
                            ref="volume_ripple"
                            class="h-full origin-bottom"
                            style="transform: scaleY(0);"
                        >
                            <div
                                :class="[
                                    has_all_data_for_play === true ? 'bg-theme-black' : 'outline-1 outline outline-theme-dark-gray',
                                    'left-0 right-0 mx-auto w-0.5 h-full'
                                ]"
                            ></div>
                        </div>
                    </div>
                    <!--slider-->
                    <div
                        class="w-full h-full absolute bottom-0"
                    >
                        <div
                            ref="playback_slider"
                            :class="[
                                has_all_data_for_play === true && is_playback_slider_ready === true ? 'touch-none' : '',
                                'h-full relative'
                            ]"
                            @mouseenter.stop="is_playback_slider_hover = true"
                            @mouseleave.stop="is_playback_slider_hover = false"
                            @mousedown.stop="[startPlaybackDrag(), doPlaybackDrag($event)]"
                            @touchstart.stop="[startPlaybackDrag(true), doPlaybackDrag($event)]"
                        >
                            <!--for reference, since playback_slider_progress cannot give full width at start-->
                            <div
                                ref="playback_slider_dimension"
                                class="h-0 absolute opacity-0 left-0 right-0 top-0 bottom-0 m-auto"
                            ></div>
                            <div
                                :class="[
                                    is_playback_slider_hover && has_all_data_for_play === true ? 'double-height-when-hover' : 'scale-y-100',
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
                            >
                                <div
                                    ref="spinner_container"
                                    class="w-full h-full relative opacity-0"
                                >
                                    <i
                                        ref="spinner"
                                        class="fas fa-spinner text-2xl absolute w-fit h-fit -left-1 top-0 bottom-0 my-auto"
                                    ></i>
                                </div>
                            </div>
                        </div>
                    </div>
                    <span class="sr-only">playback navigation</span>
                </div>

                <!--volume, timers-->
                <div
                    class="row-start-2 row-span-1 col-start-2 col-span-2 grid grid-rows-1 grid-cols-3"
                >
                    <!--current duration-->
                    <div class="row-start-1 row-span-1 col-start-1 col-span-1 relative text-sm font-medium">
                        <span class="sr-only">current duration</span>
                        <span class="absolute w-fit h-fit left-0 top-0 bottom-0 m-auto">{{pretty_current_playback_time}}</span>
                    </div>
                    <!--volume-->
                    <div
                        ref="playback_volume_opener"
                        class="row-start-1 row-span-1 col-start-2 col-span-1 h-full text-lg relative"
                    >
                        <!--open/close volume-->
                        <button
                            v-if="propIsForRecording === false"
                            @click="togglePlaybackVolumeOptions()"
                            class="w-full h-full shade-text-when-hover transition-colors duration-200 ease-in-out rounded-md"
                            :disabled="has_all_data_for_play === false"
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
                            <span v-if="propIsForRecording" class="sr-only">
                                cannot open volume box, as volume is always at maximum when recording
                            </span>
                            <span v-else>
                                <span v-if="is_playback_volume_open" class="sr-only">
                                    close volume box
                                </span>
                                <span v-else class="sr-only">
                                    open volume box, of which you can use up down keystrokes to adjust
                                </span>
                            </span>
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
                                    :propInitialSliderValue="playback_volume"
                                    @hasNewSliderValue="changePlaybackVolume($event)"
                                    class="w-full h-full"
                                >
                                    <span class="sr-only">vertical volume box</span>
                                </VSliderYSmall>
                            </VBox>
                        </TransitionFade>
                    </div>
                    <!--total duration-->
                    <div class="row-start-1 row-span-1 col-start-3 col-span-1 relative text-sm font-medium">
                        <span class="absolute w-fit h-fit right-0 top-0 bottom-0 m-auto">
                            <span class="sr-only">total duration</span>
                            {{pretty_playback_duration}}
                        </span>
                    </div>
                </div>

                <div
                    v-if="propEventTone !== null"
                    class="row-span-2 col-span-1 relative"
                >
                    <span class="text-2xl pb-0.5 absolute w-fit h-fit left-0 right-0 top-0 bottom-0 m-auto">
                        {{ propEventTone.event_tone_symbol }}
                    </span>
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
    import { defineComponent, PropType } from 'vue';
    import { prettyDuration } from '@/helper_functions';
    import anime from 'animejs';
    import EventToneTypes from '@/types/EventTones.interface';

    export default defineComponent({
        data(){
            return {
                pretty_current_playback_time: '00:00',
                pretty_playback_duration: '00:00',
                is_playing: false,
                main_anime: null as InstanceType<typeof anime> | null,   //to store animePlaybackStates() anime

                is_loading: false,
                spinner_anime: null as InstanceType<typeof anime> | null,
                
                playback_slider_value: 0,
                is_playback_slider_ready: false,
                is_playback_slider_drag: false,
                is_playback_slider_touch: false,
                is_playback_slider_hover: false,
                playback_slider_dimension: null as DOMRect | null,
                playback_slider_knob_anime: null as InstanceType<typeof anime> | null, //we play/pause instead of new anime() for best results
                playback_slider_progress_anime: null as InstanceType<typeof anime> | null, //we play/pause instead of new anime() for best results
                was_paused: true,  //if user pauses, then navigating will not auto-play

                playback_rate: 1,   //allows 0 to 2, but we handle 0.5, 1, 1.5
                playback_volume: 0, //accepts 0 to 1
                is_repeat: false,

                is_playback_options_open: false,
                is_playback_speed_options_open: false,
                is_playback_volume_open: false,

                playback_states: ['initiate', 'recording', 'attaching', 'can_play', 'loading'],
                current_playback_state: null as string | null,

                fastest_anime_duration_ms: 100, //to change anime durations easily
            };
        },
        mounted(){

            //spinner
            this.spinner_anime = anime({
                targets: this.$refs.spinner,
                easing: 'linear',
                rotate: 360,
                loop: true,
                autoplay: false,
                duration: 800,
            });

            //when propAudioVolumePeaks.length > 0 on mounted(), means VPlayback was rendered via v-if with data already
            //we do this here because in this case, watchers do not trigger
            if(this.has_all_data_for_play === true){

                //start with data already available, i.e. for existing records
                this.attachAudioToPlayback(this.propAudioURL);

            }else{

                //start as 'initiate', a.k.a. empty, i.e. for recording
                this.current_playback_state = this.playback_states[0];
            }

            //handle rate and volume differently
            if(this.propIsForRecording === true){

                //we set rate to 1 and volume to max, and hide them
                //there is no need for them if intended for recording, for best feedback
                this.playback_rate = 1;
                this.playback_volume = 1;

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

            //set <audio> rate and volume
            (this.$refs.audio_element as HTMLAudioElement).playbackRate = this.playback_rate;
            (this.$refs.audio_element as HTMLAudioElement).volume = this.playback_volume;

            //attach listeners
            window.addEventListener('mousemove', this.doPlaybackDrag);
            window.addEventListener('touchmove', this.doPlaybackDrag);
            window.addEventListener('mouseup', this.stopPlaybackDrag);
            window.addEventListener('touchend', this.stopPlaybackDrag);
            window.addEventListener('resize', this.handleWindowResize);
            window.addEventListener('keydown', (event) => {
                this.handleKeyboardEvent(event);
            });
            window.addEventListener('keyup', (event) => {
                this.handleKeyboardEvent(event);
            });
            document.addEventListener('visibilitychange', this.syncSliderAnimeAfterSuspend);
            (this.$refs.audio_element as HTMLAudioElement).addEventListener('timeupdate', this.updateCurrentPlaybackTime);
        },
        beforeUnmount(){

            //remove listeners
            window.removeEventListener('mousemove', this.doPlaybackDrag);
            window.removeEventListener('touchmove', this.doPlaybackDrag);
            window.removeEventListener('mouseup', this.stopPlaybackDrag);
            window.removeEventListener('touchend', this.stopPlaybackDrag);
            window.removeEventListener('resize', this.handleWindowResize);
            window.removeEventListener('keydown', (event) => {
                this.handleKeyboardEvent(event);
            });
            window.removeEventListener('keyup', (event) => {
                this.handleKeyboardEvent(event);
            });
            document.removeEventListener('visibilitychange', this.syncSliderAnimeAfterSuspend);
            (this.$refs.audio_element as HTMLAudioElement).removeEventListener('timeupdate', this.updateCurrentPlaybackTime);
        },
        emits: [
            'isAnimePlaybackCompleted',
            'newFileVolumes'
        ],
        props: {
            propAutoPlayOnSourceChange: {
                type: Boolean,
                default: false
            },
            propHasHighlight: {
                type: Boolean,
                default: false,
            },
            propAudio: {    //option 1
                type: Object as PropType<Blob> | PropType<File> | null,
                default: null
            },
            propAudioURL: {     //option 2
                type: String,
                default: ''
            },
            propIsRecording: {
                type: Boolean
            },
            propRecordingVisualiserVolume: Number,    //0-1
            propRecordingVisualiserTimeInterval: {  //milliseconds, based on VRecorder time_interval
                type: Number,
                default: 200
            },
            propIsForRecording: {   //if VPlayback is for recording, hide things like volume, etc.
                type: Boolean,
                default: false
            },
            propIsOpen: {   //allows parent to conditionally render this component, for seamless anime continuation
                type: Boolean,
                default: false
            },
            propAudioVolumePeaks: {    //not sure if this is the best way to type this, but it looks ok
                type: Array as PropType<number[]>,
                default: () => [],  //assigning array of 0s immediately after did not solve unrendered issue
            },
            propBucketQuantity: {   //with no default value, this is the fix for unrendered this.$refs.volume_ripple
                type: Number,
                required: true
            },
            propEventTone: {
                type: Object as PropType<EventToneTypes>,
                default: null
            },
        },
        watch: {
            is_loading(new_value){

                if(new_value === true){

                    anime({
                        targets: this.$refs.spinner_container,
                        easing: 'linear',
                        duration: 150,
                        autoplay: true,
                        loop: false,
                        opacity: '1',
                        begin: ()=>{
                            this.spinner_anime.play();
                        }
                    });

                    //'if' statement should help prevent race condition
                    if(this.is_playing === true){

                        this.playback_slider_knob_anime.pause();
                        this.playback_slider_progress_anime.pause();
                    }

                }else{

                    anime({
                        targets: this.$refs.spinner_container,
                        easing: 'linear',
                        duration: 150,
                        autoplay: true,
                        loop: false,
                        opacity: '0',
                        complete: ()=>{
                            this.spinner_anime.pause();
                        }
                    });

                    //'if' statement should help prevent race condition
                    if(this.is_playing === true){

                        this.playback_slider_knob_anime.play();
                        this.playback_slider_progress_anime.play();
                    }
                }
            },
            propAudio(new_value){

                this.attachAudioToPlayback(new_value);
            },
            propAudioURL(new_value){

                //reminder that with v-if and props already supplied, first time will not trigger watchers
                this.attachAudioToPlayback(new_value);
            },
            propRecordingVisualiserVolume(new_value){

                this.animeRecordingVisualiser(new_value);
            },
            propIsRecording(new_value){

                //started recording
                if(new_value === true){

                    if(this.is_playing === true){

                        this.pausePlayback();
                    }

                    this.current_playback_state = this.playback_states[1];

                }else{

                    //cancelled/finished recording
                    this.current_playback_state = this.playback_states[2];
                }
            },
            current_playback_state(){

                //for those that are one-time, put here, and we can disable/enable elements at parent with this
                this.$emit('isAnimePlaybackCompleted', false);

                this.animePlaybackStates();

                this.main_anime.finished.then(()=>{

                    this.$emit('isAnimePlaybackCompleted', true);
                });
            },
            propIsOpen(new_value){

                //if is open, i.e. rendered
                if(new_value === true){

                    //ok to run this often, since it does nothing if dimension is the same
                    this.$nextTick(()=>{
                        if(this.adjustPlaybackSliderDimension() === true && this.has_all_data_for_play === true){
                            this.createPlaybackSliderAnime();
                            this.syncSliderAnimeAfterSuspend();
                        }
                    });
                }

                //if is playing when close, pause playback
                if(new_value === false && this.is_playing === true){

                    this.pausePlayback();
                }
            },
        },
        computed: {
            has_all_data_for_play() : boolean {

                if(
                    this.propAudioVolumePeaks.length > 0 &&
                    this.propAudioVolumePeaks.length === this.propBucketQuantity &&
                    (this.propAudio !== null || this.propAudioURL !== '')
                ){

                    return true;

                }else{

                    return false;
                }
            }
        },
        methods: {
            handleKeyboardEvent(event:KeyboardEvent) : void {

                //one function, for both keydown and keyup
                //some keyup events are too late for .preventDefault(), so they use keydown

                //these keys affect only playback, so no point if there's no file
                if(this.propAudio === null){

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

                        //space also acts like 'enter', so we prevent that
                        event.preventDefault();

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

                            let audio_element = (this.$refs.audio_element as HTMLAudioElement);
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
                                break;
                            }

                    default:

                        break;
                }
            },
            handleWindowResize() : void {

                //for event listener 'resize', this recreates slider anime and syncs it
                this.adjustPlaybackSliderDimension();
                if(this.has_all_data_for_play === true && isNaN((this.$refs.audio_element as HTMLAudioElement).duration) === false){
                    this.createPlaybackSliderAnime();
                    this.syncSliderAnimeAfterSuspend();
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

                        const target = (this.$refs.audio_element as HTMLAudioElement);

                        //we want to mute to avoid the rare slight spike at certain db
                        target.muted = true;
                        this.playPlayback();
                        target.muted = false;
                    }
                }
            },
            createPlaybackSliderAnime() : void {

                //to be called during handleHasMetadata(), window resize, changePlaybackRate()
                //we can then use .play/.pause/.seek
                //expects to already have accurate this.playback_slider_value

                this.is_playback_slider_ready = false;

                //remove
                anime.remove([
                    this.$refs.playback_slider_knob,
                    this.$refs.playback_slider_progress
                ]);
                this.playback_slider_knob_anime = null;
                this.playback_slider_progress_anime = null;

                //calculate starting point of translateX
                const ending_translateX = (this.playback_slider_dimension as DOMRect).width;

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

                this.is_playback_slider_ready = true;
            },
            adjustPlaybackSliderDimension() : boolean {

                //returns true if there is change

                const playback_main = (this.$refs.playback_main as HTMLElement);
                const playback_slider = (this.$refs.playback_slider_dimension as HTMLElement);
                
                if(playback_main.style.display === 'none'){

                    return false;
                }

                //expects playback_slider to have the same width
                //use not only during 'resize' event, but when playback_states[2] is ready
                //as 'resize' may occur when element is display:none
                let new_dimension = playback_slider.getBoundingClientRect();

                //also skip create/recreate anime if no dimensional change
                if(
                    new_dimension.width === 0 ||
                    (
                        this.playback_slider_dimension !== null &&
                        this.playback_slider_dimension.width === new_dimension.width
                    )
                ){

                    return false;
                }

                this.playback_slider_dimension = new_dimension;
                return true;
            },
            endPlaybackProperly() : void {

                //when paused and dragged to end, html media seems to still want you to play once to truly end
                //handle only the media here, the rest are already settled
                const target = (this.$refs.audio_element as HTMLAudioElement);
                target.muted = true;
                target.play();
            },
            startPlaybackDrag(is_playback_slider_touch=false) : void {

                if(this.has_all_data_for_play === false || this.is_playback_slider_ready === false){

                    return;
                }

                this.is_playback_slider_drag = true;
                this.is_playback_slider_touch = is_playback_slider_touch;

                if(this.is_playing === true){

                    this.pausePlayback();
                }
            },
            doPlaybackDrag(event:MouseEvent|TouchEvent) : void {

                if(this.is_playback_slider_drag === true && this.playback_slider_dimension !== null){

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
            stopPlaybackDrag() : void {

                if(this.is_playback_slider_drag === true){

                    //we reset touch detection on every startPlaybackDrag() and stopPlaybackDrag()
                    //so we get latest status of is_playback_slider_touch
                    //some browsers also trigger both touch + mouse events together
                    this.is_playback_slider_touch = false;

                    if(this.playback_slider_value < 1 && this.was_paused === false){

                        this.playPlayback();

                    }else if(this.playback_slider_value === 1 && (this.$refs.audio_element as HTMLAudioElement).ended === false){

                        this.endPlaybackProperly();
                    }

                    this.is_playback_slider_drag = false;
                }

            },
            handlePlaybackDrag() : void {

                //expects playback_slider_value to be float 0 to 1

                //duration is the same regardless of playbackRate
                const jumped_anime_duration = this.playback_slider_value * this.playback_slider_knob_anime.duration;
                //duration changes when playbackRate changes
                const jumped_playback_duration = this.playback_slider_value * (this.$refs.audio_element as HTMLAudioElement).duration;

                //handle slider aesthetics
                //need to set .completed to false, else .play() starts from 0 if it has finished before
                //must be in ms
                this.playback_slider_knob_anime.completed = false;
                this.playback_slider_progress_anime.completed = false;
                this.playback_slider_knob_anime.seek(jumped_anime_duration);
                this.playback_slider_progress_anime.seek(jumped_anime_duration);

                //handle <audio>
                (this.$refs.audio_element as HTMLAudioElement).currentTime = jumped_playback_duration;

                //handle timer
                this.updateCurrentPlaybackTime();
            },
            skipPlayback(seconds=0) : void {

                //+x for forward, -x for backward

                //do this instead of relying on :disabled, as :disabled makes sliders bug out
                if(seconds === 0 || this.has_all_data_for_play === false || this.is_playback_slider_ready === false){

                    return;
                }

                if(this.is_playing === true){

                    this.pausePlayback();
                }

                const target = (this.$refs.audio_element as HTMLAudioElement);
                let updated_time = target.currentTime + seconds;

                if(updated_time < 0){

                    target.currentTime = 0;

                }else if(updated_time > (this.$refs.audio_element as HTMLAudioElement).duration){

                    target.currentTime = (this.$refs.audio_element as HTMLAudioElement).duration;

                }else{

                    target.currentTime = updated_time;
                }

                //update playback_slider_value and visuals
                this.playback_slider_value = target.currentTime / target.duration;
                this.handlePlaybackDrag();

                //resume if originally playing
                if(this.was_paused === false && this.playback_slider_value < 1){

                    this.playPlayback();

                }else if(this.playback_slider_value === 1){

                    this.endPlaybackProperly();
                }
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
                        duration: this.propRecordingVisualiserTimeInterval,
                    });
                }
            },
            updateCurrentPlaybackTime() : void {

                const target = (this.$refs.audio_element as HTMLAudioElement);

                //timer
                this.pretty_current_playback_time = prettyDuration(target.currentTime);
            },
            getRealDurationAfterPlaybackRate() : number{

                //note that when <audio> playbackRate changes, .duration is still the same
                return (this.$refs.audio_element as HTMLAudioElement).duration / this.playback_rate;
            },
            changePlaybackRate(new_value:number) : void {

                if(new_value === this.playback_rate){

                    return;
                }

                //note that on every new file loaded into <audio>, playbackRate is reset
                //attachAudioToPlayback() will handle this inconvenience
                (this.$refs.audio_element as HTMLAudioElement).playbackRate = new_value;
                this.playback_rate = new_value;
                window.localStorage.playback_rate = new_value;

                if((this.$refs.audio_element as HTMLAudioElement).src !== ''){

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
                
                (this.$refs.audio_element as HTMLAudioElement).volume = new_value;
                this.playback_volume = new_value;
                window.localStorage.playback_volume = new_value;
            },
            togglePlaybackSpeedOptions() : void {
                
                this.is_playback_speed_options_open = !this.is_playback_speed_options_open;
            },
            togglePlaybackVolumeOptions() : void {

                //note that slider malfunctions over :disabled elements, i.e. backward/forward, etc.

                if(this.propIsForRecording === true){

                    return;
                }

                this.is_playback_volume_open = !this.is_playback_volume_open;
            },
            playPlayback() : void {

                //using play/pause instead of remove+create prevents slight off-position on second play
                //our new anime position is already settled by handlePlaybackDrag()

                const target = (this.$refs.audio_element as HTMLAudioElement);

                //although redundant, we put target.muted=false here to guarantee it
                //as there has been a rare instance where playback had no audio unintentionally until the next replay
                target.muted = false;
                target.play();
                this.playback_slider_knob_anime.play();
                this.playback_slider_progress_anime.play();
                this.is_playing = true;
                this.was_paused = false;
            },
            pausePlayback() : void {
                
                //if playing, call this before drag, then do playPlayback() once done
                //done at startPlaybackDrag() and stopPlaybackDrag()

                const target = (this.$refs.audio_element as HTMLAudioElement);

                //also recalculate slider value
                target.pause();
                this.playback_slider_knob_anime.pause();
                this.playback_slider_progress_anime.pause();
                this.playback_slider_value = target.currentTime / target.duration;
                this.is_playing = false;

                //for HTMLAudioElement, when you pause right at the end, you can play one more time to reach true end
                //but for anime, it has already completed
                //we end the playback itself via one last play, else its @ended event doesn't run and is queued
                if(
                    target.ended === false &&
                    (
                        this.playback_slider_knob_anime.completed === true ||
                        this.playback_slider_progress_anime.completed === true
                    )
                ){
                    this.endPlaybackProperly();
                }
            },
            togglePlaybackPlayPause() : void {

                //we let everything stay at the end if playback truly ended
                //reset is only triggered on next play

                //do this instead of relying on :disabled, as :disabled makes sliders bug out
                if(this.has_all_data_for_play === false || this.is_playback_slider_ready === false){

                    return;
                }

                //check if playback is not playing
                //was_paused must be here to record user's manual pausing
                if(this.is_playing === false){

                    this.playPlayback();
                    this.was_paused = false;

                }else{

                    this.pausePlayback();
                    this.was_paused = true;
                }
            },
            animePlaybackStates() : void {

                const volume_ripples = (this.$refs.volume_ripple as HTMLElement[]);
                const recording_visualiser = (this.$refs.recording_visualiser as HTMLElement);
                const playback_main = (this.$refs.playback_main as HTMLElement);

                //reset
                this.main_anime !== null ? this.main_anime.seek(this.main_anime.duration) : null;

                switch(this.current_playback_state){

                    case this.playback_states[0]:

                        {
                            //'initiate', only used once
                            //wanted to set to 'empty' and allow for hard reset,
                            //but too lazy to implement checks on recording cancelled + empty

                            this.main_anime = anime.timeline({
                                easing: 'linear',
                                loop: false,
                                autoplay: true,
                            }).add({
                                targets: this.$refs.playback_main,
                                duration: this.fastest_anime_duration_ms,
                                opacity: '0.1',
                            }).add({
                                //set to default volume_ripples
                                targets: volume_ripples,
                                scaleY: ['0', '1'],
                                translateY: ['0%'],
                                duration: this.fastest_anime_duration_ms,
                            });
                        }
                        break;

                    case this.playback_states[1]:

                        {
                            //'recording'

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

                                    //do this so that when cancelled, revert to opacity-10
                                    //we have to run this part here to be able to get latest instance state, as anime() is async
                                    anime({
                                        targets: playback_main,
                                        begin: ()=>{
                                            playback_main.style.display = 'grid';
                                        },
                                        opacity: this.has_all_data_for_play === true ? 1 : 0.1,
                                        easing: 'linear',
                                        duration: this.fastest_anime_duration_ms * 2,
                                        //we want the entire anime to finish before this condition unlocks other actions
                                        //to delay this, we don't use setTimeout
                                        //we multiply duration above instead, so that we can still fully rely on anime's .finished.then()
                                        complete: ()=>{
                                            //set volume_ripples
                                            this.adjustVolumeRipples();
                                        }
                                    });
                                },
                            });                            
                        }
                        break;

                    default:
                        
                        console.log('State is currently null or not one of the declared playback_states.');
                        return;
                }
            },
            adjustVolumeRipples() : void {

                //we calculate height relative to most quiet and loudest parts
                //samples are expected to be between -1 and 1, but we always get -0.0001 to 1
                //so we simply force <0 to be 0, and >1 to be 1

                //if no audio, adjust back
                if(this.propAudioVolumePeaks.length === 0){

                    anime({
                            targets: this.$refs.volume_ripple as HTMLElement[],
                            scaleY: ['0', '1'],
                            autoplay: true,
                            loop: false,
                            easing: 'easeInOutQuad',
                            duration: 200,
                        });

                    return;
                }

                //if has audio, continue
                let scaleY_percentage = 0;

                for(let x=0; x < this.propAudioVolumePeaks.length; x++){

                    //UPDATE: non-zero feels more functional for end user
                    if(this.propAudioVolumePeaks[x] < 0.05){

                        scaleY_percentage = 0.05;

                    }else if(this.propAudioVolumePeaks[x] > 1){

                        scaleY_percentage = 1;

                    }else{

                        scaleY_percentage = this.propAudioVolumePeaks[x];
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
                }
            },
            attachAudioToPlayback(new_audio:string|Blob|File) : void {

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);

                //pause first if playing, and reset slider value
                //we don't create new slider here, but at <audio>'s @loadedmetadata, as its .duration is only available then
                if(this.is_playing === true){

                    this.pausePlayback();
                }

                //destroy URL.createObjectURL() instance to free from memory, then stop loading, no checks needed
                //https://developer.mozilla.org/en-US/docs/Web/Guide/Audio_and_video_delivery#other_tips_for_audiovideo
                URL.revokeObjectURL(audio_element.src);
                audio_element.removeAttribute('src');
                audio_element.load();

                if(typeof(new_audio) === 'string'){

                    //attach audio from URL origin
                    audio_element.setAttribute('src', window.location.origin + new_audio);

                }else{

                    //attach audio from Blob/File origin
                    audio_element.setAttribute('src', URL.createObjectURL(new_audio));
                }

                audio_element.load();

                //on every new file loaded into <audio>, playbackRate is reset by default
                //this is the fix
                audio_element.playbackRate = this.playback_rate;

                //cannot rely on current_playback_state watcher,
                //as merely changing source (i.e. playback_states[2] below) will not trigger watcher
                this.adjustVolumeRipples();

                //update state, not always needed but just to be sure
                this.current_playback_state = this.playback_states[2];
            },
            handleHasMetadata() : void {

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);

                //there's a bug that gives us 'Infinity'
                //this is how we fix it
                //https://stackoverflow.com/a/69512775
                if((audio_element.duration as number|string) == 'Infinity'){

                    const handler = ()=>{

                        audio_element.currentTime = 0;
                        audio_element.removeEventListener('timeupdate', handler);

                        //mm:ss
                        //only for duration display we will use floor
                        this.pretty_playback_duration = prettyDuration(
                            (this.$refs.audio_element as HTMLAudioElement).duration
                        );
                        
                        //here is the first time <audio> duration is finally available
                        this.adjustPlaybackSliderDimension();
                        this.createPlaybackSliderAnime();

                        //auto-play if desired, condition checking is also already handled
                        if(this.propAutoPlayOnSourceChange === true){

                            this.togglePlaybackPlayPause();
                        }
                    };

                    audio_element.currentTime = 1e101;
                    audio_element.addEventListener('timeupdate', handler);
                }

                //don't try to access (this.$refs.audio_element as HTMLAudioElement).duration precisely here, as something is async
                //you'll get 0, but if you check via watch, the value does change
                //put your code in handler instead if you need to run something else
            },
        }
    });
</script>