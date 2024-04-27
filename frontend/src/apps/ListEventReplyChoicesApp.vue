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
                                        <span>Come back soon!</span>
                                    </template>
                                </VDialogPlain>
                            </TransitionFade>
                        </div>
                    </div>

                    <!--is_replying dialog-->
                    <div
                        v-show="!isLoading && event_reply_choices_store.isReplying"
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
                            :propIsEnabled="!isLoading && event_reply_choices_store.hasEventReplyChoices"
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
                                class="block mx-auto"
                            ></VLoading>
                        </VActionSpecial>
                    </div>
                
                    <!--skip-->
                    <div class="col-span-1">
                        <VAction
                            @click="queueNextEventReplyChoices()"
                            :propIsEnabled="!isLoading && event_reply_choices_store.hasEventReplyChoices"
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
                        v-show="isEventCardOpen"
                        class="w-full"
                    >
                        <!--must use v-if since EventCard cannot exist with null-->
                        <!--keep-alive prevents unmounting when choices are suddenly null-->
                        <keep-alive>
                            <EventCard
                                v-if="event_reply_choices_store.getMainEvent !== null"
                                :prop-event="event_reply_choices_store.getMainEvent"
                                prop-guaranteed-event-generic-status="incomplete"
                                :prop-show-title="true"
                                :prop-has-border="true"
                                :prop-is-v-playback-open="isEventCardOpen"
                                @new-is-liked="event_reply_choices_store.newAudioClipIsLiked($event)"
                            />
                        </keep-alive>
                    </div>

                    <!--searching-->
                    <EventCardSkeleton
                        v-show="isLoading && is_searching"
                        :prop-audio-clip-quantity="1"
                        :prop-has-border="true"
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
    import VTitle from '../components/small/VTitle.vue';
    import EventCard from '../components/main/EventCard.vue';
    import EventCardSkeleton from '../components/skeleton/EventCardSkeleton.vue';
    import VActionSpecial from '../components/small/VActionSpecial.vue';
    import VAction from '../components/small/VAction.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VDialogPlain from '../components/small/VDialogPlain.vue';
    import VLoading from '../components/small/VLoading.vue';

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
    import { timeFromNowMS } from '@/helper_functions';
    // import { notify } from '@/wrappers/notify_wrapper';
    import EventsAndAudioClipsTypes from '@/types/EventsAndAudioClips.interface';
    import { useEventReplyChoicesStore } from '@/stores/EventReplyChoicesStore';
    import { usePopUpManagerStore } from '@/stores/PopUpManagerStore';
    // import AudioClipTonesTypes from '@/types/AudioClipTones.interface';


    export default defineComponent({
        name: "ListEventReplyChoicesApp",
        data() {
            return {
                event_reply_choices_store: useEventReplyChoicesStore(),
                pop_up_manager_store: usePopUpManagerStore(),

                //if false, then queue without removing previous locks
                has_searched_once: false,

                is_searching: false,
                is_reply_confirming: false,
                is_event_cancelling: false,
                is_event_expiring: false,

                expiry_interval: null as number|null,

                vplayback_canvas_ripple_callback: null as Function|null,
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
            isEventCardOpen() : boolean {

                //keep this open even when reply is confirming
                return (
                    (this.isLoading === false || this.is_reply_confirming === true) &&
                    this.event_reply_choices_store.isReplying === false
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
                    null,
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
                    this.startExpiryInterval(false);
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

                await this.event_reply_choices_store.confirmEventReplyChoice(index)
                .then(()=>{

                    //no need to undo loading when redirecting, else buttons momentarily become available
                    window.location.href = this.event_reply_choices_store.getReplyingEventURL;

                })
                .catch(()=>{

                    this.is_reply_confirming = false;

                    this.startExpiryInterval(false);
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

                    await this.event_reply_choices_store.cancelEvent(is_replying).finally(()=>{

                        this.is_event_expiring = false;
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

                        await this.event_reply_choices_store.cancelEvent(is_replying).finally(()=>{

                            this.is_event_expiring = false;
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
        },
        beforeMount(){

            (async ()=>{

                //always get expiry static values from template
                await this.event_reply_choices_store.getStaticValuesFromTemplate(
                    'data-container-list-event-choices'
                ).then(()=>{

                    //check if we have existing event in store
                    //if we do, start expiry

                    if(this.event_reply_choices_store.hasEventReplyChoices === true){

                        this.startExpiryInterval(false);
                        this.has_searched_once = true;

                    }else if(this.event_reply_choices_store.isReplying === true){

                        this.startExpiryInterval(true);
                        this.has_searched_once = true;
                    }

                });

                //listen to status changes triggered possibly by other pages

            })();
        },
    });
</script>