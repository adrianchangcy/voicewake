<template>
    <div class="flex flex-col">

        <!--loading-->
        <div v-if="is_fetching_event" class="flex flex-col gap-8">

            <VAudioClipCardSkeleton/>
        </div>

        <!--not loading-->
        <div v-else>

            <!--audio-clips-->
            <VEventCard
                v-if="hasEvent"
                :prop-event="event!"
                :prop-show-title="false"
                :prop-load-v-audio-clip-cards-only="!canReply"
                :prop-is-logged-in="is_logged_in"
                :prop-is-superuser="is_superuser"
                :prop-username="username"
                :prop-callable-popup-login-required="callableOpenPopupLoginRequired"
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
                            v-show="dialog_context === 'reply_expired'"
                            class="w-full flex flex-col"
                        >
                            <FontAwesomeIcon icon="fas fa-hourglass-end" class="mx-auto"/>
                            <span class="block mx-auto">Reply has expired.</span>
                        </div>
                        <div
                            v-show="dialog_context === 'not_replying_reupload_expired'"
                            class="w-full flex flex-col"
                        >
                            <FontAwesomeIcon icon="fas fa-hourglass-end" class="mx-auto"/>
                            <span class="block mx-auto">Reupload is overdue.</span>
                        </div>
                    </div>

                    <!--URL back to more reply choices-->
                    <div class="pt-2">
                        <VActionBorder
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
                        </VActionBorder>
                    </div>
                </div>

                <!--reupload-->
                <div
                    v-else-if="isReupload"
                    class=""
                >

                    <VTitle
                        propFontSize="l"
                        class="py-8"
                    >
                        <template #title>
                            <div class="flex items-center">
                                <span>Reupload</span>
                            </div>
                        </template>
                        <template #titleDescription>
                            <span class="text-base block text-red-700 dark:text-red-400">
                                Your previous recording had no sound.
                            </span>
                            <!--still null on first attempt, as cache is unreliable, since we don't know when task queue starts-->
                            <span
                                v-show="canShowLambdaAttemptsLeft"
                                class="text-base block text-red-700 dark:text-red-400"
                            >
                                {{ getPrettyLambdaAttemptsLeft }}
                            </span>
                        </template>
                    </VTitle>

                    <VCreateAudioClips
                        :propIsOriginator="is_originator"
                        :propReuploadAudioClipId="reupload_audio_clip_id"
                        :propEventId="event_id!"
                        :propCanSubmit="!isLoading"
                        @isSubmitting="handleIsSubmitting($event)"
                        @isSubmitSuccessful="handleIsSubmitSuccessful($event)"
                    />
                </div>

                <!--reply-->
                <div v-else-if="!isReupload && hasReplyingMenu && canReply && hasEvent">

                    <!--title, divider, cancel button-->
                    <div class="py-8 grid grid-cols-4 gap-2 items-center">

                        <!--title, divider-->
                        <div class="col-span-3 flex flex-row items-center">
                            <VTitle
                                propFontSize="l"
                                class="pb-2.5"
                            >
                                <template #title>
                                    <span>Replying</span>
                                </template>
                            </VTitle>

                            <!--divider-->
                            <div class="w-full pl-2">
                                <div class="w-full h-[1px] bg-theme-gray-2 dark:bg-dark-theme-gray-2">
                                </div>
                            </div>
                        </div>

                        <!--cancel button-->
                        <VActionDanger
                            @click="cancelReply()"
                            prop-element="button"
                            type="button"
                            prop-element-size="s"
                            prop-font-size="s"
                            :prop-is-icon-only="is_event_cancelling"
                            :prop-is-enabled="!isLoading"
                            class="col-start-4 col-span-1 px-2"
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
                                Cancel
                            </span>
                        </VActionDanger>
                    </div>

                    <!--form, expiry-->
                    <div>
                        <VCreateAudioClips
                            :propIsOriginator="false"
                            :propReuploadAudioClipId="reupload_audio_clip_id"
                            :propEventId="event!.event.id"
                            :propCanSubmit="!isLoading"
                            @isSubmitting="handleIsSubmitting($event)"
                            @isSubmitSuccessful="handleIsSubmitSuccessful($event)"
                        />

                        <VTitle
                            v-show="expiry_string !== ''"
                            prop-font-size="l"
                            class="block py-2 w-fit mx-auto"
                        >
                            <template #titleDescription>
                                {{ expiry_string }} left to reply.
                            </template>
                        </VTitle>
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
                :prop-audio-volume-peaks="vplayback_store.getPlayingAudioVolumePeaks"
                :prop-bucket-quantity="20"
            />
        </Teleport>
    </div>
