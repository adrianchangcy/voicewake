<template>
    <div class="">

        <!--title-->
        <!--logo only here, since "Reply" goes away for certain parts, and putting it here would make things jolt-->
        <!--you can find "Reply" at areas that need it instead-->
        <!--for "Reply", we use pb-9 instead of pb-8 here due to the font overflowing out at current size-->
        <VTitle
            propFontSize="l"
            class="pt-8"
        >
            <template #title>
                <div class="flex flex-col text-center">
                    <FontAwesomeIcon icon="fas fa-comments" class="text-2xl mx-auto"/>
                </div>
            </template>
        </VTitle>

        <!--content-->
        <!--we want to do is_reply_confirming here to prevent any UI surprises when redirecting-->
        <TransitionGroupFade>

            <!--search, loading dialogs, other dialogs-->
            <div
                v-show="!is_searching && !event_reply_choices_store.hasEventReplyChoices && !is_reply_confirming"
                class="w-full h-fit"
            >

                <!--title, duplicated to prevent UI jolting compared to other alternatives-->
                <VTitle
                    propFontSize="l"
                    class="w-full pb-9"
                >
                    <template #title>
                        <div class="flex flex-col">
                            <span class="block w-full text-center">
                                Reply
                            </span>
                        </div>
                    </template>
                </VTitle>

                <!--content-->
                <TransitionGroupFade>

                    <!--can search-->
                    <div
                        v-show="canQueueNextEventReplyChoices && !event_reply_choices_store.isReplying"
                        class="w-full h-fit flex flex-col"
                    >

                        <!--search-->
                        <VActionSpecial
                            @click="queueNextEventReplyChoices()"
                            :propIsEnabled="canQueueNextEventReplyChoices"
                            propElement="button"
                            type="button"
                            propElementSize="2xl"
                            propFontSize="2xl"
                            :propIsRound="true"
                            class="w-40 block mx-auto"
                        >
                            <span class="block mx-auto">
                                Search
                            </span>
                        </VActionSpecial>

                        <!--dialog-->
                        <!--we must pre-write them because the variables are reset before transition, causing warp-->
                        <div
                            v-show="event_reply_choices_store.getSharedDialogContext !== ''"
                            class="pt-10 relative"
                        >

                            <TransitionFade>

                                <VDialogPlain
                                    v-if="event_reply_choices_store.getSharedDialogContext === 'no_new_event_reply_choices'"
                                    :prop-has-border="false"
                                    :prop-has-auto-space-logo="false"
                                    :prop-has-auto-space-title="false"
                                    :prop-has-auto-space-content="false"
                                    class="w-full"
                                >
                                    <template #logo>
                                        <FontAwesomeIcon icon="far fa-face-meh-blank"/>
                                    </template>
                                    <template #title>
                                        <span>No new recordings found.</span>
                                    </template>
                                    <template #content>
                                        <span>Search again in a moment!</span>
                                    </template>
                                </VDialogPlain>

                                <VDialogPlain
                                    v-else-if="event_reply_choices_store.getSharedDialogContext === 'event_reply_choices_expired'"
                                    :prop-has-border="false"
                                    :prop-has-auto-space-logo="false"
                                    :prop-has-auto-space-title="false"
                                    :prop-has-auto-space-content="false"
                                    class="w-full"
                                >
                                    <template #logo>
                                        <FontAwesomeIcon icon="fas fa-hourglass-end"/>
                                    </template>
                                    <template #title>
                                        <span>Reply choice has expired.</span>
                                    </template>
                                    <template #content>
                                        <span>Search again for more!</span>
                                    </template>
                                </VDialogPlain>

                                <VDialogPlain
                                    v-else-if="event_reply_choices_store.getSharedDialogContext === 'reply_expired'"
                                    :prop-has-border="false"
                                    :prop-has-auto-space-logo="false"
                                    :prop-has-auto-space-title="false"
                                    :prop-has-auto-space-content="false"
                                    class="w-full"
                                >
                                    <template #logo>
                                        <FontAwesomeIcon icon="fas fa-hourglass-end"/>
                                    </template>
                                    <template #title>
                                        <span>Reply has expired.</span>
                                    </template>
                                    <template #content>
                                        <span>Search again for more!</span>
                                    </template>
                                </VDialogPlain>

                                <VDialogPlain
                                    v-else-if="event_reply_choices_store.getSharedDialogContext === 'reply_cancelled'"
                                    :prop-has-border="false"
                                    :prop-has-auto-space-logo="false"
                                    :prop-has-auto-space-title="false"
                                    :prop-has-auto-space-content="false"
                                    class="w-full"
                                >
                                    <template #logo>
                                        <FontAwesomeIcon icon="fas fa-eraser"/>
                                    </template>
                                    <template #title>
                                        <span>Reply was cancelled.</span>
                                    </template>
                                    <template #content>
                                        <span>Search again for more!</span>
                                    </template>
                                </VDialogPlain>

                                <VDialogPlain
                                    v-else-if="event_reply_choices_store.getSharedDialogContext === 'event_reply_daily_limit_reached'"
                                    :prop-has-border="false"
                                    :prop-has-auto-space-logo="false"
                                    :prop-has-auto-space-title="false"
                                    :prop-has-auto-space-content="false"
                                    class="w-full"
                                >
                                    <template #logo>
                                        <FontAwesomeIcon icon="fas fa-battery-empty"/>
                                    </template>
                                    <template #title>
                                        <span>Reached daily reply limit.</span>
                                    </template>
                                    <template #content>
                                        <span>Come back later!</span>
                                    </template>
                                </VDialogPlain>


                                <VDialogPlain
                                    v-else-if="event_reply_choices_store.getSharedDialogContext === 'generic_event_unavailable'"
                                    :prop-has-border="false"
                                    :prop-has-auto-space-logo="false"
                                    :prop-has-auto-space-title="false"
                                    :prop-has-auto-space-content="false"
                                    class="w-full"
                                >
                                    <template #logo>
                                        <FontAwesomeIcon icon="far fa-face-meh-blank"/>
                                    </template>
                                    <template #title>
                                        <span>Event unavailable.</span>
                                    </template>
                                    <template #content>
                                        <span>{{event_reply_choices_store.getGenericDialogText}}</span>
                                    </template>
                                </VDialogPlain>
                            </TransitionFade>
                        </div>
                    </div>

                    <!--is_replying, no reupload dialog-->
                    <div
                        v-show="!isLoading && event_reply_choices_store.isReplying && !hasReupload"
                        class="w-full h-fit flex flex-col"
                    >

                        <!--dialog to complete or cancel unfinished reply before continuing-->
                        <VDialogPlain
                            class="w-full h-fit"
                            :prop-has-auto-space-logo="false"
                        >
                            <template #title>
                                <span class="block">1 unfinished reply found.</span>
                            </template>
                            <template #content>
                                <span class="block text-center">
                                    Open and complete your reply, or skip it, to continue searching.
                                </span>
                                <div
                                    class="grid grid-rows-1 grid-cols-2 pt-4 gap-2"
                                >
                                    <VActionSpecial
                                        propElement="a"
                                        :href="event_reply_choices_store.getReplyingEventURL"
                                        propElementSize="s"
                                        propFontSize="s"
                                        class="col-span-1"
                                    >
                                        <span class="block mx-auto">Open</span>
                                    </VActionSpecial>
                                    <VAction
                                        @click="queueNextEventReplyChoices(true)"
                                        :propIsEnabled="!isLoading"
                                        propElement="button"
                                        type="button"
                                        propElementSize="s"
                                        propFontSize="s"
                                        class="col-span-1"
                                    >
                                        <span class="block mx-auto">Skip</span>
                                    </VAction>
                                </div>
                            </template>
                        </VDialogPlain>
                    </div>

                    <!--is_replying, has reupload dialog-->
                    <div
                        v-show="!isLoading && event_reply_choices_store.isReplying && hasReupload"
                        class="w-full h-fit flex flex-col"
                    >

                        <!--use v-if as these are unlikely to happen, so no need to render in advance-->
                        <TransitionFade>

                            <!--if processing, just make user wait-->
                            <VDialogPlain
                                v-if="reuploadStatus === 'processing'"
                                class="w-full h-fit"
                                :prop-has-auto-space-logo="false"
                            >
                                <template #title>
                                    <span class="block">Processing reply...</span>
                                </template>
                                <template #content>
                                    <VProgressBar
                                        :prop-timestamps-ms="{
                                            durations: [40000],
                                            scales: [1],
                                        }"
                                        :prop-start-on-mounted="true"
                                        :prop-step="0"
                                        class="w-full"
                                    />
                                    <span class="block text-center">
                                        Once your reply has been processed, you can start searching again.
                                    </span>
                                </template>
                            </VDialogPlain>

                            <!--error, can reupload or cancel-->
                            <VDialogPlain
                                v-else-if="reuploadStatus === 'lambda_error'"
                                class="w-full h-fit"
                                :prop-has-auto-space-logo="false"
                            >
                                <template #title>
                                    <span class="block">Your reply had issues.</span>
                                </template>
                                <template #content>
                                    <span class="block text-center">
                                        You can reupload to fix it, or skip to cancel the reply.
                                    </span>
                                    <div
                                        class="grid grid-rows-1 grid-cols-2 pt-4 gap-2"
                                    >
                                        <VActionSpecial
                                            propElement="a"
                                            :href="determineReuploadURL"
                                            propElementSize="s"
                                            propFontSize="s"
                                            class="col-span-1"
                                        >
                                            <span class="block mx-auto">Reupload</span>
                                        </VActionSpecial>
                                        <VAction
                                            @click="skipReupload()"
                                            :propIsEnabled="!isLoading"
                                            propElement="button"
                                            type="button"
                                            propElementSize="s"
                                            propFontSize="s"
                                            class="col-span-1"
                                        >
                                            <span class="block mx-auto">Skip</span>
                                        </VAction>
                                    </div>
                                </template>
                            </VDialogPlain>
                        </TransitionFade>
                    </div>

                    <!--loading dialogs-->
                    <div
                        v-show="isLoading && !is_searching"
                        class="w-full h-fit flex flex-col"
                    >

                        <div class="h-40 flex items-center text-xl font-medium">
                            <div
                                v-show="is_event_cancelling"
                                class="w-full flex flex-col"
                            >
                                <FontAwesomeIcon icon="fas fa-eraser" class="mx-auto animate-pulse"/>
                                <span class="block mx-auto">Cancelling reply...</span>
                            </div>
                            <div
                                v-show="is_event_expiring"
                                class="w-full flex flex-col"
                            >
                                <FontAwesomeIcon icon="fas fa-eraser" class="mx-auto animate-pulse"/>
                                <span class="block mx-auto">Processing expired event...</span>
                            </div>
                        </div>
                    </div>
                </TransitionGroupFade>
            </div>

            <!--can show event reply choices-->
            <div
                v-show="
                    is_searching ||
                    event_reply_choices_store.hasEventReplyChoices || is_reply_confirming
                "
                class="w-full h-fit"
            >

                <!--main buttons-->
                <div
                    class="w-full h-fit pb-8 grid grid-cols-2 gap-4"
                >

                    <!--reply-->
                    <div class="col-span-1 justify-self-end">
                        <VActionSpecial
                            @click="confirmEventReplyChoice(0)"
                            :propIsEnabled="canReply"
                            propElement="button"
                            type="button"
                            propElementSize="l"
                            propFontSize="m"
                            :propIsRound="true"
                            :prop-is-icon-only="is_reply_confirming"
                            class="w-24"
                        >
                            <span
                                v-show="!is_reply_confirming"
                                class="block mx-auto"
                            >
                                Reply
                            </span>
                            <VLoading
                                v-show="is_reply_confirming"
                                prop-element-size="m"
                                prop-colour-class="border-theme-black"
                                class="block mx-auto"
                            ></VLoading>
                        </VActionSpecial>
                    </div>
                
                    <!--skip-->
                    <div class="col-span-1">
                        <VAction
                            @click="queueNextEventReplyChoices()"
                            :propIsEnabled="canSkip"
                            propElement="button"
                            type="button"
                            propElementSize="l"
                            propFontSize="m"
                            :propIsRound="true"
                            class="w-24"
                        >
                            <span class="block mx-auto">Skip</span>
                        </VAction>
                    </div>
                </div>

                <TransitionGroupFade>

                    <!--event preview-->
                    <div
                        v-show="canVEventCardOpen"
                        class="w-full"
                    >
                        <!--must use v-if since VEventCard cannot exist with null-->
                        <!--keep-alive prevents unmounting when choices are suddenly null-->
                        <keep-alive>
                            <VEventCard
                                v-if="event_reply_choices_store.getMainEvent !== null"
                                :prop-event="event_reply_choices_store.getMainEvent"
                                prop-guaranteed-event-generic-status="incomplete"
                                :prop-show-title="true"
                                :prop-has-border="true"
                                :prop-has-padding="true"
                                :prop-is-v-playback-open="canVEventCardOpen"
                                :prop-is-logged-in="is_logged_in"
                                :prop-is-superuser="is_superuser"
                                :prop-username="username"
                                :prop-callable-popup-login-required="callableOpenPopupLoginRequired"
                                @new-is-liked="event_reply_choices_store.newAudioClipIsLiked($event)"
                                @new-audio-clip-action="handleNewAudioClipAction($event)"
                            />
                        </keep-alive>

                        <VTitle
                            v-show="expiry_string !== ''"
                            prop-font-size="l"
                            class="block py-2 w-fit mx-auto"
                        >
                            <template #titleDescription>
                                Choice expires in {{ expiry_string }}.
                            </template>
                        </VTitle>
                    </div>

                    <!--searching-->
                    <VEventCardSkeleton
                        v-show="isLoading && is_searching"
                        :prop-audio-clip-quantity="1"
                        :prop-has-border="true"
                        :prop-has-padding="true"
                        class="w-full"
                    />

                    <!--loading dialogs-->
                    <div
                        v-show="isLoading && !is_searching"
                        class="w-full h-40 flex items-center text-xl font-medium"
                    >
                        <div
                            v-show="is_event_expiring"
                            class="w-full flex flex-col"
                        >
                            <FontAwesomeIcon icon="fas fa-eraser" class="mx-auto animate-pulse"/>
                            <span class="block mx-auto">Processing expired event...</span>
                        </div>
                    </div>
                </TransitionGroupFade>
            </div>
        </TransitionGroupFade>
    </div>
