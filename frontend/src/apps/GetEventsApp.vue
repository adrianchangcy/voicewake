<template>
    <div class="flex flex-col">

        <!--loading-->
        <div v-if="is_fetching_event" class="flex flex-col gap-8">

            <div v-for="x in audio_clip_count" :key="x">
                <VAudioClipCardSkeleton/>
            </div>
        </div>

        <!--not loading-->
        <div v-else-if="event !== null">

            <!--audio-clips-->
            <EventCard
                :prop-event="event"
                :prop-show-title="false"
                :prop-load-v-audio-clip-cards-only="!canReply"
                @new-is-liked="event_reply_choices_store.newAudioClipIsLiked($event)"
                @new-v-playback-teleport-id="handleNewVPlaybackTeleportId($event)"
                class="pb-8"
            />

            <!--use custom transition with delay, as more complex v-else-if has race condition-->
            <!--causing new element to appear early-->
            <Transition
                name="transition-get-events-app"
                enter-from-class="opacity-0"
                enter-active-class="transition-opacity duration-500 ease-in-out delay-500"
                enter-to-class="opacity-100"
                leave-from-class="opacity-100"
                leave-active-class="transition-opacity duration-500 ease-in-out"
                leave-to-class="opacity-0"
            >

                <!--dialogs and reply choice URL-->
                <div v-if="hasDialog">

                    <!--dialogs-->
                    <div class="w-full h-fit pt-14 flex flex-col items-center text-xl font-medium">
                        <div
                            v-show="dialog_context === 'cancelled'"
                            class="w-full flex flex-col"
                        >
                            <FontAwesomeIcon icon="fas fa-eraser" class="mx-auto"/>
                            <span class="block mx-auto">Reply was cancelled.</span>
                        </div>
                        <div
                            v-show="dialog_context === 'expired'"
                            class="w-full flex flex-col"
                        >
                            <FontAwesomeIcon icon="fas fa-hourglass-end" class="mx-auto"/>
                            <span class="block mx-auto">Reply has expired.</span>
                        </div>
                    </div>

                    <!--URL back to more reply choices-->
                    <div class="pt-2">
                        <VActionSpecial
                            propElement="a"
                            href="/reply"
                            propElementSize="s"
                            propFontSize="s"
                            :prop-is-icon-only="true"
                            class="w-fit mx-auto"
                        >
                            <span class="flex items-center px-4">
                                <span class="block pb-0.5">More reply choices</span>
                                <FontAwesomeIcon icon="fas fa-arrow-right" class="text-lg pl-2"/>
                            </span>
                        </VActionSpecial>
                    </div>
                </div>

                <!--reply-->
                <div v-else-if="!hasDialog && !isReupload && hasReplyingMenu && canReply">

                    <VUsernameURL
                        :propUsername="username"
                    />

                    <div class="relative border border-theme-gray-2 rounded-lg px-2 sm:px-4 pt-8 pb-12">

                        <div ref="replying_title_section" class="grid grid-cols-4 gap-2 pb-6">

                            <VTitle
                                propFontSize="m"
                                class="col-span-3"
                            >
                                <template #title>
                                    <div class="h-10 flex items-center">
                                        <span>Replying</span>
                                    </div>
                                </template>
                            </VTitle>

                            <div class="col-span-1">
                                <VActionDanger
                                    @click="cancelReply()"
                                    prop-element="button"
                                    type="button"
                                    prop-element-size="s"
                                    prop-font-size="s"
                                    :prop-is-icon-only="is_event_cancelling"
                                    :prop-is-enabled="!isLoading"
                                    class="w-full"
                                >
                                    <VLoading
                                        v-show="is_event_cancelling"
                                        propElementSize="s"
                                        propColourClass="border-theme-light"
                                        class="mx-auto"
                                    />
                                    <span
                                        v-show="!is_event_cancelling"
                                        class="mx-auto"
                                    >
                                        Delete
                                    </span>
                                </VActionDanger>
                            </div>
                        </div>

                        <CreateAudioClips
                            :propIsOriginator="false"
                            :propReuploadAudioClipId="reupload_audio_clip_id"
                            :propEventId="event.event.id"
                            :propCanSubmit="!isLoading"
                            @isSubmitting="handleIsSubmitting($event)"
                            @isSubmitSuccessful="handleIsSubmitSuccessful($event)"
                        />
                    </div>
                </div>

                <!--reupload-->
                <div v-else-if="isReupload">
                    <VUsernameURL
                        :propUsername="username"
                    />
                    <div class="flex flex-col rounded-lg divide-y divide-theme-gray-2 border border-theme-gray-2">
                            
                        <div ref="reupload_title_section">
                            <VTitle
                                propFontSize="m"
                                class="px-2 sm:px-4 py-4"
                            >
                                <template #title>
                                    <div class="flex items-center">
                                        <span>Reupload recording</span>
                                    </div>
                                </template>
                                <template #titleDescription>
                                    <span class="text-base block text-red-700">
                                        Your previous recording had no sound.
                                    </span>
                                    <!--still null on first attempt, as cache is unreliable, since we don't know when task queue starts-->
                                    <span
                                        v-show="canShowLambdaAttemptsLeft"
                                        class="text-sm block py-1"
                                    >
                                        {{ getPrettyLambdaAttemptsLeft }}
                                    </span>
                                </template>
                            </VTitle>
                        </div>
                        <CreateAudioClips
                            :propIsOriginator="is_originator"
                            :propReuploadAudioClipId="reupload_audio_clip_id"
                            :propEventId="event_id!"
                            :propCanSubmit="!isLoading"
                            @isSubmitting="handleIsSubmitting($event)"
                            @isSubmitSuccessful="handleIsSubmitSuccessful($event)"
                            @hasForm="handleHasForm($event)"
                            class="px-2 sm:px-4 pt-8 pb-12"
                        />
                    </div>
                </div>
            </Transition>
        </div>

        <!--playback for normal view-->
        <Teleport
            v-if="!canReply && teleport_id !== ''"
            :to="teleport_id"
        >
            <VPlayback
                :prop-audio-clip="vplayback_store.getPlayingAudioClip"
                :prop-is-open="true"
                :prop-audio-volume-peaks="getSelectedAudioClipAudioVolumePeaks"
                :prop-bucket-quantity="20"
            />
        </Teleport>
    </div>
