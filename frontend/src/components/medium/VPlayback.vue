<template>
    <div
        :class="[
            source_has_error ? 'border-red-700 dark:border-red-400' : 'border-theme-gray-2 dark:border-dark-theme-gray-2 shade-border-when-hover',
            'h-20 border rounded-lg  transition-colors text-center text-theme-black dark:text-dark-theme-white-2'
        ]"
    >
        <!--add @timeupdate at mounted(), not here, as beforeUnmount() cannot remove it, and it'll still fire after unmount-->
        <!--must add all calls in handleHasMetadata(), not here, since the Infinity duration is not fixed until then-->
        <!--@pause and @playing is 99% but not 100% reliable, e.g. during pause + source change-->
        <!--so together with playPlayback() + pausePlayback() + @playing + @pause, playback_paused is now 100% reliable-->
        <audio
            ref="audio_element"
            @loadedmetadata="[handleHasMetadata()]"
            @canplay="is_playback_buffering=false"
            @waiting="is_playback_buffering=true"
            @playing="playback_paused=false"
            @pause="playback_paused=true"
        ></audio>

        <div
            v-show="playbackHasError"
            class="w-full h-full flex items-center text-center text-red-700 dark:text-red-400"
        >
            <span class="w-full h-fit text-base">Oops! Recording unavailable.</span>
        </div>

        <!--
            ripples, slider, volume, play/pause, rate, timers
            @focusin works here, but not @focusout
        -->
        <div
            v-show="!playbackHasError"
            ref="playback_main"
            :class="[
                propHasAudioClipTone === true ? 'grid-cols-4' : 'grid-cols-3 pr-4',
                'h-full grid grid-rows-2'
            ]"
            @click="[updateInstanceLastInteracted()]"
            @pointerdown="[updateInstanceLastInteracted()]"
            @focusin="[updateInstanceLastInteracted()]"
        >

            <!--play/pause-->
            <!--must use click-->
            <!--because pointerdown doesn't tell browser that user has interacted with document for media.play()-->
            <div class="row-start-1 row-span-2 col-start-1 col-span-1 text-4xl relative p-2">
                <VActionText
                    @click="userTogglePlaybackPlayPause()"
                    @keydown.enter="userTogglePlaybackPlayPause()"
                    :propIsEnabled="!isProcessing"
                    propElement="button"
                    type="button"
                    
                    class="w-full h-full focus-visible:-outline-offset-2"
                >

                    <!--pt 1px to point right to the middle of slider-->
                    <!--show loading when still initialising-->
                    <div
                        v-show="!is_initialised_on_new_audio"
                        class="w-full h-full pt-[1px] flex items-center"
                    >
                        <VLoading
                            prop-element-size="l"
                            class="mx-auto"
                        />
                        <span class="sr-only">loading audio</span>
                    </div>

                    <!--can play/pause-->
                    <div
                        v-show="is_initialised_on_new_audio"
                        class="w-full h-full pt-[1px] flex items-center"
                    >
                        <FontAwesomeIcon
                            fixed-width
                            :icon="playback_paused ? 'fas fa-play' : 'fas fa-pause'"
                            class="mx-auto"
                        />
                        <span v-show="playback_paused" class="sr-only">
                            pause
                        </span>
                        <span v-show="!playback_paused" class="sr-only">
                            play
                        </span>
                    </div>

                    <span v-show="!isPlaybackReady">
                        <span class="sr-only">Cannot play, no recording loaded</span>
                    </span>
                </VActionText>
            </div>

            <!--ripples, slider, do left-2 right-2 m-auto if you want outermost knob to be within bounds-->
            <div
                class="h-12 row-start-1 row-span-1 col-start-2 col-span-2 relative"
            >

                <!--ripples-->
                <!--need inline CSS to prevent jolting from anime if without it-->
                <div
                    v-show="is_initialised_on_new_audio"
                    ref="canvas_ripples_container"
                    class="h-6 absolute top-4 left-2 right-2 pb-2"
                >
                    <canvas ref="canvas_ripples" class="w-full h-full mx-auto"></canvas>
                </div>

                <!--slider-->
                <!--not sure why, but when fixed, need to shift this a little lower-->
                <div
                    class="w-full h-10 absolute top-[0.54rem]"
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

                        <!--background-->
                        <div
                            :class="[
                                isPlaybackReady === true ? 'double-height-when-hover' : '',
                                'h-1 absolute left-0 right-0 bottom-2 m-auto transition-transform bg-theme-gray-3 dark:bg-dark-theme-gray-3'
                            ]"
                        ></div>

                        <!--moving playback elements-->
                        <!--cannot use class scale-x-0, it will lock the element and prevent animate's scaleX from applying-->
                        <div
                            ref="playback_slider_progress"
                            class="h-1 absolute bg-theme-lead dark:bg-dark-theme-lead left-0 right-0 bottom-2 m-auto origin-left"
                            style="transform:scaleX(0);"
                        ></div>
                        <!--cannot apply scale to knob for some reason-->
                        <div
                            ref="playback_slider_knob"
                            class="w-4 h-4 absolute bottom-0.5 m-auto rounded-full   bg-theme-black dark:bg-dark-theme-white-2"
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
                <div
                    v-show="isPlaybackReady"
                    class="row-start-1 row-span-1 col-start-1 col-span-1 relative text-xs sm:text-sm"
                >
                    <span class="sr-only">current duration</span>
                    <span class="absolute w-fit h-fit left-0 -top-2 bottom-0 m-auto">{{pretty_current_playback_time}}</span>
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
                            is_playback_volume_open ? 'h-32 z-10 bg-theme-light dark:bg-theme-dark border-theme-black dark:border-dark-theme-white-2' : 'h-full border-transparent',
                            'absolute w-full bottom-0 m-auto border-2 rounded-lg'
                        ]"
                        @pointerenter.stop="handlePlaybackVolumeHoverIn($event)"
                        @pointerleave.stop="handlePlaybackVolumeHoverOut($event)"
                    >

                        <!--volume button-->
                        <VActionText
                            @pointerdown="toggleMute(false)"
                            @keydown.enter="toggleMute(true)"
                            propElement="button"
                            type="button"
                            
                            class="w-full h-[2.1875rem] absolute bottom-0 focus-visible:-outline-offset-2 focus-visible:outline-1"
                        >
                            <div
                                :class="[
                                    is_playback_volume_open ? '-rotate-90' : 'rotate-0',
                                    'flex w-full h-full relative transition-transform'
                                ]"
                            >
                                <FontAwesomeIcon v-show="isMuted" icon="fas fa-volume-xmark" class="absolute w-0 h-0 inset-0 m-auto"/>
                                <FontAwesomeIcon v-show="isLowVolume" icon="fas fa-volume-low" class="absolute w-0 h-0 inset-0 m-auto"/>
                                <FontAwesomeIcon v-show="isHighVolume" icon="fas fa-volume-high" class="absolute w-0 h-0 inset-0 m-auto"/>
                            </div>

                            <span v-show="isMuted" class="sr-only">
                                unmute to bring volume back to {{ getBackupVolume }}
                            </span>
                            <span v-show="!isMuted" class="sr-only">
                                current volume is {{ getCurrentVolume }}, click to mute
                            </span>
                            <span class="sr-only">
                                when volume menu is open, keyboard up and down keys can also adjust volume
                            </span>
                        </VActionText>

                        <!--volume menu-->
                        <!--h-22, so +h-10 of button, we can set content size at h-32-->
                        <VSliderYSmall
                            v-show="is_playback_volume_open"
                            ref="volume_slider"
                            :propSliderValue="playback_volume"
                            @hasNewSliderValue="changePlaybackVolume($event)"
                            @startDragSliderValue="handleVolumeStartDrag()"
                            @stopDragSliderValue="handleVolumeStopDrag()"
                            class="w-full h-[5.5rem] absolute left-0 right-0 bottom-10 m-auto pt-5 pb-1"
                        >
                            <span class="sr-only">vertical volume box</span>
                        </VSliderYSmall>
                    </div>
                </div>

                <!--total duration-->
                <div
                    v-show="isPlaybackReady"
                    class="row-start-1 row-span-1 col-start-3 col-span-1 relative text-xs sm:text-sm"
                >
                    <span class="absolute w-fit h-fit right-0 -top-2 bottom-0 m-auto">
                        <span class="sr-only">total duration</span>
                        {{pretty_playback_duration}}
                    </span>
                </div>
            </div>

            <div
                class="row-span-2 col-span-1 relative"
                v-if="propHasAudioClipTone"
            >
                <div class="text-2xl absolute w-fit h-fit left-0 right-0 top-0 bottom-0 m-auto">
                    <span
                        v-if="propAudioClip !== null"
                        class="has-emoji"
                    >
                        {{ propAudioClip.audio_clip_tone.audio_clip_tone_symbol }}
                        <span class="sr-only">{{ propAudioClip.audio_clip_tone.audio_clip_tone_name }}</span>
                    </span>
                    <FontAwesomeIcon v-else icon="far fa-face-meh-blank" class="text-2xl"/>
                </div>
            </div>
        </div>
    </div>
