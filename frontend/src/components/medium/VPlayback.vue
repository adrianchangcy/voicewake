<template>
    <div
        class="text-theme-black text-center"
    >
        <!--add @timeupdate at mounted(), not here, as beforeUnmount() cannot remove it, and it'll still fire after unmount-->
        <!--must add all calls in handleHasMetadata(), not here, since the Infinity duration is not fixed until then-->
        <audio
            ref="audio_element"
            @loadedmetadata="[handleHasMetadata()]"
            @canplay="is_playback_buffering=false"
            @waiting="is_playback_buffering=true"
            @ended="[pausePlaybackAndUpdateSliderValue(), user_paused=true]"
        ></audio>

        <!--
            ripples, slider, volume, play/pause, rate, timers
        -->
        <div
            ref="playback_main"
            :class="[
                propEvent === null ? 'grid-cols-3 pr-4' : 'grid-cols-4',
                'h-20 grid grid-rows-2 rounded-lg border border-theme-light-gray shade-border-when-hover transition-colors'
            ]"
            @pointerdown="[updateInstanceLastInteracted(), instance_has_focus=true]"
            @focusin="[updateInstanceLastInteracted(), instance_has_focus=true]"
            @focusout="instance_has_focus=false"
        >

            <!--play/pause-->
            <div class="row-start-1 row-span-2 col-start-1 col-span-1 text-4xl relative">
                <VActionTextOnly
                    @pointerdown="userTogglePlaybackPlayPause()"
                    @keydown.enter="userTogglePlaybackPlayPause()"
                    :propIsEnabled="isPlaybackReady"
                    propElement="button"
                    type="button"
                    :propIsIconOnly="true"
                    :propIsDefaultOutlineOffset="false"
                    class="absolute left-2 right-2 top-2 bottom-2 focus-visible:-outline-offset-2"
                >
                    <i
                        :class="[
                            is_playing? 'fa-pause' : 'fa-play',
                            'fas mt-[1px]'
                        ]"
                    ></i>
                    <span v-if="is_playing" class="sr-only">
                        pause
                    </span>
                    <span v-else class="sr-only">
                        play
                    </span>
                </VActionTextOnly>
            </div>

            <!--ripples, slider, do left-2 right-2 m-auto if you want outermost knob to be within bounds-->
            <div
                class="h-12 row-start-1 row-span-1 col-start-2 col-span-2 relative"
            >

                <!--ripples-->
                <!--need inline CSS to prevent jolting from anime if without it-->
                <div
                    ref="volume_ripples_container"
                    class="w-full h-8 absolute top-2 pb-2 flex flex-row justify-between px-2"
                >
                    <div
                        v-for="volume_ripple in propBucketQuantity" :key="volume_ripple"
                        ref="volume_ripple"
                        class="h-full origin-bottom"
                        style="transform: scaleY(0);"
                    >
                        <div
                            :class="[
                                isPlaybackReady === true ? 'bg-theme-black' : 'outline-1 outline outline-theme-dark-gray',
                                'left-0 right-0 mx-auto w-0.5 h-full'
                            ]"
                        ></div>
                    </div>
                </div>

                <!--slider-->
                <div
                    class="w-full h-10 absolute top-2"
                >
                    <!--only want z-10 here so that it takes priority over volume button-->
                    <!--we want to use button instead of div to allow for pointerdown bubbling-->
                    <button
                        ref="playback_slider"
                        :class="[
                            isPlaybackReady === true ? 'touch-none cursor-pointer' : 'cursor-default',
                            'w-full h-full relative z-10 rounded-lg parent-trigger-double-height-when-hover    focus:outline-none focus-visible:outline-none'
                        ]"
                        @pointerdown="[startPlaybackDrag(), doPlaybackDrag($event)]"
                        type="button"
                        tabindex="-1"
                    >

                        <!--for dimension reference, since playback_slider_progress cannot give full width at start-->
                        <div
                            ref="playback_slider_dimension"
                            class="h-0 absolute opacity-0 left-2 right-2 top-0 bottom-0 m-auto"
                        ></div>

                        <!--loading-->
                        <div
                            v-show="is_playback_buffering"
                            class="h-1 absolute left-0 right-0 bottom-2 m-auto"
                        >
                            <div
                                :class="[
                                    isPlaybackReady === true ? 'double-height-when-hover' : '',
                                    'w-full h-full skeleton transform'
                                ]"
                            ></div>
                        </div>
                        <!--not loading-->
                        <div
                            v-show="!is_playback_buffering"
                            :class="[
                                isPlaybackReady === true ? 'double-height-when-hover' : '',
                                'h-1 absolute bg-theme-light-gray left-0 right-0 bottom-2 m-auto transition-transform'
                            ]"
                        ></div>

                        <div
                            ref="playback_slider_progress"
                            class="h-1 absolute bg-theme-lead left-0 right-0 bottom-2 m-auto scale-x-0 origin-left"
                        ></div>
                        <div
                            ref="playback_slider_knob"
                            class="w-4 h-4 absolute rounded-full bg-theme-black bottom-0.5 m-auto"
                        >
                        </div>

                        <span class="sr-only">playback navigation</span>
                    </button>
                </div>
            </div>

            <!--volume, timers-->
            <!--originally h-10, as per grid, but do pt-2 to let row above be h-12-->
            <!--use my-auto but do -top-2 bottom-0 for child-most element to align as if it is h-10-->
            <div
                class="pt-2 row-start-2 row-span-1 col-start-2 col-span-2 grid grid-rows-1 grid-cols-3"
            >

                <!--current duration-->
                <div class="row-start-1 row-span-1 col-start-1 col-span-1 relative text-xs sm:text-sm">
                    <span class="sr-only">current duration</span>
                    <span class="absolute w-fit h-fit left-0 -top-[0.625rem] bottom-0 m-auto">{{pretty_current_playback_time}}</span>
                </div>

                <!--volume-->
                <div
                    v-if="propIsForRecording === false"
                    ref="playback_volume_opener"
                    class="row-start-1 row-span-1 col-start-2 col-span-1 h-full relative text-lg"
                >

                    <!--volume content-->
                    <div
                        :class="[
                            is_playback_volume_open ? 'h-32 z-10 bg-theme-light border-theme-dark-gray' : 'h-full border-transparent',
                            'absolute w-full bottom-0 m-auto border rounded-lg'
                        ]"
                        @pointerenter.stop="handlePlaybackVolumeHoverIn($event)"
                        @pointerleave.stop="handlePlaybackVolumeHoverOut($event)"
                    >

                        <!--volume button-->
                        <VActionTextOnly
                            @pointerdown="toggleMute($event)"
                            @keydown.enter="toggleMute($event)"
                            :propIsEnabled="isPlaybackReady"
                            propElement="button"
                            type="button"
                            :propIsIconOnly="true"
                            :propIsDefaultOutlineOffset="false"
                            class="w-full h-10 absolute -bottom-0.5 focus-visible:-outline-offset-8"
                        >
                            <div class="w-full h-full relative">
                                <i
                                    :class="[
                                        (isMuted ? 'fa-volume-xmark' : ''),
                                        (playback_volume <= 0.5 ? 'fa-volume-low' : ''),
                                        (playback_volume <= 1 ? 'fa-volume-high' : ''),
                                        (is_playback_volume_open ? '-rotate-90' : 'rotate-0'),
                                        'fas transition-transform w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto'
                                    ]"
                                ></i>
                            </div>
                            <span v-show="isMuted" class="sr-only">
                                unmute to {{ getPrettyVolume }} and open volume menu
                            </span>
                            <span v-show="!isMuted" class="sr-only">
                                mute
                            </span>
                        </VActionTextOnly>

                        <!--volume menu-->
                        <!--h-22, so +h-10 of button, we can set content size at h-32-->
                        <VSliderYSmall
                            v-show="is_playback_volume_open"
                            ref="volume_slider"
                            :propSliderValue="playback_volume"
                            @hasNewSliderValue="changePlaybackVolume($event)"
                            @startDragSliderValue="handleVolumeStartDrag($event)"
                            @stopDragSliderValue="handleVolumeStopDrag($event)"
                            class="w-full h-[5.5rem] absolute left-0 right-0 bottom-10 m-auto px-2 pt-5 pb-1"
                        >
                            <span class="sr-only">vertical volume box</span>
                        </VSliderYSmall>
                    </div>
                </div>

                <!--total duration-->
                <div class="row-start-1 row-span-1 col-start-3 col-span-1 relative text-xs sm:text-sm">
                    <span class="absolute w-fit h-fit right-0 -top-[0.625rem] bottom-0 m-auto">
                        <span class="sr-only">total duration</span>
                        {{pretty_playback_duration}}
                    </span>
                </div>
            </div>

            <div
                v-if="propEvent !== null"
                class="row-span-2 col-span-1 relative"
            >
                <span class="text-2xl pb-0.5 absolute w-fit h-fit left-0 right-0 top-0 bottom-0 m-auto">
                    {{ propEvent.event_tone.event_tone_symbol }}
                </span>
            </div>
        </div>
    </div>