</template>


<script setup lang="ts">
    import VTitle from '@/components/small/VTitle.vue';
    import VEventCard from '@/components/main/VEventCard.vue';
    import VEventCardSkeleton from '@/components/skeleton/VEventCardSkeleton.vue';
    import VActionSpecial from '@/components/small/VActionSpecial.vue';
    import VAction from '@/components/small/VAction.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VDialogPlain from '@/components/small/VDialogPlain.vue';
    import VLoading from '@/components/small/VLoading.vue';
    import VProgressBar from '@/components/small/VProgressBar.vue';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faFaceMehBlank } from '@fortawesome/free-regular-svg-icons/faFaceMehBlank';
    import { faComments } from '@fortawesome/free-solid-svg-icons/faComments';
    import { faHourglassEnd } from '@fortawesome/free-solid-svg-icons/faHourglassEnd';
    import { faEraser } from '@fortawesome/free-solid-svg-icons/faEraser';
    import { faBatteryEmpty } from '@fortawesome/free-solid-svg-icons/faBatteryEmpty';

    library.add(faFaceMehBlank, faComments, faHourglassEnd, faEraser, faBatteryEmpty);
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { timeFromNowMS, prettyTimeRemaining, isLoggedIn, isSuperuser, getUsername } from '@/helper_functions';
    // import { notify } from '@/wrappers/notify_wrapper';
    import EventsAndAudioClipsTypes from '@/types/EventsAndAudioClips.interface';
    import { useEventReplyChoicesStore } from '@/stores/EventReplyChoicesStore';
    import { usePopUpManagerStore } from '@/stores/PopUpManagerStore';
    import { useAudioClipProcessingsStore } from '@/stores/AudioClipProcessingsStore';
    import { useVPlaybackStore } from '@/stores/VPlaybackStore';
    import { AudioClipProcessingStatusesTypes } from '@/types/AudioClipProcessingDetails.interface';
    import AudioClipActionsTypes from '@/types/AudioClipActions.interface';


    export default defineComponent({
        name: "EventReplyChoicesApp",
        data() {
            return {
                event_reply_choices_store: useEventReplyChoicesStore(),
                pop_up_manager_store: usePopUpManagerStore(),
                audio_clip_processings_store: useAudioClipProcessingsStore(),
                vplayback_store: useVPlaybackStore(),

                is_logged_in: false,
                is_superuser: false,
                username: '',

                //if false, then queue without removing previous locks
                has_searched_once: false,

                is_searching: false,
                is_reply_confirming: false,
                is_event_cancelling: false,
                is_event_expiring: false,

                expiry_interval: null as number|null,
                expiry_string: '',

                vplayback_canvas_ripple_callback: null as Function|null,

                expiry_interval_checkpoint_ms: 80000, //when to switch from slowest_expiry_interval_ms to fastest_expiry_interval_ms
                slowest_expiry_interval_ms: 10000,
                fastest_expiry_interval_ms: 1000,
            };
        },
        computed: {
            isLoading() : boolean {

                return (
                    this.is_searching === true ||
                    this.is_reply_confirming === true ||
                    this.is_event_cancelling === true ||
                    this.is_event_expiring === true
                );
            },
            canQueueNextEventReplyChoices() : boolean {

                return this.isLoading === false;
            },
            canVEventCardOpen() : boolean {

                //keep this open even when reply is confirming
                return (
                    (this.isLoading === false || this.is_reply_confirming === true) &&
                    this.event_reply_choices_store.isReplying === false
                );
            },
            hasReupload() : boolean {

                return this.audio_clip_processings_store.getResponderProcessing !== null;
            },
            reuploadStatus() : ''|AudioClipProcessingStatusesTypes {

                const processing = this.audio_clip_processings_store.getResponderProcessing;

                if(processing === null){

                    return '';
                }

                return processing.status;
            },
            determineReuploadURL() : string {

                const processing = this.audio_clip_processings_store.getResponderProcessing;
                const audio_clip_id = this.audio_clip_processings_store.responder_processing_audio_clip_id;

                if(
                    processing === null || audio_clip_id === null
                ){

                    return '';
                }

                return this.audio_clip_processings_store.determineReuploadURL(
                    processing['event'].id,
                    audio_clip_id
                );
            },
            canReply() : boolean {

                return (
                    this.isLoading === false &&
                    this.event_reply_choices_store.hasEventReplyChoices === true &&
                    this.event_reply_choices_store.getEventReplyChoices[0].event.generic_status.generic_status_name !== 'deleted'
                );
            },
            canSkip() : boolean {

                return (
                    this.isLoading === false
                    && this.event_reply_choices_store.hasEventReplyChoices === true
                );
            },
        },
        methods: {
            async queueNextEventReplyChoices(is_cancelling_reply:boolean=false) : Promise<void> {

                if(this.canQueueNextEventReplyChoices === false){

                    return;
                }

                //remove expiry to prevent race condition
                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_interval = null;
                this.expiry_string = '';

                //do is_cancelling_reply=true if we are cancelling + searching instead of just searching
                //does not affect API itself

                if(is_cancelling_reply === true){

                    this.is_event_cancelling = true;

                }else{

                    this.is_searching = true;
                }

                //when has_searched_once is true, all requests auto-unlock previous events
                //when false, it fetches previous valid events, if any
                await this.event_reply_choices_store.queueNextEventReplyChoices(
                    this.has_searched_once
                ).then(()=>{

                    //put here instead of in "finally" block
                    //when there are errors not by user's fault, can repeat
                    this.has_searched_once = true;

                }).finally(()=>{

                    if(is_cancelling_reply === true){
                        
                        //reset replying data in store
                        this.is_event_cancelling = false;
                        this.event_reply_choices_store.updateReplyingEvent(null);

                    }else{

                        this.is_searching = false;
                    }

                    //clear interval, and restart if there are events
                    this.handleExpiryInterval(false);
                });
            },
            async confirmEventReplyChoice(index:number) : Promise<void> {

                if(this.isLoading === true){

                    return;
                }

                this.is_reply_confirming = true;

                //remove expiry to prevent race condition
                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_interval = null;
                this.expiry_string = '';

                await this.event_reply_choices_store.confirmEventReplyChoice(index)
                .then(()=>{

                    //no need to undo loading when redirecting, else buttons momentarily become available
                    window.location.href = this.event_reply_choices_store.getReplyingEventURL;

                }).finally(()=>{
                    
                    this.is_reply_confirming = false;
                    this.handleExpiryInterval(false);
                });
            },
            async handleExpiryInterval(is_replying:boolean): Promise<void> {

                if(this.isLoading === true){

                    return;
                }

                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_interval = null;
                this.expiry_string = '';

                let target_event: EventsAndAudioClipsTypes|null = null;
                let target_max_ms = 0;

                if(
                    is_replying === true &&
                    this.event_reply_choices_store.getReplyingEvent !== null
                ){

                    target_event = this.event_reply_choices_store.getReplyingEvent;
                    target_max_ms = this.event_reply_choices_store.event_reply_expiry_ms;

                }else if(
                    is_replying === false &&
                    this.event_reply_choices_store.getEventReplyChoices.length === 1
                ){

                    target_event = this.event_reply_choices_store.getEventReplyChoices[0];
                    target_max_ms = this.event_reply_choices_store.event_reply_choice_expiry_ms;

                }else{

                    //no new interval needed
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
                    this.expiry_string = '';

                    this.is_event_expiring = true;

                    await this.event_reply_choices_store.cancelEvent(is_replying).finally(()=>{

                        this.is_event_expiring = false;
                    });

                    return;
                }

                //proceed

                //run every 1s if <120s remaining, else run every 60s
                //change this again once sped up
                let interval_ms:number = 0;

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
                    const time_elapsed_ms = timeFromNowMS(when_locked_ms);

                    //get pretty time remaining
                    this.expiry_string = prettyTimeRemaining(time_elapsed_ms, target_max_ms);

                    //time is up
                    if (time_elapsed_ms >= target_max_ms) {

                        //remove expiry to prevent race condition
                        this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                        this.expiry_interval = null;
                        this.expiry_string = '';

                        this.is_event_expiring = true;

                        //currently does nothing if auto expiry cancels and fails
                        await this.event_reply_choices_store.cancelEvent(is_replying).finally(()=>{

                            this.is_event_expiring = false;
                        });

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
            async skipReupload() : Promise<void> {

                if(this.is_event_cancelling === true){

                    return;
                }

                this.is_event_cancelling = true;

                const api_calls = [];

                if(this.audio_clip_processings_store.responder_processing_audio_clip_id !== null){

                    api_calls.push(
                        this.audio_clip_processings_store.deleteAudioClipProcessing(
                            this.audio_clip_processings_store.responder_processing_audio_clip_id
                        )
                    );
                }

                api_calls.push(
                    this.queueNextEventReplyChoices(true)
                );

                await Promise.allSettled(api_calls).finally(()=>{

                    this.is_event_cancelling = false;
                })
            },
            callableOpenPopupLoginRequired() : void {

                this.pop_up_manager_store.openPopup({context: 'login_required', kwargs: null});
            },
            handleNewAudioClipAction(new_value:AudioClipActionsTypes) : void {

                //must be logged in

                if(this.is_logged_in === false){

                    this.pop_up_manager_store.openPopup({'context': 'login_required', 'kwargs': null});
                    return;
                }

                //proceed

                let popup_title = '';
                let popup_description = '';
                let popup_cancellation_term = '';
                let popup_confirmation_term = '';

                if(new_value.action === 'ban'){

                    popup_title = 'Ban recording?';
                    popup_description = 'User will incur a temporary ban.';
                    popup_cancellation_term = 'Cancel';
                    popup_confirmation_term = 'Ban';

                }else if(new_value.action === 'delete'){

                    if(new_value.audio_clip.audio_clip_role.audio_clip_role_name === 'originator'){

                        popup_description = 'The event will also be deleted.';

                    }else if(new_value.audio_clip.audio_clip_role.audio_clip_role_name === 'responder'){

                        popup_description = 'This action cannot be undone.';
                    }

                    popup_title = 'Delete recording?';
                    popup_cancellation_term = 'Cancel';
                    popup_confirmation_term = 'Delete';

                }else if(new_value.action === 'report'){

                    popup_title = 'Report recording?';
                    popup_description = 'The recording will be evaluated for a ban.';
                    popup_cancellation_term = 'Cancel';
                    popup_confirmation_term = 'Report';

                }else{

                    throw new Error('Invalid action.');
                }

                //do nothing on cancel
                const popup_cancellation_callback = ()=>{};

                //prepare callback on confirmation
                const popup_confirmation_callback = async ()=>{

                    await new_value.api_request().then(()=>{

                        //do nothing to vplayback_store
                        //do nothing to filtered events store to keep frontend logic simpler

                        //since VEventCard is using its own VPlayback, we have no other choice but to trigger pause

                        if(new_value.action === 'ban' || new_value.action === 'delete'){

                            this.event_reply_choices_store.updateAudioClipDeleted(
                                new_value.audio_clip.event_id,
                                new_value.audio_clip.audio_clip_role.audio_clip_role_name
                            );

                            if(
                                this.event_reply_choices_store.getMainEvent !== null &&
                                new_value.audio_clip.event_id === this.event_reply_choices_store.getMainEvent.event.id
                            ){

                                this.vplayback_store.triggerPause();
                            }
                        }
                    });
                };

                //open dialog
                this.pop_up_manager_store.openPopup({
                    context: 'cancel_confirm',
                    kwargs: {
                        prop_title: popup_title,
                        prop_description: popup_description,
                        prop_cancellation_term: popup_cancellation_term,
                        prop_cancellation_callback: popup_cancellation_callback,
                        prop_confirmation_term: popup_confirmation_term,
                        prop_confirmation_callback: popup_confirmation_callback,
                    }
                });
            },
        },
        beforeMount(){

            this.is_logged_in = isLoggedIn();
            this.is_superuser = isSuperuser();
            this.username = getUsername();

            const container = document.getElementById('data-container-list-event-choices') as HTMLElement;

            if(container === null){

                throw new Error('Data container element was not found.');
            }

            //always get expiry static values from template
            this.event_reply_choices_store.getStaticValuesFromTemplate(container);

            //check if we have existing event in store
            //if we do, start expiry

            if(this.event_reply_choices_store.hasEventReplyChoices === true){

                this.handleExpiryInterval(false);
                this.has_searched_once = true;

            }else if(this.event_reply_choices_store.isReplying === true){

                this.handleExpiryInterval(true);
                this.has_searched_once = true;
            }
        },
    });
</script>