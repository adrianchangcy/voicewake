<template>
    <div class="flex flex-col">

        <div v-if="is_fetching_event" class="flex flex-col gap-8">

            <!--loading audio-clips-->
            <div v-for="x in audio_clip_count" :key="x">
                <VAudioClipCardSkeleton/>
            </div>
        </div>

        <div v-else-if="event !== null">

            <!--audio-clips-->
            <EventCard
                :prop-event="event"
                :prop-show-title="false"
                :prop-load-v-audio-clip-cards-only="!isReplying"
                @new-is-liked="event_reply_choices_store.newAudioClipIsLiked($event)"
                @new-v-playback-teleport-id="handleNewVPlaybackTeleportId($event)"
            />

            <!--reply area-->
            <div
                v-if="hasReplyingMenu"
            >
                <TransitionFadeSlow>
                    <div
                        v-if="isReplying"
                        class="w-full flex flex-col pt-8"
                    >
                        <VUsernameURL
                            :propUsername="(getDataFromTemplateJSONScript('data-user-username') as string)"
                        />

                        <div class="relative border border-theme-gray-2 rounded-lg px-2 sm:px-4 py-8 shade-border-when-hover transition-colors">

                            <div class="grid grid-cols-4 gap-2 pb-6">

                                <VTitle
                                    propFontSize="m"
                                    class="col-span-3"
                                >
                                    <template #title>
                                        <div class="h-10 flex items-center">
                                            <span>Replying...</span>
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
                                :propEventId="event.event.id"
                                :propCanSubmit="!isLoading"
                                @isSubmitting="handleIsSubmitting($event)"
                                @isSubmitSuccessful="handleIsSubmitSuccessful($event)"
                            />
                        </div>
                    </div>

                    <!--just cancelled while replying-->
                    <div
                        v-else
                        class="w-full"
                    >
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
                                class="w-fit mx-auto"
                            >
                                <span class="flex items-center px-4">
                                    <span class="block">More reply choices</span>
                                    <FontAwesomeIcon icon="fas fa-arrow-right" class="text-lg pl-2"/>
                                </span>
                            </VActionSpecial>
                        </div>
                    </div>
                </TransitionFadeSlow>
            </div>

            <Teleport
                v-if="!isReplying && teleport_id !== ''"
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
    </div>
</template>

<script setup lang="ts">
    import EventCard from '../components/main/EventCard.vue';
    import VActionDanger from '../components/small/VActionDanger.vue';
    import VActionSpecial from '../components/small/VActionSpecial.vue';
    import CreateAudioClips from '../components/main/CreateAudioClips.vue';
    import VTitle from '../components/small/VTitle.vue';
    import TransitionFadeSlow from '@/transitions/TransitionFadeSlow.vue';
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
    import { notify } from 'notiwind';
    import { useEventReplyChoicesStore } from '@/stores/EventReplyChoicesStore';
    import { useVPlaybackStore } from '@/stores/VPlaybackStore';
    import { CreateAudioClips__isSubmitSuccessfulTypes } from '@/types/General.interface';

    const axios = require('axios');


    export default defineComponent({
        name: 'GetEventsApp',
        data() {
            return {
                event_reply_choices_store: useEventReplyChoicesStore(),
                vplayback_store: useVPlaybackStore(),

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
            isReplying() : boolean {

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
            getSelectedAudioClipAudioVolumePeaks() : number[] {

                if(this.vplayback_store.getPlayingAudioClip === null){

                    return [];
                }

                return this.vplayback_store.getPlayingAudioClip.audio_volume_peaks;
            },
        },
        watch: {
            isReplying(new_value){

                //don't autoplay when replying
                this.vplayback_store.updateCanAutoplay(!new_value);
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
                        await this.event_reply_choices_store.updateReplyingEvent(this.event!);
                    }
                })
                .catch((error:any) => {

                    let error_text = '';

                    if(Object.hasOwn(error, 'request') === true && Object.hasOwn(error, 'response') === true){

                        error_text = error.response.data['message'];
                    }

                    notify({
                        title: "Error",
                        text: error_text,
                        type: "error"
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

                    await this.event_reply_choices_store.cancelEvent(is_replying).finally(()=>{

                        if(this.isReplying === false){

                            this.is_event_expiring = false;
                            this.dialog_context = 'expired';
                            document.title = this.original_document_title;

                        }else{

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

                        await this.event_reply_choices_store.cancelEvent(is_replying).finally(()=>{

                            if(this.isReplying === false){

                                this.is_event_expiring = false;
                                this.dialog_context = 'expired';
                                document.title = this.original_document_title;

                            }else{

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
            async handleIsSubmitting(new_value:boolean) : Promise<void> {

                this.is_event_submitting = new_value;

                if(new_value === true){

                    this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                    this.expiry_interval = null;
                }
            },
            async handleIsSubmitSuccessful(new_data:CreateAudioClips__isSubmitSuccessfulTypes) : Promise<void> {

                if(new_data['is_successful'] === true){

                    this.event_reply_choices_store.softReset();
                    window.location.replace(window.location.href);

                }else{

                    this.is_event_submitting = false;
                    this.startExpiryInterval(true);
                }
            },
            async cancelReply() : Promise<void> {

                if(this.isLoading === true){

                    return;
                }

                this.is_event_cancelling = true;

                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_interval = null;

                await this.event_reply_choices_store.cancelEvent(true, false)
                .finally(()=>{

                    if(this.isReplying === false){

                        this.dialog_context = "cancelled";
                        document.title = this.original_document_title;

                    }else{

                        this.is_event_cancelling = false;
                        this.startExpiryInterval(true);
                    }

                });
            },
            handleNewVPlaybackTeleportId(teleport_id:string) : void {

                this.teleport_id = teleport_id;
            },
        },
        beforeMount(){

            //change when_created
            document.getElementsByClassName('when-created')[0].textContent = prettyTimePassed(new Date(
                document.getElementsByClassName('when-created')[0].textContent as string
            ));

            //get data from SSR template
            const container = (document.getElementById('data-container-get-events') as HTMLElement);

            this.event_reply_choices_store.getStaticValuesFromTemplate('data-container-get-events');
            this.event_id = parseInt(container.getAttribute('data-event-id') as string);
            this.audio_clip_count = JSON.parse(container.getAttribute('data-audio-clip-count') as string);

            //store original page title, so if user is no longer replying, can auto-revert
            this.original_document_title = document.title;

            //if replying, don't autoplay
            this.vplayback_store.updateCanAutoplay(!this.isReplying);

            //if event_reply_choices_store has this event, get from store instead of API

            if(this.event_reply_choices_store.getReplyingEvent !== null){

                //get event from store
                //cannot refer to same object across multiple tabs, so like/dislike will be out of sync
                this.event = this.event_reply_choices_store.getReplyingEvent;
                
                //rewrite title
                document.title = "Replying: " + document.title;

                this.startExpiryInterval(true);

            }else{

                //get event from API
                //getEvent() will also update store's replying_event
                (async ()=>{
                    await this.getEvent().then(()=>{

                        if(this.isReplying === true){

                            //rewrite title
                            document.title = "Replying: " + document.title;

                            this.startExpiryInterval(true);
                            this.vplayback_store.updateCanAutoplay(!this.isReplying);
                        }
                    });
                })();
            }
        },
    });
</script>