</template>

<script setup lang="ts">
    import EventCard from '../components/main/EventCard.vue';
    import VActionDanger from '../components/small/VActionDanger.vue';
    import VActionSpecial from '../components/small/VActionSpecial.vue';
    import CreateAudioClips from '../components/main/CreateAudioClips.vue';
    import VTitle from '../components/small/VTitle.vue';
    import VPlayback from '../components/medium/VPlayback.vue';
    import VUsernameURL from '../components/small/VUsernameURL.vue';
    import VAudioClipCardSkeleton from '../components/skeleton/VAudioClipCardSkeleton.vue';
    import VLoading from '../components/small/VLoading.vue';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faFaceMehBlank } from '@fortawesome/free-regular-svg-icons/faFaceMehBlank';
    import { faEraser } from '@fortawesome/free-solid-svg-icons/faEraser';
    import { faHourglassEnd } from '@fortawesome/free-solid-svg-icons/faHourglassEnd';
    import { faArrowRight } from '@fortawesome/free-solid-svg-icons/faArrowRight';

    library.add(faFaceMehBlank, faEraser, faHourglassEnd, faArrowRight);
</script>


<script lang="ts">
    import { defineComponent, } from 'vue';
    import { timeFromNowMS, getDataFromTemplateJSONScript, prettyTimePassed } from '@/helper_functions';
    import EventsAndAudioClipsTypes from '@/types/EventsAndAudioClips.interface';
    import { notify } from '@/wrappers/notify_wrapper';
    import { useEventReplyChoicesStore } from '@/stores/EventReplyChoicesStore';
    import { useVPlaybackStore } from '@/stores/VPlaybackStore';
    import { useAudioClipProcessingsStore } from '@/stores/AudioClipProcessingsStore';

    import anime from 'animejs';
    const axios = require('axios');


    export default defineComponent({
        name: 'GetEventsApp',
        data() {
            return {
                audio_clip_processings_store: useAudioClipProcessingsStore(),
                event_reply_choices_store: useEventReplyChoicesStore(),
                vplayback_store: useVPlaybackStore(),

                username: '',

                reupload_audio_clip_id: null as number|null,
                is_originator: false,

                event_id: null as number|null,
                event: null as EventsAndAudioClipsTypes|null,

                audio_clip_count: 0,
                original_document_title: "",
                
                is_fetching_event: false,
                is_event_cancelling: false,
                is_event_submitting: false,
                is_event_expiring: false,
                dialog_context: "" as ""|"expired"|"cancelled",

                expiry_interval: null as number|null,

                teleport_id: '',
            };
        },
        computed: {
            isLoading() : boolean {

                return (
                    this.is_fetching_event === true ||
                    this.is_event_cancelling === true ||
                    this.is_event_submitting === true ||
                    this.is_event_expiring === true
                );
            },
            isReupload() : boolean {

                return (
                    this.event === null &&
                    this.event_id !== null &&
                    this.reupload_audio_clip_id !== null
                );
            },
            canReply() : boolean {

                //use store instead of this.event
                //because this.event will still exist when replying is cancelled, but store won't have it
                return this.event_reply_choices_store.getReplyingEventId !== null &&
                    this.event_reply_choices_store.getReplyingEventId === this.event_id;
            },
            hasReplyingMenu() : boolean {

                //use this.event so we have an event to check with after replying
                return this.event !== null &&
                    Object.hasOwn(this.event, 'event_reply_queue') === true;
            },
            hasDialog() : boolean {

                return this.dialog_context !== '';
            },
            getSelectedAudioClipAudioVolumePeaks() : number[] {

                if(this.vplayback_store.getPlayingAudioClip === null){

                    return [];
                }

                return this.vplayback_store.getPlayingAudioClip.audio_volume_peaks;
            },
            canShowLambdaAttemptsLeft() : boolean {

                return (
                    this.reupload_audio_clip_id !== null &&
                    this.getPrettyLambdaAttemptsLeft !== ''
                );
            },
            getPrettyLambdaAttemptsLeft() : string {

                if(this.reupload_audio_clip_id === null){

                    return '';
                }

                return this.audio_clip_processings_store.getPrettyLambdaAttemptsLeft(this.reupload_audio_clip_id);
            },
        },
        watch: {
            canReply(new_value){

                //don't autoplay when replying
                this.vplayback_store.autoplayOnChange(!new_value);
            },
        },
        methods: {
            async getEvent() : Promise<void> {

                if(this.event_id === null){

                    return;
                }

                this.is_fetching_event = true;

                //prepare audio_clips, then separate
                await axios.get(window.location.origin + '/api/events/get/' + this.event_id.toString())
                .then(async(result:any)=>{

                    if(result.data['data'].length === 0){

                        return;
                    }

                    //API always returns list, even if there is only one event
                    this.event = result.data['data'][0];

                    if(Object.hasOwn(this.event!, 'event_reply_queue') === true){

                        //store this to store
                        //although we now have two separate locations,
                        //it being an object makes the locations refer to one singular object
                        this.event_reply_choices_store.updateReplyingEvent(this.event!);
                    }
                })
                .catch((error:any) => {

                    //if reupload, don't notify if no "ok" rows found
                    if(error.request.status === 404 && this.reupload_audio_clip_id !== null){

                        return;
                    }

                    notify({
                        type: 'error',
                        title: 'Error',
                        text: 'Unable to get recordings for this event.',
                        icon: {'font_awesome': 'fas fa-exclamation'},
                    }, 4000);

                }).finally(()=>{

                    this.is_fetching_event = false;
                });
            },
            async startExpiryInterval(is_replying:boolean): Promise<void> {

                if(this.isLoading === true){

                    return;
                }

                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_interval = null;

                let target_event: EventsAndAudioClipsTypes|null = null;
                let target_max_ms = 0;

                if(
                    is_replying === true &&
                    this.event_reply_choices_store.getReplyingEvent !== null
                ){

                    target_event = this.event_reply_choices_store.getReplyingEvent;
                    target_max_ms = this.event_reply_choices_store.event_reply_expiry_max_ms;

                }else if(
                    is_replying === false &&
                    this.event_reply_choices_store.getEventReplyChoices.length === 1
                ){

                    target_event = this.event_reply_choices_store.getEventReplyChoices[0];
                    target_max_ms = this.event_reply_choices_store.event_reply_choice_expiry_max_ms;

                }else{

                    return;
                }

                if(Object.hasOwn(target_event, 'event_reply_queue') === false){

                    throw new Error('Cannot start expiry interval if target_event has no event_reply_queue attribute.');
                }

                const when_locked_ms = new Date(target_event.event_reply_queue!.when_locked);
                const time_elapsed_ms = timeFromNowMS(when_locked_ms);

                //time is up
                if (time_elapsed_ms >= target_max_ms) {

                    //remove expiry to prevent race condition
                    this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                    this.expiry_interval = null;

                    this.is_event_expiring = true;

                    await this.event_reply_choices_store.cancelEvent(
                        is_replying
                    ).then(()=>{

                        //success

                        //get audio_clip_id, delete processing

                        const audio_clip_id = this.audio_clip_processings_store.getAudioClipIdByEventId(this.event_id!);

                        if(audio_clip_id !== null){

                            this.audio_clip_processings_store.deleteAudioClipProcessing(audio_clip_id);
                        }

                        this.dialog_context = 'expired';
                        document.title = this.original_document_title;

                    }).finally(()=>{

                        this.is_event_expiring = false;

                        if(this.canReply === true){

                            //cancellation failed, restart expiry
                            this.startExpiryInterval(true);
                        }
                    });

                    return;
                }

                //proceed

                //run every 1s if <120s remaining, else run every 60s
                //change this again once sped up
                let interval_ms:number = 0;

                if((target_max_ms - time_elapsed_ms) <= this.event_reply_choices_store.expiry_interval_checkpoint_ms){

                    interval_ms = this.event_reply_choices_store.fastest_expiry_interval_ms;

                }else{

                    interval_ms = this.event_reply_choices_store.slowest_expiry_interval_ms;
                }

                //declare this here for reusability
                const interval_function = async ()=>{

                    if(this.is_event_expiring === true){

                        return;
                    }

                    //get time difference
                    const time_elapsed_ms = timeFromNowMS(when_locked_ms);

                    //time is up
                    if (time_elapsed_ms >= target_max_ms) {

                        //remove expiry to prevent race condition
                        this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                        this.expiry_interval = null;

                        this.is_event_expiring = true;

                        await this.event_reply_choices_store.cancelEvent(
                            is_replying
                        ).then(()=>{

                            //success

                            //get audio_clip_id, delete processing

                            const audio_clip_id = this.audio_clip_processings_store.getAudioClipIdByEventId(this.event_id!);

                            if(audio_clip_id !== null){

                                this.audio_clip_processings_store.deleteAudioClipProcessing(audio_clip_id);
                            }

                            this.dialog_context = 'expired';
                            document.title = this.original_document_title;

                        }).finally(()=>{

                            this.is_event_expiring = false;

                            if(this.canReply === true){

                                //cancellation failed, restart expiry
                                this.startExpiryInterval(true);
                            }
                        });

                        return;
                    }

                    //if interval started with >1000, reinitialise itself for new interval with shorter time
                    if (
                        interval_ms === this.event_reply_choices_store.slowest_expiry_interval_ms &&
                        (target_max_ms - time_elapsed_ms) <= this.event_reply_choices_store.expiry_interval_checkpoint_ms
                    ){

                        //remove expiry to prevent race condition
                        this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                        this.expiry_interval = null;

                        this.expiry_interval = window.setInterval(
                            interval_function,
                            this.event_reply_choices_store.fastest_expiry_interval_ms
                        );

                        //change interval_ms as a lazy way to ensure this 'if' block runs once only
                        interval_ms = this.event_reply_choices_store.fastest_expiry_interval_ms;
                    }
                };

                //start interval
                this.expiry_interval = window.setInterval(interval_function, interval_ms);
            },
            handleIsSubmitting(new_value:boolean) : void {

                this.is_event_submitting = new_value;

                if(new_value === true){

                    this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                    this.expiry_interval = null;
                }
            },
            handleIsSubmitSuccessful(is_successful:boolean) : void {

                if(this.canReply === false){

                    return;
                }

                if(is_successful === false){

                    //restart expiry
                    this.is_event_submitting = false;
                    this.startExpiryInterval(true);
                    return;
                }

                //don't reset reply choice here, now is not the time
                //only reset when processing is done
            },
            async cancelReply() : Promise<void> {

                if(this.isLoading === true){

                    return;
                }

                this.is_event_cancelling = true;

                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_interval = null;

                await this.event_reply_choices_store.cancelEvent(true, false)
                .then(()=>{

                    //get audio_clip_id, delete processing

                    const audio_clip_id = this.audio_clip_processings_store.getAudioClipIdByEventId(this.event_id!);

                    if(audio_clip_id !== null){

                        this.audio_clip_processings_store.deleteAudioClipProcessing(audio_clip_id);
                    }

                    this.dialog_context = 'cancelled';
                    document.title = this.original_document_title;

                }).finally(()=>{

                    this.is_event_cancelling = false;

                    if(this.canReply === true){

                        //failed, restart expiry
                        this.startExpiryInterval(true);
                    }
                });
            },
            handleNewVPlaybackTeleportId(teleport_id:string) : void {

                this.teleport_id = teleport_id;
            },
            determineIsOriginatorForReupload() : void {

                //this only matters during reupload
                //when not for reupload, is responder

                //get data from SSR template
                const container = (document.getElementById('data-container-get-events') as HTMLElement);

                if(container === null){

                    throw new Error('container was not found in template.');
                }

                const audio_clip_role_name = container.getAttribute('data-reupload-audio-clip-role-name');

                if(audio_clip_role_name === null){

                    //not reupload
                    return;
                }

                if(audio_clip_role_name === 'originator'){

                    this.is_originator = true;

                }else if(audio_clip_role_name === 'responder'){

                    this.is_originator = false;

                }else{

                    throw new Error('Cannot determine originator/responder.');
                }
            },
            handleHasForm(new_value:boolean) : void {

                //this is to hide when CreateAudioClips.vue has its own dialog
                //helps to not overwhelm the user with texts, and to shift focus appropriately

                let target_el = null;

                if(this.canReply === true){

                    target_el = (this.$refs.replying_title_section as HTMLElement);

                }else{

                    target_el = (this.$refs.reupload_title_section as HTMLElement);
                }

                if(target_el === null){

                    return;
                }

                anime.remove(target_el);

                if(new_value === true){

                    anime({
                        targets: target_el,
                        easing: 'linear',
                        autoplay: true,
                        loop: false,
                        opacity: 0,
                        duration: 150,
                        complete: ()=>{
                            target_el.style.visibility = 'hidden';
                        }
                    });

                }else{

                    anime({
                        targets: target_el,
                        easing: 'linear',
                        autoplay: true,
                        loop: false,
                        opacity: 1,
                        duration: 150,
                        begin: ()=>{
                            target_el.style.visibility = 'visible';
                        }
                    });
                }
            },
        },
        beforeMount(){

            //username
            //empty string if not found
            this.username = getDataFromTemplateJSONScript('data-user-username') as string;

            //check if reuploading
            //does not rely on persisted store to know if user is reuploading
            this.reupload_audio_clip_id = this.audio_clip_processings_store.getReuploadAudioClipId();
            this.determineIsOriginatorForReupload();

            //change when_created
            const when_created_element = document.getElementById('event-when-created');

            if(when_created_element !== null){

                when_created_element.textContent = prettyTimePassed(
                    new Date(when_created_element.textContent as string)
                );
            }

            //get data from SSR template
            const container = (document.getElementById('data-container-get-events') as HTMLElement);

            this.event_reply_choices_store.getStaticValuesFromTemplate('data-container-get-events');
            this.event_id = parseInt(container.getAttribute('data-event-id') as string);
            this.audio_clip_count = JSON.parse(container.getAttribute('data-audio-clip-count') as string);

            //store original page title, so if user is no longer replying, can auto-revert
            this.original_document_title = document.title;

            //if replying or reuploading, don't autoplay
            this.vplayback_store.autoplayOnChange(
                this.canReply === false && this.isReupload === false
            );

            //if event_reply_choices_store has this event, get from store instead of API

            if(this.event_reply_choices_store.getReplyingEvent !== null){

                //get event from store
                //cannot refer to same object across multiple tabs, so like/dislike will be out of sync
                this.event = this.event_reply_choices_store.getReplyingEvent;
                
                //rewrite title
                document.title = "Replying: " + this.original_document_title;

                this.startExpiryInterval(true);
                return;
            }

            //get event from API
            //getEvent() will also update store's replying_event
            this.getEvent().then(()=>{

                if(this.canReply === true){

                    //rewrite title
                    document.title = "Replying: " + this.original_document_title;

                    this.startExpiryInterval(true);
                    this.vplayback_store.autoplayOnChange(false);
                }
            });
        },
    });
</script>