</template>

<script setup lang="ts">
    import VEventCard from '@/components/main/VEventCard.vue';
    import VActionDanger from '@/components/small/VActionDanger.vue';
    import VActionBorder from '@/components/small/VActionBorder.vue';
    import VCreateAudioClips from '@/components/main/VCreateAudioClips.vue';
    import VTitle from '@/components/small/VTitle.vue';
    import VPlayback from '@/components/medium/VPlayback.vue';
    import VAudioClipCardSkeleton from '@/components/skeleton/VAudioClipCardSkeleton.vue';
    import VLoading from '@/components/small/VLoading.vue';

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
    import { timeFromNowMS, prettyTimePassed, prettyTimeRemaining, getPiniaDateObject, isLoggedIn, isSuperuser, getUsername } from '@/helper_functions';
    import EventsAndAudioClipsTypes from '@/types/EventsAndAudioClips.interface';
    import { notify } from '@/wrappers/notify_wrapper';
    import { useEventReplyChoicesStore } from '@/stores/EventReplyChoicesStore';
    import { useVPlaybackStore } from '@/stores/VPlaybackStore';
    import { useAudioClipProcessingsStore } from '@/stores/AudioClipProcessingsStore';
    import { usePopUpManagerStore } from '@/stores/PopUpManagerStore';
    import axios from 'axios';


    export default defineComponent({
        name: 'GetEventsApp',
        data() {
            return {
                audio_clip_processings_store: useAudioClipProcessingsStore(),
                event_reply_choices_store: useEventReplyChoicesStore(),
                vplayback_store: useVPlaybackStore(),
                pop_up_manager_store: usePopUpManagerStore(),

                is_logged_in: false,
                is_superuser: false,
                username: '',

                reupload_audio_clip_id: null as number|null,
                is_originator: true,

                event_id: null as number|null,
                event: null as EventsAndAudioClipsTypes|null,

                original_document_title: "",
                
                is_fetching_event: false,
                is_event_cancelling: false,
                is_event_submitting: false,
                is_event_expiring: false,
                dialog_context: "" as ""|"reply_expired"|"not_replying_reupload_expired"|"cancelled",

                expiry_interval: null as number|null,
                expiry_string: '',

                teleport_id: '',

                expiry_interval_checkpoint_ms: 80000, //when to switch from slowest_expiry_interval_ms to fastest_expiry_interval_ms
                slowest_expiry_interval_ms: 10000,
                fastest_expiry_interval_ms: 1000,
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

                //for originator reupload, event will be null, hence not included here
                return (
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
            hasEvent() : boolean {

                return this.event !== null;
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

                //for originator upload, no event will be returned

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
                    }, 4000);

                }).finally(()=>{

                    this.is_fetching_event = false;
                });
            },
            startExpiryInterval(is_replying:boolean): void {

                //if user is reuploading, use reupload expiry
                //if user is responder, responder expiry may be longer/shorter than reply expiry
                    //just use reply expiry, and if reply is expired, disallow reupload

                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_interval = null;
                this.expiry_string = '';

                let target_event: EventsAndAudioClipsTypes|null = null;
                let target_max_ms = 0;
                let start_date:Date|null = null;
                let expiry_context = '' as 'replying'|'not_replying_and_reupload';

                if(
                    is_replying === true &&
                    this.event_reply_choices_store.getReplyingEvent !== null
                ){

                    //user is replying, just use event_reply_queue's when_locked

                    target_event = this.event_reply_choices_store.getReplyingEvent;
                    target_max_ms = this.event_reply_choices_store.event_reply_expiry_ms;
                    start_date = getPiniaDateObject(target_event.event_reply_queue!.when_locked);
                    expiry_context = 'replying';

                }else if(
                    is_replying === false &&
                    this.reupload_audio_clip_id !== null
                ){

                    //user is not replying, use processing's last_attempt

                    target_max_ms = this.audio_clip_processings_store.audio_clip_unprocessed_expiry_ms;
                    expiry_context = 'not_replying_and_reupload';

                    const target_audio_clip_processing = this.audio_clip_processings_store.getAudioClipProcessing(
                        this.reupload_audio_clip_id
                    );

                    if(target_audio_clip_processing !== null){

                        start_date = getPiniaDateObject(
                            target_audio_clip_processing.last_attempt
                        );
                    }

                }else{

                    return;
                }

                if(target_event !== null && Object.hasOwn(target_event, 'event_reply_queue') === false){

                    throw new Error('Cannot start expiry interval if target_event has no event_reply_queue attribute.');
                }

                if(start_date === null){

                    throw new Error('start_date is null.');
                }

                const handle_expired = async ()=>{

                    if(this.is_event_expiring === true){

                        return;
                    }

                    //remove expiry to prevent race condition
                    this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                    this.expiry_interval = null;
                    this.expiry_string = '';

                    this.is_event_expiring = true;

                    if(expiry_context === 'replying'){

                        //replying

                        await this.event_reply_choices_store.cancelEvent(
                            is_replying
                        ).then(()=>{

                            //success

                            //get audio_clip_id, delete processing

                            const audio_clip_id = this.audio_clip_processings_store.getAudioClipIdByEventId(this.event_id!);

                            if(audio_clip_id !== null){

                                this.audio_clip_processings_store.deleteAudioClipProcessing(audio_clip_id);
                            }

                            this.dialog_context = 'reply_expired';
                            document.title = this.original_document_title;

                        }).finally(()=>{

                            this.is_event_expiring = false;

                            if(this.canReply === true){

                                //cancellation failed, restart expiry
                                this.startExpiryInterval(true);
                            }
                        });

                        return;

                    }else if(expiry_context === 'not_replying_and_reupload'){

                        //not replying, and reuploading

                        const current_processing = this.audio_clip_processings_store.getAudioClipProcessing(this.reupload_audio_clip_id!);

                        if(current_processing !== null){

                            const new_processing = this.audio_clip_processings_store.updateProcessing(
                                this.reupload_audio_clip_id!,
                                current_processing,
                                'not_found',
                                null
                            );

                            this.audio_clip_processings_store.audio_clip_processings[this.reupload_audio_clip_id!] = new_processing;
                        }

                        this.dialog_context = 'not_replying_reupload_expired';
                        document.title = this.original_document_title;
                        this.is_event_expiring = false;

                        return;

                    }else{

                        this.is_event_expiring = false;
                        throw new Error('Unrecognised expiry_context');
                    }
                };

                const time_elapsed_ms = timeFromNowMS(start_date);

                //time is up
                if (time_elapsed_ms >= target_max_ms){

                    handle_expired();
                    return;
                }

                //proceed

                //run every 1s if <120s remaining, else run every 60s
                //change this again once sped up
                let interval_ms = 0;

                if((target_max_ms - time_elapsed_ms) <= this.expiry_interval_checkpoint_ms){

                    interval_ms = this.fastest_expiry_interval_ms;

                }else{

                    interval_ms = this.slowest_expiry_interval_ms;
                }

                //get pretty time remaining on first time
                this.expiry_string = prettyTimeRemaining(time_elapsed_ms, target_max_ms);

                //declare this here for reusability
                const interval_function = async ()=>{

                    if(this.is_event_expiring === true){

                        return;
                    }

                    //get time difference
                    const time_elapsed_ms = timeFromNowMS(start_date);

                    //get pretty time remaining
                    this.expiry_string = prettyTimeRemaining(time_elapsed_ms, target_max_ms);

                    //time is up
                    if (time_elapsed_ms >= target_max_ms) {

                        handle_expired();
                        return;
                    }

                    //if interval started with >1000, reinitialise itself for new interval with shorter time
                    if (
                        interval_ms === this.slowest_expiry_interval_ms &&
                        (target_max_ms - time_elapsed_ms) <= this.expiry_interval_checkpoint_ms
                    ){

                        //remove expiry to prevent race condition
                        this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                        this.expiry_interval = null;
                        this.expiry_string = '';

                        this.expiry_interval = window.setInterval(
                            interval_function,
                            this.fastest_expiry_interval_ms
                        );

                        //change interval_ms as a lazy way to ensure this 'if' block runs once only
                        interval_ms = this.fastest_expiry_interval_ms;
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
                    this.expiry_string = '';
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
                this.expiry_string = '';

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
            getReuploadDetailsFromTemplate(data_container_element:HTMLElement) : void {

                //determines reupload_audio_clip_id, is_originator

                //this is only used to verify that reupload is allowed, when user wants to reupload
                //only used at GetEventsApp, when user is at reupload-specific URL

                //check if URL has get param

                const current_url = new URL(window.location.href);
                const reupload_audio_clip_id = data_container_element.getAttribute('data-reupload-audio-clip-id');
                const reupload_audio_clip_id_from_url = current_url.searchParams.get('reupload');

                if(
                    reupload_audio_clip_id !== null &&
                    reupload_audio_clip_id_from_url !== null &&
                    reupload_audio_clip_id === reupload_audio_clip_id_from_url
                ){

                    //is reupload
                    this.reupload_audio_clip_id = Number(reupload_audio_clip_id);

                }else{

                    //not reupload, just return
                    return;
                }

                //check role

                const audio_clip_role_name = data_container_element.getAttribute('data-reupload-audio-clip-role-name') as 'originator'|'responder';

                if(audio_clip_role_name === 'originator'){

                    this.is_originator = true;

                }else if(audio_clip_role_name === 'responder'){

                    this.is_originator = false;

                }else{

                    throw new Error('Missing or unrecognised data.');
                }
            },
            callableOpenPopupLoginRequired() : void {

                this.pop_up_manager_store.openPopup({context: 'login_required', kwargs: null});
            },
        },
        beforeMount(){

            this.is_logged_in = isLoggedIn();
            this.is_superuser = isSuperuser();
            this.username = getUsername();

            //get data from SSR template
            const container = document.getElementById('data-container-get-events') as HTMLElement;

            if(container === null){

                throw new Error('Data container element was not found.');
            }

            //change when_created
            const when_created_element = document.getElementById('event-when-created');

            if(when_created_element !== null){

                when_created_element.textContent = prettyTimePassed(
                    new Date(container.getAttribute('data-when-created') as string)
                );
            }

            this.getReuploadDetailsFromTemplate(container);
            this.event_reply_choices_store.getStaticValuesFromTemplate(container);
            this.audio_clip_processings_store.getStaticValuesFromTemplate(container);

            this.event_id = parseInt(container.getAttribute('data-event-id') as string);

            //store original page title, so if user is no longer replying, can auto-revert
            this.original_document_title = document.title;

            //if replying or reuploading, don't autoplay
            this.vplayback_store.autoplayOnChange(
                this.canReply === false && this.isReupload === false
            );

            //if event_reply_choices_store has this event, get from store instead of API

            if(this.canReply === true){

                //get event from store

                //cannot refer to same object across multiple tabs, so like/dislike will be out of sync
                this.event = this.event_reply_choices_store.getReplyingEvent;
                this.is_originator = false;
                
                //rewrite title
                document.title = "Replying: " + this.original_document_title;

                this.startExpiryInterval(true);

            }else{

                //get event from API

                //getEvent() will also update store's replying_event
                this.getEvent().then(()=>{

                    if(this.canReply === true){

                        this.is_originator = false;

                        //rewrite title
                        document.title = "Replying: " + this.original_document_title;

                        this.startExpiryInterval(true);
                        this.vplayback_store.autoplayOnChange(false);
                    }
                });
            }
        },
    });
</script>