</template>



<script setup lang="ts">
    import VSliderYSmall from '/src/components/small/VSliderYSmall.vue';
    import VActionTextOnly from '../small/VActionTextOnly.vue';
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import { prettyDuration, getRandomUUID } from '@/helper_functions';
    import anime from 'animejs';
    import EventTypes from '@/types/Events.interface';
    import VSliderTypes from '@/types/values/VSlider';
    import { useVPlaybackStore } from '@/stores/VPlaybackStore';

    export default defineComponent({
        data(){
            return {
                instance_id: "",    //uuid, to identify between multiple VPlayback instances
                vplayback_store: useVPlaybackStore(),
                instance_has_focus: false,  //enables keyboard events inside VPlayback that need e.preventDefault()
                previous_event: null as EventTypes | null,  //store triggers on new event, but needs previous event

                pretty_current_playback_time: '00:00',
                pretty_playback_duration: '00:00',
                is_playing: false,
                main_anime: null as InstanceType<typeof anime> | null,   //to store animePlaybackStates() anime

                is_playback_empty_anime: true,  //this is only to anime empty --> non-empty once, and vice versa

                is_playback_slider_ready: false,
                is_playback_attached: false,

                is_playback_buffering: false,
                is_playback_slider_processing: false,
                is_playback_attaching: false,

                playback_slider_value: 0,
                is_playback_slider_drag: false,
                playback_slider_dimension: null as DOMRect | null,
                playback_slider_knob_anime: null as InstanceType<typeof anime> | null, //we play/pause instead of new anime() for best results
                playback_slider_progress_anime: null as InstanceType<typeof anime> | null, //we play/pause instead of new anime() for best results
                user_paused: true,  //if user pauses, then navigating will not auto-play

                playback_rate: 1,   //allows 0 to 2, but we handle 0.5, 1, 1.5
                playback_volume: 0, //accepts 0 to 1
                backup_playback_volume: 0,  //accepts 0 to 1, used when unmuting playback_volume from 0

                is_playback_speed_options_open: false,
                
                //everything else will auto-close volume menu
                //except for hover
                //always use openPlaybackVolume() and closePlaybackVolume() to ensure timeout is synced
                is_playback_volume_open: false,
                autoclose_playback_volume_timeout: null as number|null,

                playback_states: ['initiate', 'recording', 'attaching', 'can_play', 'loading'],

                fastest_anime_duration_ms: 100, //to change anime durations easily
            };
        },
        emits: [
            'newFileVolumes', 'isReadyToPlay', 'isProcessing'
        ],
        props: {
            propAutoPlayOnSourceChange: {
                type: Boolean,
                default: false
            },
            propEvent: {
                type: Object as PropType<EventTypes>,
                default: null
            },
            propAudio: {    //used when receiving from VRecorder
                type: Object as PropType<Blob> | PropType<File> | null,
                default: null
            },
            propIsRecording: {  //when changed, pause VPlayback
                type: Boolean
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
        },
        watch: {
            is_playback_buffering(new_value){

                if(new_value === true){

                    //'if' statement should help prevent race condition
                    if(this.is_playing === true){

                        this.playback_slider_knob_anime.pause();
                        this.playback_slider_progress_anime.pause();
                    }

                }else{

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
            propEvent(new_value:EventTypes|null){

                //reminder that with v-if and props already supplied, first time will not trigger watchers

                if(new_value !== null){

                    //do store before new audio is attached
                    if(this.previous_event !== null){

                        this.storeCurrentEventLastStopped(this.previous_event);
                    }

                    //store previous event for situations where store needs it
                    this.previous_event = new_value;

                    //attach new audio
                    this.attachAudioToPlayback(new_value.audio_file);
                }
            },
            propIsRecording(new_value){

                //started recording
                if(new_value === true){

                    if(this.is_playing === true){

                        this.pausePlaybackAndUpdateSliderValue();
                    }
                }
            },
            propIsOpen(new_value){

                //if is open, i.e. rendered
                if(new_value === true){

                    //ok to run this often, since it does nothing if dimension is the same
                    this.$nextTick(()=>{
                        if(this.adjustPlaybackSliderDimension() === true && this.isPlaybackReady === true){
                            this.createPlaybackSliderAnime();
                            this.syncSliderAnimeAfterSuspend();
                        }
                    });
                }

                //if is playing when close, pause playback
                if(new_value === false && this.is_playing === true){

                    this.pausePlaybackAndUpdateSliderValue();
                }
            },
        },
        computed: {
            getPrettyVolume() : string {
                
                return (this.playback_volume * 100).toString() + "%";
            },
            isMuted() : boolean {

                return this.playback_volume === 0;
            },
            isPlaybackReady() : boolean {

                const is_playback_ready = (
                    this.propAudioVolumePeaks.length > 0 &&
                    this.propAudioVolumePeaks.length === this.propBucketQuantity &&
                    (this.propAudio !== null || this.propEvent !== null) &&
                    this.is_playback_slider_ready === true &&
                    this.is_playback_attached === true &&
                    this.isProcessing === false
                );

                this.$emit('isReadyToPlay', is_playback_ready);
                return is_playback_ready;
            },
            isProcessing() : boolean {

                const is_processing = this.is_playback_attaching || this.is_playback_slider_processing;

                this.$emit('isProcessing', is_processing);
                return is_processing;
            },
            isInstanceLastInteracted() : boolean {

                return this.instance_id === this.vplayback_store.getLastInteractedUUID;
            },
        },
        methods: {
            determineInstanceHasFocus(event:PointerEvent) : void {

                this.instance_has_focus = (this.$refs.playback_main as HTMLElement).contains(event.target as Node);
            },
            syncToPlaybackSliderValue() : void {

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);

                if(
                    audio_element.src === '' ||
                    this.playback_slider_knob_anime === null || this.playback_slider_progress_anime === null
                ){

                    return;
                }
                
                //duration is the same regardless of playbackRate
                const jumped_anime_duration = this.playback_slider_value * this.playback_slider_knob_anime.duration;
                //duration changes when playbackRate changes
                const jumped_playback_duration = this.playback_slider_value * audio_element.duration;

                this.playback_slider_knob_anime.seek(jumped_anime_duration);
                this.playback_slider_progress_anime.seek(jumped_anime_duration);
                this.playback_slider_knob_anime.completed = false;
                this.playback_slider_progress_anime.completed = false;

                audio_element.currentTime = jumped_playback_duration;

                if(this.playback_slider_value === 1){

                    this.endPlaybackProperly();
                }
            },
            setInitialPlaybackSliderValue() : void {
                
                //initial
                this.playback_slider_value = 0;

                if(this.propEvent === null){

                    return;
                }

                const last_stopped_s = this.vplayback_store.getEventPlaybackLastStoppedS(this.propEvent.id);

                //not stored
                if(last_stopped_s === null){

                    return;
                }

                const total_duration_s = (this.$refs.audio_element as HTMLAudioElement).duration;

                //restore slider value
                //as long as both this function and StoreCurrentEventLastStopped() use <audio>.currentTime,
                //value should always be <= 1
                let new_value = Number((last_stopped_s / total_duration_s).toFixed(3));

                this.playback_slider_value = new_value;
            },
            storeCurrentEventLastStopped(specific_event:EventTypes) : void {

                //call this after pause on source change, but before source change happens

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);
                const specific_event_full_url = window.location.origin + specific_event.audio_file;

                if(
                    specific_event.audio_file.length === 0 ||
                    specific_event === null || audio_element.src === '' ||
                    audio_element.src !== specific_event_full_url
                ){

                    return;
                }

                //get seconds
                //0 if no audio
                const current_time_s = audio_element.currentTime;

                //no need to store if 0
                if(current_time_s === 0){

                    return;
                }

                //store
                this.vplayback_store.addEventPlaybackLastStopped(specific_event.id, current_time_s);
            },
            updateInstanceLastInteracted(to_remove:boolean=false) : void {

                //any actions taken to any VPlayback instance will update store
                //so that handleKeyboardEvent() goes through for "last interacted VPlayback" only

                if(to_remove === false){

                    this.vplayback_store.updateLastInteractedUUID(this.instance_id);

                }else{

                    this.vplayback_store.updateLastInteractedUUID("");
                }
            },
            handleInitialAutoplay() : void {

                //auto-play if desired, condition checking is also already handled at this stage

                if(this.propAutoPlayOnSourceChange === false){

                    return;
                }

                if(this.playback_slider_value < 1){

                    this.userTogglePlaybackPlayPause();
                }
            },
            handlePlaybackVolumeHoverIn(event:PointerEvent) : void {

                //don't handle hover if not mouse, since hover behaviour is meant for mouse only
                //otherwise, touch triggers mouseenter and mouseleave undesirably
                if(event.pointerType !== "mouse"){

                    return;
                }

                this.openPlaybackVolume();
            },
            handlePlaybackVolumeHoverOut(event:PointerEvent) : void {

                //don't handle hover if not mouse, since hover behaviour is meant for mouse only
                //otherwise, touch triggers mouseenter and mouseleave undesirably
                if(event.pointerType !== "mouse"){

                    return;
                }

                this.closePlaybackVolume(false);
            },
            handleVolumeStartDrag(new_value:VSliderTypes) : void {

                this.openPlaybackVolume();
                this.saveBackupPlaybackVolume(new_value.slider_value);
            },
            handleVolumeStopDrag(new_value:VSliderTypes) : void {

                this.saveBackupPlaybackVolume(new_value.slider_value);

                //don't close from here if user is hovering
                if(new_value.pointer_type === "mouse"){

                    return;
                }

                this.closePlaybackVolume();
            },
            saveBackupPlaybackVolume(new_value:number) : void {

                //never 0
                if(new_value === 0){

                    return;
                }

                window.localStorage.backup_playback_volume = new_value;
            },
            toggleMute(event:KeyboardEvent|PointerEvent|null=null) : void {

                //we don't use audio_element.muted
                //we simply move volume to 0 when user wants to mute, for better UX, as per YouTube
                //.muted continues to be used for bug fixes

                if(this.propIsForRecording === true){
                    
                    return;
                }

                this.openPlaybackVolume();

                //briefly open menu on unmute
                if(this.playback_volume === 0){

                    //unmute, i.e. set volume back to original
                    this.playback_volume = parseFloat(window.localStorage.backup_playback_volume);
                    (this.$refs.audio_element as HTMLAudioElement).volume = this.playback_volume;
                    window.localStorage.playback_volume = this.playback_volume;

                }else{

                    //mute, i.e. set volume to 0
                    this.playback_volume = 0;
                    (this.$refs.audio_element as HTMLAudioElement).volume = 0;
                    window.localStorage.playback_volume = 0;
                }

                //don't close if user is hovering with mouse
                if(event !== null && "pointerType" in event && event.pointerType === "mouse"){

                    return;
                }

                this.closePlaybackVolume();
            },
            openPlaybackVolume() : void {

                //remove timeout
                if(this.autoclose_playback_volume_timeout !== null){

                    window.clearTimeout(this.autoclose_playback_volume_timeout);
                    this.autoclose_playback_volume_timeout = null;
                }

                this.is_playback_volume_open = true;
            },
            closePlaybackVolume(has_delay=true) : void {

                //remove timeout
                if(this.autoclose_playback_volume_timeout !== null){

                    window.clearTimeout(this.autoclose_playback_volume_timeout);
                    this.autoclose_playback_volume_timeout = null;
                }

                //close later
                if(has_delay === true){

                    this.autoclose_playback_volume_timeout = window.setTimeout(()=>{
                        this.is_playback_volume_open = false;
                    }, 1000);

                }else{

                    this.is_playback_volume_open = false;
                }
            },
            userAdjustVolume(add_or_sub_value:number) : void {

                //pass values like 0.2 to add, -0.2 to sub

                if(
                    this.propIsForRecording === true || add_or_sub_value < -1 || add_or_sub_value > 1
                ){

                    return;
                }

                let new_playback_volume = this.playback_volume + add_or_sub_value;
                new_playback_volume = parseFloat(new_playback_volume.toFixed(2));

                //ensure it is never > 1
                if(new_playback_volume > 1){

                    new_playback_volume = 1;

                }else if(new_playback_volume < 0){

                    new_playback_volume = 0;
                }
                
                this.changePlaybackVolume(new_playback_volume);
                this.closePlaybackVolume();

                //save backup volume for unmute scenario
                if(new_playback_volume > 0){

                    this.saveBackupPlaybackVolume(new_playback_volume);
                }
            },
            handleKeyboardEvent(event:KeyboardEvent) : void {

                //FYI, some keyup events are too late for .preventDefault(), so they use keydown

                //these keys affect only playback, so no point if there's no file
                if(this.isPlaybackReady === false || this.isInstanceLastInteracted === false){

                    return;
                }

                //ensure this won't be used during user input
                const event_target = (event.target as Node);

                if(event_target.nodeName === "INPUT" || event_target.nodeName === "TEXTAREA"){

                    return;
                }

                //keyCode is deprecated, use .key
                    //.code is different on different types of keyboards, but .key will be consistent
                //https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/key
                switch(event.key){

                    case 'ArrowLeft':

                        //go backwards playback
                        this.skipPlayback(-5);
                        break;

                    case 'ArrowRight':

                        //go forward playback
                        this.skipPlayback(5);
                        break;

                    case ' ':

                        //space also acts like 'enter', so we prevent that
                        event.preventDefault();

                        //play/pause
                        this.userTogglePlaybackPlayPause();
                        break;

                    case 'm':

                        {
                            //mute/unmute
                            //when for recording, no volume option
                            //we use localStorage for backup value from mute to unmute
                            this.toggleMute(null);
                            break;
                        }

                    case 'ArrowUp':

                        if(this.instance_has_focus === true){

                            event.preventDefault();
                            this.userAdjustVolume(0.2);
                        }

                        break;

                    case 'ArrowDown':

                        if(this.instance_has_focus === true){

                            event.preventDefault();
                            this.userAdjustVolume(-0.2);
                        }

                        break;

                    default:

                        break;
                }
            },
            handleWindowResize() : void {

                //during hot reload (change html/css --> save --> DOM changes without refresh), JS parts get slightly buggy
                //e.g. all playback skips just lead to seek(0)
                //simply do a manual refresh

                //for event listener 'resize', this recreates slider anime and syncs it
                this.adjustPlaybackSliderDimension();

                if(this.isPlaybackReady === true && isNaN((this.$refs.audio_element as HTMLAudioElement).duration) === false){
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

                        //reminder that pausePlaybackAndUpdateSliderValue() also updates this.playback_slider_value
                        this.pausePlaybackAndUpdateSliderValue();
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

                //states
                this.is_playback_slider_ready = false;
                this.is_playback_slider_processing = true;

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

                //states
                this.is_playback_slider_ready = true;
                this.is_playback_slider_processing = false;
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

                const target = (this.$refs.audio_element as HTMLAudioElement);

                if(target.ended === false && target.paused === true){

                    //when paused and dragged to end, html media seems to still want you to play once to truly end
                    //handle only the media here, the rest are already settled
                    target.muted = true;
                    target.currentTime = target.duration;
                    target.play();

                    //must do this, otherwise during edge case where endPlaybackProperly() is still running
                    //and user plays, anime will restart from 0
                    this.playback_slider_knob_anime.seek(this.playback_slider_knob_anime.duration);
                    this.playback_slider_progress_anime.seek(this.playback_slider_progress_anime.duration);
                    this.playback_slider_knob_anime.completed = true;
                    this.playback_slider_progress_anime.completed = true;
                }
            },
            startPlaybackDrag() : void {

                if(this.isPlaybackReady === false){

                    return;
                }

                this.is_playback_slider_drag = true;

                if(this.is_playing === true){

                    this.pausePlaybackAndUpdateSliderValue();
                }

                //fixed: drag to end --> .completed=true --> .seek() --> .play() starts from 0
                this.playback_slider_knob_anime.completed = false;
                this.playback_slider_progress_anime.completed = false;
            },
            doPlaybackDrag(event:PointerEvent) : void {

                if(this.is_playback_slider_drag === true && this.playback_slider_dimension !== null){

                    //can use clientX, screenX, pageX
                    //clientY seems to work best
                    const user_x = event.clientX;

                    if(user_x >= this.playback_slider_dimension.left && user_x <= this.playback_slider_dimension.right){

                        //will always be 0 to 1
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

                    if(this.playback_slider_value < 1 && this.user_paused === false){

                        this.playPlayback();

                    }else if(this.playback_slider_value === 1 && (this.$refs.audio_element as HTMLAudioElement).ended === false){

                        this.endPlaybackProperly();
                    }

                    this.is_playback_slider_drag = false;
                }

            },
            handlePlaybackDrag() : void {

                //expects playback_slider_value to be float 0 to 1

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);

                //duration is the same regardless of playbackRate
                const jumped_anime_duration = this.playback_slider_value * this.playback_slider_knob_anime.duration;
                //duration changes when playbackRate changes
                const jumped_playback_duration = this.playback_slider_value * audio_element.duration;

                //handle slider aesthetics
                //need to set .completed to false, else .play() starts from 0 if it has finished before
                //must be in ms

                this.playback_slider_knob_anime.seek(jumped_anime_duration);
                this.playback_slider_progress_anime.seek(jumped_anime_duration);

                //fixed: anytime .seek(end), .completed=true automatically, causing unintentional start from 0
                this.playback_slider_knob_anime.completed = false;
                this.playback_slider_progress_anime.completed = false;

                //handle <audio>
                (this.$refs.audio_element as HTMLAudioElement).currentTime = jumped_playback_duration;

                //handle timer
                this.updateCurrentPlaybackTime();
            },
            skipPlayback(seconds=0) : void {

                //+x for forward, -x for backward

                //do this instead of relying on :disabled, as :disabled makes sliders bug out
                if(seconds === 0 || this.isPlaybackReady === false){

                    return;
                }

                if(this.is_playing === true){

                    this.pausePlaybackAndUpdateSliderValue();
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
                if(this.user_paused === false && this.playback_slider_value < 1){

                    this.playPlayback();

                }else if(this.playback_slider_value === 1){

                    this.endPlaybackProperly();
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

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);

                if(new_value === this.playback_rate || audio_element.src === ''){

                    return;
                }

                //consider is_playing when this rate change happened
                const resume_later = this.is_playing;

                //pause to make changes, and to update playback_slider_value
                this.pausePlaybackAndUpdateSliderValue();

                //update values
                //note that on every new file loaded into <audio>, playbackRate is reset
                //attachAudioToPlayback() will handle this inconvenience
                audio_element.playbackRate = new_value;
                this.playback_rate = new_value;
                window.localStorage.playback_rate = new_value;

                //adjust anime
                this.createPlaybackSliderAnime();
                this.playback_slider_knob_anime.seek(this.playback_slider_value * this.playback_slider_knob_anime.duration);
                this.playback_slider_progress_anime.seek(this.playback_slider_value * this.playback_slider_progress_anime.duration);

                //play if was playing
                if(resume_later === true){

                    this.playPlayback();
                }
            },
            changePlaybackVolume(new_value:number) : void {
                
                (this.$refs.audio_element as HTMLAudioElement).volume = new_value;
                this.playback_volume = new_value;
                window.localStorage.playback_volume = new_value;

                //show volume menu
                this.openPlaybackVolume();
            },
            togglePlaybackSpeedOptions() : void {
                
                this.is_playback_speed_options_open = !this.is_playback_speed_options_open;
            },
            playPlayback() : void {

                //using play/pause instead of remove+create prevents slight off-position on second play
                //our new anime position is already settled by handlePlaybackDrag()

                const target = (this.$refs.audio_element as HTMLAudioElement);

                //this is important to let endPlaybackProperly() do its thing
                if(target.paused === false){

                    return;
                }

                //although redundant, we put target.muted=false here to guarantee it
                //as there has been a rare instance where playback had no audio unintentionally until the next replay
                target.muted = false;
                target.play();
                this.is_playing = true;
                this.user_paused = false;

                if(this.is_playback_buffering === false){

                    this.playback_slider_knob_anime.play();
                    this.playback_slider_progress_anime.play();
                }
            },
            pausePlaybackAndUpdateSliderValue() : void {
                
                //if playing, call this before drag, then do playPlayback() once done
                //done at startPlaybackDrag() and stopPlaybackDrag()

                const target = (this.$refs.audio_element as HTMLAudioElement);

                //also recalculate slider value
                target.pause();
                this.playback_slider_value = target.currentTime / target.duration;
                this.is_playing = false;

                if(this.is_playback_buffering === false){

                    this.playback_slider_knob_anime.pause();
                    this.playback_slider_progress_anime.pause();
                }

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
            userTogglePlaybackPlayPause() : void {

                //we let everything stay at the end if playback truly ended
                //reset is only triggered on next play

                //do this instead of relying on :disabled, as :disabled makes sliders bug out
                if(this.isPlaybackReady === false){

                    return;
                }

                //edge case of dragging + space
                //cancel drag if so, while stopPlaybackDrag() auto-plays for us
                if(this.is_playback_slider_drag === true){
                    
                    this.stopPlaybackDrag();

                    //if we don't return here, we get "play() interrupted by pause()"
                    return;
                }

                //check if playback is not playing
                //user_paused must be here to record user's manual pausing
                if(this.is_playing === false){

                    this.playPlayback();
                    this.user_paused = false;

                }else{

                    this.pausePlaybackAndUpdateSliderValue();
                    this.user_paused = true;
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

                    this.pausePlaybackAndUpdateSliderValue();
                }

                //states
                this.is_playback_attached = false;
                this.is_playback_attaching = true;

                this.animeIsNotEmptyPlayback();

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

                //states
                this.is_playback_attached = true;
                this.is_playback_attaching = false;

                this.adjustVolumeRipples();
            },
            handleHasMetadata() : void {

                //@loadedmetadata is when <audio>.duration is finally available

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);

                //there's a bug that gives us 'Infinity', had we not used fixWebmDuration
                //this is because the browser does not insert duration metadata into our webm
                //this is how we fix it, which still applies after the fixWebmDuration solution
                //https://stackoverflow.com/a/69512775

                const handler = ()=>{

                    audio_element.currentTime = 0;
                    audio_element.removeEventListener('timeupdate', handler);

                    //mm:ss
                    //only for duration display we will use floor
                    this.pretty_playback_duration = prettyDuration(
                        (this.$refs.audio_element as HTMLAudioElement).duration
                    );

                    this.adjustPlaybackSliderDimension();
                    this.createPlaybackSliderAnime();
                    this.setInitialPlaybackSliderValue();
                    this.syncToPlaybackSliderValue();
                    this.handleInitialAutoplay();
                };

                audio_element.currentTime = 1e101;
                audio_element.addEventListener('timeupdate', handler);

                //don't try to access (this.$refs.audio_element as HTMLAudioElement).duration precisely here, as something is async
                //you'll get 0, but if you check via watch, the value does change
                //put your code in handler instead if you need to run something else
            },
            animeIsNotEmptyPlayback() : void {

                if(this.is_playback_empty_anime === false){

                    return;
                }

                anime({
                    easing: 'linear',
                    loop: false,
                    autoplay: true,
                    targets: this.$refs.playback_main,
                    duration: this.fastest_anime_duration_ms,
                    opacity: '1',
                });

                this.is_playback_empty_anime = false;
            },
            animeIsEmptyPlayback(): void {

                const volume_ripples = (this.$refs.volume_ripple as HTMLElement[]);

                anime.timeline({
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

                this.is_playback_empty_anime = true;
            }
        },
        mounted(){

            //generate uuid for this component instance
            this.instance_id = getRandomUUID();

            //initial state
            this.animeIsEmptyPlayback();
            this.$emit('isProcessing', false);

            //if store has no instance recorded yet, use current instance as default, whichever mounts first
            if(this.vplayback_store.getLastInteractedUUID === ""){

                this.vplayback_store.updateLastInteractedUUID(this.instance_id);
            }

            //handle when propEvent already exists on mounted, which means it's from API
            if(this.propEvent !== null && this.propEvent.audio_file.length > 0){

                this.previous_event = this.propEvent;
                this.attachAudioToPlayback(this.propEvent.audio_file);
            }

            //handle rate and volume differently
            if(this.propIsForRecording === true){

                //we set rate to 1 and volume to max, and hide them
                //there is no need for them if intended for recording, for best feedback
                this.playback_rate = 1;
                this.playback_volume = 1;

            }else{

                //handle localStorage
                //invoking them gives you get() value, so const would not behave like a reference

                //rate
                if(window.localStorage.playback_rate === undefined){
                    window.localStorage.playback_rate = 1;
                }

                //volume, default 50%
                if(window.localStorage.playback_volume === undefined){
                    window.localStorage.playback_volume = 0.5;
                }

                //backup volume, i.e. the value before volume is ever set to 0
                //this is successfully done based on when you call to modify this
                if(window.localStorage.backup_playback_volume === undefined){
                    window.localStorage.backup_playback_volume = 0.5;
                }

                //set values
                this.playback_rate = parseFloat(window.localStorage.playback_rate);
                this.playback_volume = parseFloat(window.localStorage.playback_volume);
                this.backup_playback_volume = parseFloat(window.localStorage.backup_playback_volume);

                //mute decision
                    //scenario #1:
                        //when mute, it is volume 0
                    //scenario #2:
                        //when mute, it is muted, but volume is original
                    //scenario #1 is more keyboard-friendly
                    //scenario #2, when volume at 100%, one accidental arrowup would blast the volume to max
            }

            //set <audio> rate and volume
            (this.$refs.audio_element as HTMLAudioElement).playbackRate = this.playback_rate;
            (this.$refs.audio_element as HTMLAudioElement).volume = this.playback_volume;

            //attach listeners
            window.addEventListener('pointerdown', this.determineInstanceHasFocus);
            window.addEventListener('pointermove', this.doPlaybackDrag);
            window.addEventListener('pointerup', this.stopPlaybackDrag);
            window.addEventListener('resize', this.handleWindowResize);
            window.addEventListener('keydown', this.handleKeyboardEvent);
            document.addEventListener('visibilitychange', this.syncSliderAnimeAfterSuspend);
            (this.$refs.audio_element as HTMLAudioElement).addEventListener('timeupdate', this.updateCurrentPlaybackTime);
        },
        beforeUnmount(){

            //remove listeners
            window.removeEventListener('pointerdown', this.determineInstanceHasFocus);
            window.removeEventListener('pointermove', this.doPlaybackDrag);
            window.removeEventListener('pointerup', this.stopPlaybackDrag);
            window.removeEventListener('resize', this.handleWindowResize);
            window.removeEventListener('keydown', this.handleKeyboardEvent);
            document.removeEventListener('visibilitychange', this.syncSliderAnimeAfterSuspend);
            (this.$refs.audio_element as HTMLAudioElement).removeEventListener('timeupdate', this.updateCurrentPlaybackTime);
        },
    });
</script>