</template>



<script setup lang="ts">
    import VSliderYSmall from '@/components/small/VSliderYSmall.vue';
    import VActionText from '@/components/small/VActionText.vue';
    import VLoading from '@/components/small/VLoading.vue';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faFaceMehBlank } from '@fortawesome/free-regular-svg-icons/faFaceMehBlank';
    import { faPlay } from '@fortawesome/free-solid-svg-icons/faPlay';
    import { faPause } from '@fortawesome/free-solid-svg-icons/faPause';
    import { faVolumeXmark } from '@fortawesome/free-solid-svg-icons/faVolumeXmark';
    import { faVolumeLow } from '@fortawesome/free-solid-svg-icons/faVolumeLow';
    import { faVolumeHigh } from '@fortawesome/free-solid-svg-icons/faVolumeHigh';

    library.add(faFaceMehBlank, faPlay, faPause, faVolumeXmark, faVolumeLow, faVolumeHigh);
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import { prettyDuration, getRandomUUID, drawCanvasRipples } from '@/helper_functions';
    import { animate, utils } from 'animejs';
    import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';
    import AudioClipsTypes from '@/types/AudioClips.interface';
    // import VSliderTypes from '@/types/values/VSlider';
    import { useVPlaybackStore } from '@/stores/VPlaybackStore';
    import { useRedrawCanvasesStore } from '@/stores/RedrawCanvasesStore';
    import { notify } from '@/wrappers/notify_wrapper';

    export default defineComponent({
        data(){
            return {
                source_has_error: false,

                vplayback_store: useVPlaybackStore(),
                redraw_canvases_store: useRedrawCanvasesStore(),
                instance_uuid: "",    //uuid, to identify between multiple VPlayback instances, and to manage focus
                redraw_canvases_store_index: null as number|null,

                pretty_current_playback_time: '00:00',
                pretty_playback_duration: '00:00',
                playback_paused: true,
                play_promise: null as Promise<void>|null,
                main_anime: null as InstanceType<typeof animate> | null,   //to store animePlaybackStates() anime

                is_playback_slider_ready: false,
                is_playback_attached: false,

                is_playback_buffering: false,
                is_playback_slider_processing: false,
                is_playback_attaching: false,

                playback_slider_value: 0,
                is_playback_slider_drag: false,
                playback_slider_dimension: null as DOMRect | null,
                playback_slider_knob_anime: null as InstanceType<typeof animate> | null, //we play/pause instead of new animate() for best results
                playback_slider_progress_anime: null as InstanceType<typeof animate> | null, //we play/pause instead of new animate() for best results
                stay_paused_on_drag: true,  //if user pauses, then navigating will not auto-play

                playback_rate: 1,   //allows 0 to 2, but we handle 0.5, 1, 1.5
                playback_volume: 1, //always changes, accepts 0 to 1
                playback_volume_backup_never_0: 1,  //only changes when appropriate, accepts >0 to 1
                is_playback_volume_slider_dragging: false,
                is_playback_volume_slider_hovering: false,

                is_playback_speed_options_open: false,

                //handleHasMetadata() makes this true, but only when propIsOpen is true
                //else, the related functions don't run until propIsOpen is true
                //resets on new audio
                is_initialised_on_new_audio: false,

                instance_has_focus: false,
                
                //everything else will auto-close volume menu
                //except for hover
                //always use openPlaybackVolume() and closePlaybackVolume() to ensure timeout is synced
                is_playback_volume_open: false,
                autoclose_playback_volume_timeout: null as number|null,

                playback_states: ['initiate', 'recording', 'attaching', 'can_play', 'loading'],

                fastest_anime_duration_ms: 100, //to change anime durations easily

                //fix for resize firing adjustment too quickly, leaving us with inaccurate dimension
                window_resize_timeout: null as number|null,
            };
        },
        emits: [
            'isReadyToPlay', 'isProcessing',
        ],
        props: {
            propAudioClip: {
                type: Object as PropType<AudioClipsAndLikeDetailsTypes|AudioClipsTypes|null>,
                default: null
            },
            propAudio: {    //used when receiving from VRecorder
                type: Object as PropType<Blob|File|null>,
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
            propBucketQuantity: {
                type: Number,
                required: true
            },
            propHasAudioClipTone: {
                type: Boolean,
                default: true,
            },
        },
        watch: {
            is_playback_buffering(new_value){

                if(new_value === true){

                    //'if' statement should help prevent race condition
                    if(this.playback_paused === false){

                        this.playback_slider_knob_anime.pause();
                        this.playback_slider_progress_anime.pause();
                    }

                }else{

                    //'if' statement should help prevent race condition
                    if(this.playback_paused === false && this.playback_slider_value < 1){

                        this.playback_slider_knob_anime.play();
                        this.playback_slider_progress_anime.play();
                    }
                }
            },
            propAudio(new_value){

                this.is_initialised_on_new_audio = false;

                this.attachAudioToPlayback(new_value);

                //apply focus on source change
                this.updateInstanceLastInteracted();
            },
            propAudioClip(
                new_value:AudioClipsTypes|AudioClipsAndLikeDetailsTypes|null,
                old_value:AudioClipsTypes|AudioClipsAndLikeDetailsTypes|null,
            ){

                //reminder that with v-if and props already supplied, first time will not trigger watchers

                //store where the previous audio was stopped
                //must do this before <audio> changes via attachAudioToPlayback()
                if(old_value !== null){

                    this.storeCurrentAudioClipLastStopped(old_value);
                }

                //reset

                this.is_initialised_on_new_audio = false;
                this.pretty_current_playback_time = '00:00';
                this.pretty_playback_duration = '00:00';
                this.playback_slider_value = 0;

                if(
                    this.playback_slider_knob_anime !== null &&
                    this.playback_slider_progress_anime !== null)
                {

                    this.playback_slider_knob_anime.completed = false;
                    this.playback_slider_progress_anime.completed = false;

                    this.playback_slider_knob_anime.seek(0);
                    this.playback_slider_progress_anime.seek(0);
                }

                if(new_value === null){

                    this.is_initialised_on_new_audio = true;
                    return;
                }

                //get where new audio was stopped, if any

                //attach new audio
                this.attachAudioToPlayback(new_value.audio_file);

                //apply focus on source change
                this.updateInstanceLastInteracted();
            },
            propIsRecording(new_value){

                //started recording
                if(new_value === true){

                    if(this.playback_paused === false){

                        (async ()=> {

                            await this.pausePlayback();
                            this.updatePlaybackSliderValue();
                        })();
                    }
                }
            },
            propIsOpen(new_value){

                //if is open, i.e. rendered
                if(new_value === true){

                    //ok to run this often, since it does nothing if dimension is the same
                    this.$nextTick(async () => {

                        if(this.is_initialised_on_new_audio === false){

                            this.handleHasMetadata();

                        }else if(this.adjustPlaybackSliderDimension() === true && this.isPlaybackReady === true){

                            this.createPlaybackSliderAnimate();
                            await this.syncSliderAnimeAfterSuspend();
                            this.drawRipples();
                        }
                    });

                }else if(new_value === false && this.playback_paused === false){
                    
                    //if is playing when close, pause playback
                    (async () => {

                        await this.pausePlayback();
                        this.updatePlaybackSliderValue();
                    })();
                }
            },
        },
        computed: {
            isMuted() : boolean {

                return this.playback_volume === 0;
            },
            getCurrentVolume() : string {

                return (this.playback_volume * 100).toString() + "%";
            },
            getBackupVolume() : string {

                return (this.playback_volume * 100).toString() + "%";
            },
            isPlaybackReady() : boolean {

                const is_playback_ready = (
                    this.is_initialised_on_new_audio === true &&
                    this.playbackHasError === false &&
                    this.propIsOpen === true &&
                    this.propAudioVolumePeaks.length > 0 &&
                    this.propAudioVolumePeaks.length === this.propBucketQuantity &&
                    (this.propAudio !== null || this.propAudioClip !== null) &&
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

                return this.instance_uuid === this.vplayback_store.getLastInteractedVPlaybackUUID;
            },
            isLowVolume() : boolean {

                return this.isMuted === false && this.playback_volume > 0 && this.playback_volume <= 0.5;
            },
            isHighVolume() : boolean {

                return this.isMuted === false && this.playback_volume > 0.5 && this.playback_volume <= 1;
            },
            playbackHasError() : boolean {

                return this.source_has_error === true;
            },
        },
        methods: {
            setInitialPlaybackSliderValue() : void {
                
                //initial
                this.playback_slider_value = 0;

                if(this.propAudioClip === null){

                    return;
                }

                const last_stopped_s = this.vplayback_store.getAudioClipLastStoppedS(this.propAudioClip.id);

                //not stored
                if(last_stopped_s === null){

                    return;
                }

                const total_duration_s = (this.$refs.audio_element as HTMLAudioElement).duration;

                //restore slider value
                //as long as both this function and StoreCurrentAudioClipLastStopped() use <audio>.currentTime,
                //value should always be <= 1
                let new_value = Number((last_stopped_s / total_duration_s).toFixed(3));

                this.playback_slider_value = new_value;
            },
            async storeCurrentAudioClipLastStopped(audio_clip:AudioClipsTypes|AudioClipsAndLikeDetailsTypes) : Promise<void> {

                //call this after pause on source change, but before source change happens

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);

                if(
                    audio_clip === null || audio_element.src === ''
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
                this.vplayback_store.addAudioClipLastStoppedS(audio_clip.id, current_time_s);
            },
            async updateInstanceLastInteracted() : Promise<void> {

                //any actions taken to any VPlayback instance will update store
                //so that handleKeyboardEvent() goes through for "last interacted VPlayback" only
                this.vplayback_store.updateLastInteractedVPlaybackUUID(this.instance_uuid);

                this.instance_has_focus = true;
            },
            async determineInstanceHasFocus(e:PointerEvent) : Promise<void> {

                //we need this with pointerdown at window to detect focus lost
                //because @focusout doesn't work

                this.instance_has_focus = (this.$refs.playback_main as HTMLElement).contains(e.target as Node);
            },
            handleInitialAutoplay() : void {

                //auto-play if desired, condition checking is also already handled at this stage

                if(this.vplayback_store.getCanAutoplay === false){

                    return;
                }

                if(this.playback_slider_value < 1){

                    this.playPlayback();
                }
            },
            async handlePlaybackVolumeHoverIn(e:PointerEvent) : Promise<void> {

                //don't handle hover if not mouse, since hover behaviour is meant for mouse only
                //otherwise, touch triggers mouseenter and mouseleave undesirably
                if(e.pointerType !== "mouse"){

                    return;
                }

                this.is_playback_volume_slider_hovering = true;
                this.openPlaybackVolume();
            },
            async handlePlaybackVolumeHoverOut(e:PointerEvent) : Promise<void> {

                //don't handle hover if not mouse, since hover behaviour is meant for mouse only
                //otherwise, touch triggers mouseenter and mouseleave undesirably
                if(e.pointerType !== "mouse"){

                    return;
                }

                this.is_playback_volume_slider_hovering = false;

                if(this.is_playback_volume_slider_dragging === false){

                    this.closePlaybackVolume(false);
                }
            },
            handleVolumeStartDrag() : void {

                this.is_playback_volume_slider_dragging = true;
                this.savePlaybackVolumeLocalStorage(this.playback_volume);
                this.openPlaybackVolume();
            },
            handleVolumeStopDrag() : void {

                this.is_playback_volume_slider_dragging = false;
                this.savePlaybackVolumeLocalStorage(this.playback_volume);

                if(this.is_playback_volume_slider_hovering === false){

                    this.closePlaybackVolume(false);
                }
            },
            toggleMute(show_volume:boolean) : void {

                if(this.is_playback_volume_slider_dragging === true){

                    return;
                }

                if(this.playback_volume === 0){

                    //unmute
                    this.changePlaybackVolume(this.playback_volume_backup_never_0);
                    this.savePlaybackVolumeLocalStorage(this.playback_volume_backup_never_0);

                }else{

                    //mute
                    this.changePlaybackVolume(0);
                    this.savePlaybackVolumeLocalStorage(0);
                }

                if(show_volume === true){

                    this.openPlaybackVolume();
                    this.closePlaybackVolume();
                }
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
            keyboardAdjustVolume(add_or_sub_value:number) : void {

                //pass values like 0.2 to add, -0.2 to sub

                if(add_or_sub_value < -1 || add_or_sub_value > 1){

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

                this.openPlaybackVolume();

                this.changePlaybackVolume(new_playback_volume);
                this.savePlaybackVolumeLocalStorage(new_playback_volume);

                this.closePlaybackVolume();
            },
            handleKeyboardEvent(event:KeyboardEvent) : void {

                //FYI, some keyup events are too late for .preventDefault(), so they use keydown

                //ensure this won't be used during user input
                const audio_clip_target = (event.target as Node);

                if(audio_clip_target.nodeName === "INPUT" || audio_clip_target.nodeName === "TEXTAREA"){

                    return;
                }

                //keyCode is deprecated, use .key
                    //.code is different on different types of keyboards, but .key will be consistent
                //https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/key
                switch(event.key){

                    case 'ArrowLeft':

                        if(this.isPlaybackReady === true && this.isInstanceLastInteracted === true){

                            //go backwards playback
                            this.skipPlayback(-5);
                        }

                        break;

                    case 'ArrowRight':

                        if(this.isPlaybackReady === true && this.isInstanceLastInteracted === true){

                            //go forward playback
                            this.skipPlayback(5);
                        }

                        break;

                    case ' ':

                        if(this.isPlaybackReady === true && this.isInstanceLastInteracted === true){

                            //space also acts like 'enter', so we prevent that
                            event.preventDefault();

                            //play/pause
                            this.userTogglePlaybackPlayPause();
                        }

                        break;

                    case 'm':

                        if(this.isInstanceLastInteracted === true){

                            //mute/unmute
                            //when for recording, no volume option
                            //we use localStorage for backup value from mute to unmute
                            this.toggleMute(true);
                        }

                        this.instance_has_focus = true;

                        break;

                    case 'ArrowUp':

                        if(this.isInstanceLastInteracted === true && this.instance_has_focus === true){


                            event.preventDefault();
                            this.keyboardAdjustVolume(0.2);
                        }

                        break;

                    case 'ArrowDown':

                        if(this.isInstanceLastInteracted === true && this.instance_has_focus === true){

                            event.preventDefault();
                            this.keyboardAdjustVolume(-0.2);
                        }

                        break;

                    case 'Escape':

                        if(this.instance_has_focus === true){

                            this.instance_has_focus = false;
                        }

                        break;

                    default:

                        break;
                }
            },
            async doRedraw() : Promise<void> {

                //during hot reload (change html/css --> save --> DOM changes without refresh), JS parts get slightly buggy
                //e.g. all playback skips just lead to seek(0)
                //simply do a manual refresh

                //we need to use timeout because resize audio_clip randomly fires before actual dimension is fixed

                this.window_resize_timeout !== null ? clearTimeout(this.window_resize_timeout) : null;

                const handler = async ()=>{

                    //for audio_clip listener 'resize', this recreates slider anime and syncs it
                    this.adjustPlaybackSliderDimension();

                    //redraw canvas
                    this.drawRipples();

                    if(this.isPlaybackReady === true && isNaN((this.$refs.audio_element as HTMLAudioElement).duration) === false){
                        
                        this.createPlaybackSliderAnimate();
                        await this.syncSliderAnimeAfterSuspend();
                    }

                    //redraw canvas
                }

                //run once, i.e. immediately
                await handler();

                //run this delayed one next, in case immediate call had fired before dimension is fixed
                this.window_resize_timeout = window.setTimeout(async ()=>{
                    await handler();
                }, 200);
            },
            async syncSliderAnimeAfterSuspend() : Promise<void> {

                //we need this because anime's engine.pauseOnDocumentHidden=false does not work
                //basically just to reposition slider anime to playback, else it doesn't do that
                //must call pause() first, else seek() is inaccurate

                if(this.isPlaybackReady === false){

                    return;
                }

                if(
                    document.visibilityState === 'visible' &&
                    this.playback_slider_knob_anime !== null && this.playback_slider_progress_anime !== null
                ){

                    let resume_later = null;

                    if(this.playback_paused === false){

                        await this.pausePlayback();
                        resume_later = true;
                    }

                    this.updatePlaybackSliderValue();
                    this.seekPlayback();

                    if(resume_later === true){

                        await this.playPlayback();
                    }
                }
            },
            createPlaybackSliderAnimate() : void {

                //to be called during handleHasMetadata(), window resize, changePlaybackRate()
                //we can then use .play/.pause/.seek
                //expects to already have accurate this.playback_slider_value

                //sometimes, immediate mounting and unmounting causes race condition
                    //e.g. store has reply choice --> open reply page --> load VPlayback --> immediately expire

                if(this.playback_slider_dimension === null){

                    return;
                }

                //states
                this.is_playback_slider_ready = false;
                this.is_playback_slider_processing = true;

                //remove
                utils.remove([
                    this.$refs.playback_slider_knob,
                    this.$refs.playback_slider_progress
                ]);
                this.playback_slider_knob_anime = null;
                this.playback_slider_progress_anime = null;

                //calculate starting point
                const ending_translateX = (this.playback_slider_dimension as DOMRect).width;

                //calculate duration based on playback_rate
                //note that when <audio> playbackRate changes, .duration is still the same
                const anime_duration = ((this.$refs.audio_element as HTMLAudioElement).duration / this.playback_rate) * 1000;

                //create new anime
                this.playback_slider_knob_anime = animate(this.$refs.playback_slider_knob, {
                    ease: 'linear',
                    autoplay: false,
                    loop: false,
                    duration: anime_duration,
                    translateX: [
                        '0px',
                        ending_translateX.toString() + 'px'
                    ],
                });
                this.playback_slider_progress_anime = animate(this.$refs.playback_slider_progress, {
                    ease: 'linear',
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
                //use not only during 'resize' audio_clip, but when playback_states[2] is ready
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
            async startPlaybackDrag() : Promise<void> {

                if(this.isPlaybackReady === false){

                    return;
                }

                this.is_playback_slider_drag = true;

                if(this.playback_paused === false){

                    await this.pausePlayback();
                    this.updatePlaybackSliderValue();
                }

                //fixed: drag to end --> .completed=true --> .seek() --> .play() starts from 0
                this.playback_slider_knob_anime.completed = false;
                this.playback_slider_progress_anime.completed = false;
            },
            doPlaybackDrag(e:PointerEvent) : void {

                if(this.is_playback_slider_drag === true && this.playback_slider_dimension !== null){

                    //can use clientX, screenX, pageX
                    //clientY seems to work best
                    const user_x = e.clientX;

                    if(user_x >= this.playback_slider_dimension.left && user_x <= this.playback_slider_dimension.right){

                        //will always be 0 to 1
                        this.playback_slider_value = (user_x - this.playback_slider_dimension.left) / this.playback_slider_dimension.width;

                    }else if(user_x < this.playback_slider_dimension.left){

                        this.playback_slider_value = 0;

                    }else if(user_x > this.playback_slider_dimension.right){

                        this.playback_slider_value = 1;
                    }

                    this.seekPlayback();
                }
            },
            async stopPlaybackDrag() : Promise<void> {

                if(this.is_playback_slider_drag === false){

                    return;
                }

                //when user has dragged to end, will fix .ended=false issue
                this.seekPlayback();
                this.endPlaybackTruly();

                if(this.playback_slider_value < 1 && this.stay_paused_on_drag === false){

                    await this.playPlayback();
                }

                this.is_playback_slider_drag = false;
            },
            endPlaybackTruly() : void {

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);

                if(audio_element.src === ''){

                    return;
                }

                if(audio_element.paused === true && this.playback_slider_value === 1 && audio_element.ended === false){

                    //on next play, anime starts from 0
                    this.playback_slider_knob_anime.seek(this.playback_slider_knob_anime.duration);
                    this.playback_slider_progress_anime.seek(this.playback_slider_progress_anime.duration);
                    this.playback_slider_knob_anime.completed = true;
                    this.playback_slider_progress_anime.completed = true;

                    //edge case: seeked to end, but .ended still false
                    //we use .play() and muted=true to fix, while not touching anything else

                    //to prevent button from flashing during "already ended" + endPlaybackTruly(),
                    //manipulate playback_paused to stay paused
                    //if original state is playing, .finally() will revert to it

                    audio_element.muted = true;
                    const original_playback_paused = this.playback_paused;
                    this.playback_paused = true;
                    this.play_promise = audio_element.play().finally(()=>{

                        this.play_promise = null;
                        this.playback_paused = original_playback_paused;
                    });

                //as of 2023-08-17, this block is important
                //doing .completed=false for every seekPlayback() didn't work consistently
                }else if(audio_element.ended === false){

                    this.playback_slider_knob_anime.completed = false;
                    this.playback_slider_progress_anime.completed = false;
                }
            },
            seekPlayback() : void {

                //expects playback_slider_value to be float 0 to 1

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);

                //don't rely on playback_paused here, as there are some situations where
                //you need this function to trigger the change for it, not beforehand
                if(audio_element.paused === false && this.playback_paused === false){

                    return;
                }
                //duration is the same regardless of playbackRate
                const jumped_anime_duration = this.playback_slider_value * this.playback_slider_knob_anime.duration;
                //duration changes when playbackRate changes
                const jumped_playback_duration = this.playback_slider_value * audio_element.duration;

                //handle slider aesthetics
                //need to set .completed to false, else .play() starts from 0 if it has finished before
                //must be in ms

                this.playback_slider_knob_anime.seek(jumped_anime_duration);
                this.playback_slider_progress_anime.seek(jumped_anime_duration);

                //handle <audio>
                audio_element.currentTime = jumped_playback_duration;

                //handle timer
                this.updateCurrentPlaybackTime();
            },
            async skipPlayback(seconds=0) : Promise<void> {

                //+x for forward, -x for backward

                //do this instead of relying on :disabled, as :disabled makes sliders bug out
                if(seconds === 0 || this.isPlaybackReady === false){

                    return;
                }

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);

                if(this.playback_paused === false){

                    await this.pausePlayback();
                }

                let updated_time = audio_element.currentTime + seconds;

                if(updated_time < 0){

                    updated_time = 0;

                }else if(updated_time > audio_element.duration){

                    updated_time = audio_element.duration;
                }

                //update slider value
                this.playback_slider_value = updated_time / audio_element.duration;

                //adjust
                this.seekPlayback();

                if(this.stay_paused_on_drag === false && this.playback_slider_value < 1){

                    //set .completed back to false to handle "skipped to end --> endPlaybackTruly() --> skipped left"
                    this.playback_slider_knob_anime.completed = false;
                    this.playback_slider_progress_anime.completed = false;

                    //resume if originally playing
                    await this.playPlayback();

                }else{

                    this.endPlaybackTruly();
                }
            },
            updatePlaybackSliderValue() : void {

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);

                if(isNaN(audio_element.duration) === true){

                    return;
                }

                this.playback_slider_value = audio_element.currentTime / audio_element.duration;
            },
            async updateCurrentPlaybackTime() : Promise<void> {

                const target = (this.$refs.audio_element as HTMLAudioElement);

                //timer
                this.pretty_current_playback_time = prettyDuration(target.currentTime);
            },
            async changePlaybackVolume(new_value:number) : Promise<void> {

                this.playback_volume = new_value;
                (this.$refs.audio_element as HTMLAudioElement).volume = new_value;
            },
            async savePlaybackVolumeLocalStorage(new_value:number) : Promise<void> {

                if(new_value === 0){

                    localStorage.setItem('is_muted', JSON.stringify(true));

                }else{

                    localStorage.setItem('is_muted', JSON.stringify(false));
                    localStorage.setItem('playback_volume_backup_never_0', JSON.stringify(new_value));
                    this.playback_volume_backup_never_0 = new_value;
                }
            },
            async changePlaybackRate(new_value:number) : Promise<void> {

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);

                if(new_value === this.playback_rate || audio_element.src === ''){

                    return;
                }

                //consider playback_paused when this rate change happened
                const resume_later = !this.playback_paused;

                //pause to make changes, and to update playback_slider_value
                await this.pausePlayback();
                this.updatePlaybackSliderValue();

                //update values
                //note that on every new file loaded into <audio>, playbackRate is reset
                //attachAudioToPlayback() will handle this inconvenience
                audio_element.playbackRate = new_value;
                this.playback_rate = new_value;
                localStorage.setItem('playback_rate', JSON.stringify(new_value));

                //adjust anime
                this.createPlaybackSliderAnimate();
                this.playback_slider_knob_anime.seek(this.playback_slider_value * this.playback_slider_knob_anime.duration);
                this.playback_slider_progress_anime.seek(this.playback_slider_value * this.playback_slider_progress_anime.duration);

                //play if was playing
                if(resume_later === true){

                    await this.playPlayback();
                }
            },
            async togglePlaybackSpeedOptions() : Promise<void> {
                
                this.is_playback_speed_options_open = !this.is_playback_speed_options_open;
            },
            async playPlayback() : Promise<void> {

                //using anime.play/pause instead of remove+create prevents slight off-position on second play
                //our new anime position is already settled by seekPlayback()

                //recommended HTML native media workflow:
                    //you can do as many .play() as you want, as it is also async (hence no check for paused=true here)
                    //be sure to handle catch for .play()

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);

                const handler = ()=>{

                    //although redundant, we put audio_element.muted=false here to guarantee it
                    //as there has been a rare instance where playback had no audio unintentionally until the next replay
                    audio_element.muted = false;
                    this.playback_paused = false;

                    this.stay_paused_on_drag = false;

                    //fixed: playback ends --> play --> knob and progress still at end
                    if(this.playback_slider_knob_anime.completed === true && this.playback_slider_progress_anime.completed === true){

                        this.playback_slider_knob_anime.restart();
                        this.playback_slider_progress_anime.restart();
                    }

                    if(this.is_playback_buffering === false){

                        this.playback_slider_knob_anime.play();
                        this.playback_slider_progress_anime.play();
                    }
                };

                //promise
                this.play_promise = audio_element.play().then(()=>{

                    handler();

                }).catch(()=>{

                    audio_element.pause();

                }).finally(()=>{

                    this.play_promise = null;
                });
            },
            async pausePlayback() : Promise<void> {

                //if playing, call this before drag, then do playPlayback() once done
                //done at startPlaybackDrag() and stopPlaybackDrag()

                //don't be alarmed at the fact that this is called 3 times on first load
                    //attach audio at slider 1 --> pause(0) --> endProperly --> @ended=pause(1) --> endProperly -->
                    //@ended=pause(2), but .ended=True --> stop

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);

                const handler = ()=>{

                    if(this.playback_paused === true){

                        return;
                    }

                    //also recalculate slider value
                    audio_element.pause();
                    this.playback_paused = true;

                    this.playback_slider_knob_anime.pause();
                    this.playback_slider_progress_anime.pause();
                };

                if(this.play_promise !== null){

                    await this.play_promise.then(()=>{

                        handler();
                    });

                }else{

                    handler();
                }
            },
            async userTogglePlaybackPlayPause() : Promise<void> {

                //we let everything stay at the end if playback truly ended
                //reset is only triggered on next play

                //do this instead of relying on :disabled, as :disabled makes sliders bug out
                if(this.isPlaybackReady === false){

                    notify({
                        type: 'generic',
                        title: 'No recording loaded',
                        text: '',
                        icon: {'font_awesome': 'far fa-face-meh-blank'},
                    }, 2000);

                    return;
                }

                //edge case of dragging + space
                //cancel drag if so, while stopPlaybackDrag() auto-plays for us
                if(this.is_playback_slider_drag === true){
                    
                    await this.stopPlaybackDrag();

                    //if we don't return here, we get "play() interrupted by pause()"
                    return;
                }

                //check if playback is not playing
                //stay_paused_on_drag must be here to record user's manual pausing
                if(this.playback_paused === true){

                    await this.playPlayback();
                    this.stay_paused_on_drag = false;

                    //if we have other instances, we pause other instances on play
                    if(this.vplayback_store.active_vplayback_uuids.length > 1){

                        this.vplayback_store.triggerPause(false);
                    }

                }else{

                    await this.pausePlayback();
                    this.updatePlaybackSliderValue();
                    this.endPlaybackTruly();
                    this.stay_paused_on_drag = true;
                }
            },
            async attachAudioToPlayback(new_audio:string|Blob|File) : Promise<void> {

                //reset
                this.source_has_error = false;

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);

                //pause first if playing
                //we don't create new slider here, but at <audio>'s @loadedmetadata, as its .duration is only available then
                if(this.playback_paused === false){

                    await this.pausePlayback();
                }

                //states
                this.is_playback_attached = false;
                this.is_playback_attaching = true;

                if(audio_element.hasAttribute('src') && audio_element.src.length > 0){

                    //destroy URL.createObjectURL() instance to free from memory, then stop loading, no checks needed
                    //https://developer.mozilla.org/en-US/docs/Web/Guide/Audio_and_video_delivery#other_tips_for_audiovideo
                    //when this happens, it also triggers @ended audio_clip
                    URL.revokeObjectURL(audio_element.src);
                    audio_element.removeAttribute('src');
                    audio_element.load();
                }

                if(typeof(new_audio) === 'string'){

                    //attach audio from URL origin
                    audio_element.setAttribute('src', new_audio);

                }else{

                    //attach audio from Blob/File origin
                    audio_element.setAttribute('src', URL.createObjectURL(new_audio));
                }

                //load new source
                audio_element.load();

                //on every new file loaded into <audio>, playbackRate is reset by default
                //this is the fix
                audio_element.playbackRate = this.playback_rate;

                //states
                this.is_playback_attached = true;
                this.is_playback_attaching = false;
            },
            handleHasMetadata() : void {

                //@loadedmetadata fires when <audio>.duration is finally available

                const audio_element = (this.$refs.audio_element as HTMLAudioElement);

                //when NaN, it's because this isn't called by @loadedmetadata, i.e. VPlayback loaded as empty
                if(audio_element === null || this.propIsOpen === false || isNaN(audio_element.duration) === true){

                    return;
                }

                //there's a bug that gives us 'Infinity', had we not used fixWebmDuration
                //this is because the browser does not insert duration metadata into our webm
                //this is how we fix it, which still applies after the fixWebmDuration solution
                //https://stackoverflow.com/a/69512775

                const handler = () => {

                    audio_element.currentTime = 0;
                    audio_element.removeEventListener('timeupdate', handler);

                    //mm:ss
                    //only for duration display we will use floor
                    this.pretty_playback_duration = prettyDuration(
                        audio_element.duration
                    );

                    this.adjustPlaybackSliderDimension();
                    this.drawRipples();
                    this.createPlaybackSliderAnimate();
                    this.setInitialPlaybackSliderValue();
                    this.seekPlayback();
                    //must call this in case ended audio is loaded in
                    this.endPlaybackTruly();
                    this.handleInitialAutoplay();

                    this.is_initialised_on_new_audio = true;
                };

                audio_element.currentTime = 1e101;
                audio_element.addEventListener('timeupdate', handler);

                //don't try to access (this.$refs.audio_element as HTMLAudioElement).duration precisely here, as something is async
                //you'll get 0, but if you check via watch, the value does change
                //put your code in handler instead if you need to run something else
            },
            drawRipples() : void {

                this.$nextTick(()=>{

                    drawCanvasRipples(
                        (this.$refs.canvas_ripples_container as HTMLElement).getBoundingClientRect(),
                        this.$refs.canvas_ripples as HTMLCanvasElement,
                        this.propAudioVolumePeaks,
                        'bottom',
                    );
                });
            },
            setPlaybackSourceHasError() : void {

                this.source_has_error = true;
            },
        },
        beforeMount(){

            if(this.propAudio === null && this.propAudioClip === null){

                this.is_initialised_on_new_audio = true;
            }

            this.vplayback_store.$onAction(({
                name,
                after,
            })=>{

                after(()=>{

                    //pause all VPlayback instances
                    if(
                        name === 'triggerPause' &&
                        (
                            this.vplayback_store.can_pause_trigger_affect_last_interacted_vplayback === true ||
                            (
                                this.vplayback_store.can_pause_trigger_affect_last_interacted_vplayback === false &&
                                this.isInstanceLastInteracted === false
                            )
                        )
                    ){

                        (async ()=>{
                            await this.pausePlayback();
                            this.updatePlaybackSliderValue();
                        })();
                    }
                });
            });
        },
        mounted(){

            // Note on expected playback issue:
                // At localhost, on first-time media serve (i.e. not from cache), Django is missing a few headers.
                // Some or all of these headers are required to do .currentTime properly:
                // Content-Range, Accept-Ranges, Content-Length, Content-Type
                // Request status is also 200, when it should be 206.
            // What the issue looks like:
                // First time load --> missing headers --> play until end -->
                // trying to do <audio>.currentTime=x always becomes <audio>.currentTime=0.
            // Solutions:
                // To fix at localhost, just refresh page and let browser serve from cache. Everything is correct if from cache.
                // To fix at production, specify some settings at web server. It's supposedly easy.
                // If using AWS CloudFront, the problem seems non-existent.
                // Links that will/might help:
                // https://stackoverflow.com/q/39051206
                // https://stackoverflow.com/q/157318
                // https://stackoverflow.com/q/52137963

            //generate uuid for this component instance
            this.instance_uuid = getRandomUUID();

            //initial state
            this.$emit('isProcessing', false);

            //add uuid to list of active uuids
            //we then always focus on first UUID, useful when we have multiple VPlayback
            this.vplayback_store.addActiveVPlaybackUUID(this.instance_uuid);
            this.vplayback_store.focusFirstVPlaybackUUID();

            //handle when propAudioClip already exists on mounted, which means it's from API
            if(this.propAudioClip !== null && this.propAudioClip.audio_file.length > 0){

                this.attachAudioToPlayback(this.propAudioClip.audio_file);
            }

            //handle rate and volume differently
            if(this.propIsForRecording === true){

                //we set rate to 1 and volume to max, and hide them
                //there is no need for them if intended for recording, for best feedback
                this.playback_rate = 1;
                this.playback_volume = 1;
                this.playback_volume_backup_never_0 = 1;

            }else{

                //handle localStorage
                //invoking them gives you get() value, so const would not behave like a reference

                //rate
                if(localStorage.getItem('playback_rate') === null){
                    localStorage.setItem('playback_rate', JSON.stringify(1));
                }

                //volume
                //always save >0, never 0
                //starts as 1, so volume changes are saved on touch audio_clips, i.e. mobile
                //else, unmute must always be 1, which is bad for users using touch but are able to adjust volume
                if(localStorage.getItem('playback_volume_backup_never_0') === null){
                    localStorage.setItem('playback_volume_backup_never_0', JSON.stringify(1));
                }

                //when muted, this is true, but playback_volume is still >0
                if(localStorage.getItem('is_muted') === null){
                    localStorage.setItem('is_muted', JSON.stringify(true));
                }

                //set values
                this.playback_rate = parseFloat(JSON.parse(localStorage.getItem('playback_rate')!));
                this.playback_volume_backup_never_0 = parseFloat(JSON.parse(localStorage.getItem('playback_volume_backup_never_0')!));

                //set volume
                if(JSON.parse(localStorage.getItem('is_muted')!) === true){
                    this.playback_volume = 0;
                }else{
                    this.playback_volume = this.playback_volume_backup_never_0;
                }

                //mute decision
                    //scenario #1:
                        //when mute, it is volume 0
                    //scenario #2:
                        //when mute, it is muted, but volume is original
                    //scenario #1 is more keyboard-friendly
                    //scenario #2, when volume at 100%, one accidental arrowup would blast the volume to max
            }

            const audio_element = (this.$refs.audio_element as HTMLAudioElement);

            //set <audio> properties
            audio_element.playbackRate = this.playback_rate;
            audio_element.volume = this.playback_volume;
            
            //check if user's browser is unable to play mp3
            if(audio_element.canPlayType("audio/mp3").toLowerCase().length === 0){

                alert("Oops! Your browser does not support mp3 files. All recordings are in mp3 format.");
            }

            //attach listeners
            window.addEventListener('pointerdown', this.determineInstanceHasFocus);
            window.addEventListener('pointermove', this.doPlaybackDrag);
            window.addEventListener('pointerup', this.stopPlaybackDrag);
            this.propIsRecording === false ? window.addEventListener('keydown', this.handleKeyboardEvent) : null;
            document.addEventListener('visibilitychange', this.syncSliderAnimeAfterSuspend);
            audio_element.addEventListener('timeupdate', this.updateCurrentPlaybackTime);
            audio_element.addEventListener('error', this.setPlaybackSourceHasError);

            //resize and dark mode change
            this.redraw_canvases_store_index = this.redraw_canvases_store.addAudioVolumePeakCanvas(
                this.doRedraw
            );
        },
        beforeUnmount(){

            const audio_element = (this.$refs.audio_element as HTMLAudioElement);

            //remove listeners
            window.removeEventListener('pointerdown', this.determineInstanceHasFocus);
            window.removeEventListener('pointermove', this.doPlaybackDrag);
            window.removeEventListener('pointerup', this.stopPlaybackDrag);
            this.propIsRecording === false ? window.removeEventListener('keydown', this.handleKeyboardEvent) : null;
            document.removeEventListener('visibilitychange', this.syncSliderAnimeAfterSuspend);
            audio_element.removeEventListener('timeupdate', this.updateCurrentPlaybackTime);
            audio_element.removeEventListener('error', this.setPlaybackSourceHasError);

            if(this.redraw_canvases_store_index !== null){

                this.redraw_canvases_store.deleteAudioVolumePeakCanvas(this.redraw_canvases_store_index);
            }

            //record last stopped
            if(this.propAudioClip !== null){

                this.storeCurrentAudioClipLastStopped(this.propAudioClip);
            }
        },
    });
</script>