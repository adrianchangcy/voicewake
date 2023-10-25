<template>
    <div class="flex flex-col">

        <div v-if="is_searching" class="flex flex-col gap-10">

            <!--loading audio-clips-->
            <div v-for="x in audio_clip_count" :key="x">
                <VAudioClipCardSkeleton/>
            </div>
        </div>

        <div v-else-if="event !== null">

            <!--audio-clips-->
            <EventCard
                :propEvent="event"
                :propShowTitle="false"
            />

            <!--reply area-->
            <TransitionFadeSlow>
                <div
                    v-if="is_this_user_replying"
                    id="is-replying-area"
                    class="flex flex-col gap-2 pt-10"
                >
                    <VUsernameURL
                        :propUsername="(getDataFromTemplateJSONScript('data-user-username') as string)"
                    />

                    <div class="border border-theme-light-gray rounded-lg px-4 py-6 relative">

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
                                <VActionButtonDangerS
                                    class="w-full"
                                    @click.stop="stopReplying('deleted')"
                                    :propIsEnabled="canDelete"
                                >
                                    <VLoading
                                        v-if="is_deleting"
                                        propElementSize="s"
                                        propColourClass="border-theme-light"
                                        class="mx-auto"
                                    />
                                    <span
                                        v-else
                                        class="mx-auto"
                                    >
                                        Delete
                                    </span>
                                </VActionButtonDangerS>
                            </div>
                        </div>

                        <CreateAudioClips
                            :propIsOriginator="false"
                            :propEventId="event.event.id"
                            :propCanSubmit="canSubmit"
                            @isSubmitting="handleIsSubmitting($event)"
                            @isSubmitSuccessful="handleIsSubmitSuccessful($event)"
                        />
                    </div>
                </div>

                <!--just deleted while replying-->
                <div
                    v-else-if="reply_is_deleted"
                    class="w-full h-fit pt-10 flex flex-col text-xl font-medium text-center text-theme-black"
                >
                    <i class="fas fa-eraser block w-full" aria-hidden="true"></i>
                    <span class="block w-full">Your reply has been deleted.</span>
                </div>

                <!--just expired while replying-->
                <div
                    v-else-if="reply_is_expired"
                    class="w-full h-fit pt-10 flex flex-col text-xl font-medium text-center text-theme-black"
                >
                    <i class="fas fa-hourglass-end block w-full" aria-hidden="true"></i>
                    <span class="block w-full">Your reply has expired.</span>
                </div>
            </TransitionFadeSlow>

            <TransitionFadeSlow>
                <!--URL back to more reply choices-->
                <div v-if="reply_is_deleted || reply_is_expired" class="pt-2">
                    <VActionSimplest
                        propElement="a"
                        href="/reply"
                        propElementSize="s"
                        propFontSize="s"
                        class="w-fit mx-auto"
                    >
                        <span class="flex items-center px-4">
                            <span class="block">More reply choices</span>
                            <i class="fas fa-arrow-right block text-lg pl-2" aria-hidden="true"></i>
                        </span>
                    </VActionSimplest>
                </div>
            </TransitionFadeSlow>

            <!--VAudioClipCard emits selection, which triggers :to, thus teleporting-->
            <!--presence of VAudioClipCard depends on VEventCard-->
            <div v-if="selected_audio_clip !== null">
                <Teleport :to="getVPlaybackTeleportId">
                    <VPlayback
                        :propAudioClip="selected_audio_clip"
                        :propIsOpen="true"
                        :propAudioVolumePeaks="selected_audio_clip.audio_volume_peaks"
                        :propBucketQuantity="selected_audio_clip.audio_volume_peaks.length"
                        :propAutoPlayOnSourceChange="true"
                    />
                </Teleport>
            </div>
        </div>
    </div>
</template>


<script setup lang="ts">
    import EventCard from '@/components/main/EventCard.vue';
    import VActionButtonDangerS from '@/components/small/VActionButtonDangerS.vue';
    import VActionSimplest from '@/components/small/VActionSimplest.vue';
    import CreateAudioClips from '@/components/main/CreateAudioClips.vue';
    import VTitle from '@/components/small/VTitle.vue';
    import TransitionFadeSlow from '@/transitions/TransitionFadeSlow.vue';
    import VPlayback from '@/components/medium/VPlayback.vue';
    import VUsernameURL from '@/components/small/VUsernameURL.vue';
    import VAudioClipCardSkeleton from '@/components/skeleton/VAudioClipCardSkeleton.vue';
    import VLoading from '@/components/small/VLoading.vue';
</script>


<script lang="ts">
    import { defineComponent, } from 'vue';
    import { prettyTimePassed, prettyTimeRemaining, getDataFromTemplateJSONScript, timeFromNowMS } from '@/helper_functions';
    import GroupedAudioClipsTypes from '@/types/GroupedAudioClips.interface';
    import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';
    import StatusValues from '@/types/values/StatusValues';
    import { notify } from 'notiwind';
    import { useUnfinishedReplyStore } from '@/stores/UnfinishedReplyStore';
    import { useCurrentlyPlayingAudioClipStore } from '@/stores/CurrentlyPlayingAudioClipStore';
    const axios = require('axios');

    export default defineComponent({
        name: 'GetEventsApp',
        data() {
            return {
                unfinished_reply_store: useUnfinishedReplyStore(),
                currently_playing_audio_clip_store: useCurrentlyPlayingAudioClipStore(),

                user_id: null as number|null,
                event_id: null as number|null,
                audio_clip_count: 0, //from DOM
                is_this_user_replying: false,
                is_deleted: false,

                reply_is_deleted: false,    //set True once, only to show message
                reply_is_expired: false,  //set True once, only to show message

                event: null as GroupedAudioClipsTypes|null,

                is_searching: false,
                is_deleting: false,
                is_expiring: false,
                is_submitting: false,
                
                selected_audio_clip: null as AudioClipsAndLikeDetailsTypes|null,
                reply_expiry_interval: null as number|null,
                reply_expiry_string: '',

                choice_expiry_max_ms: 0,   //will be replaced with SSR data on beforeMount()
                reply_expiry_max_ms: 0, //will be replaced with SSR data on beforeMount()
                expiry_interval_checkpoint_ms: 80000, //transitions from minute to seconds smoothly
                slowest_expiry_interval_ms: 10000,
                fastest_expiry_interval_ms: 1000,
            };
        },
        computed: {
            canSubmit() : boolean {

                return this.is_this_user_replying === true && this.is_searching === false &&
                    this.is_deleting === false && this.is_expiring === false && this.is_submitting === false;
            },
            canDelete() : boolean {

                return this.canSubmit;
            },
            getVPlaybackTeleportId() : string {

                if(this.selected_audio_clip === null){

                    return '';
                }

                return '#playback-teleport-audio-clip-id-' + this.selected_audio_clip.id;
            },
        },
        watch: {
        },
        methods: {
            async handleUnfinishedReplyStoreChange() : Promise<void> {

                const store_status = this.unfinished_reply_store.getStatus;
                const relevant_statuses:StatusValues[] = [
                    "replying", "replying_deleted", "replying_expired"
                ];

                if(
                    relevant_statuses.includes(store_status) === false ||
                    this.unfinished_reply_store.event === null ||
                    this.unfinished_reply_store.event.event.id !== this.event_id
                ){

                    return;
                }

                switch(store_status){

                    //no need to handle replying_successful here

                    case 'replying':

                        if(this.is_this_user_replying === true){

                            //if user opens page when already replying, i.e. normal journey
                            //no need to do anything here
                            break;
                        }

                        //user originally isn't replying, but may now be
                        //i.e. not replying --> tab left open --> triggers replying
                        //we refresh our stale data, and it will evaluate if user is replying
                        this.getEvent();
                        break;

                    case 'replying_deleted':

                        this.is_this_user_replying = false;
                        this.reply_is_deleted = true;
                        this.reply_is_expired = false;
                        this.reply_expiry_interval !== null ? clearInterval(this.reply_expiry_interval) : null;
                        this.reply_expiry_interval = null;
                        break;

                    case 'replying_expired':

                        this.is_this_user_replying = false;
                        this.reply_is_deleted = false;
                        this.reply_is_expired = true;
                        this.reply_expiry_interval !== null ? clearInterval(this.reply_expiry_interval) : null;
                        this.reply_expiry_interval = null;
                        break;

                    default:

                        break;
                }
            },
            async checkUserIsReplying(event:GroupedAudioClipsTypes) : Promise<void> {

                //check if user is supposed to reply to this
                //might not seem important to do this much if journey is standard reply --> open
                //but doing this helps us guarantee, and also handle is_this_user_replying's false --> true

                //basic validation
                if(
                    event.event.id !== this.event_id ||
                    this.user_id === null
                ){

                    return;
                }

                //validate whether user is replying
                if(
                    event.event.is_replying === true &&
                    event.event.locked_for_user !== null &&
                    event.event.locked_for_user.id === this.user_id
                ){

                    //is replying
                    this.is_this_user_replying = true;
                    await this.startReplyExpiryInterval();
                    this.scrollToReplyArea();

                    //patch store
                    this.unfinished_reply_store.$patch({
                        event: event,
                        status: "replying"
                    });

                }else{

                    //is not replying
                    this.is_this_user_replying = false;
                }
            },
            async stopReplying(context:"deleted"|"expired") : Promise<void> {

                if(context === "deleted" && this.is_deleting === true){
                    return;
                }else if(context === "expired" && this.is_expiring === true){
                    return;
                }

                if(context === "deleted"){
                    this.is_deleting = true;
                }else if(context === "expired"){
                    this.is_expiring = true;
                }

                //state handling
                const handler = ()=>{

                    this.is_this_user_replying = false;
                    this.reply_expiry_interval !== null ? clearInterval(this.reply_expiry_interval) : null;

                    if(context === "deleted"){

                        this.is_deleting = false;
                        this.reply_is_deleted = true;

                        //patch store
                        this.unfinished_reply_store.$patch({
                            status: "replying_deleted"
                        });

                    }else if(context === "expired"){

                        this.is_expiring = false;
                        this.reply_is_expired = true;

                        //patch store
                        this.unfinished_reply_store.$patch({
                            status: "replying_expired"
                        });
                    }
                };

                //do API request
                let data = new FormData();
                data.append('event_id', JSON.stringify(this.event_id));

                await axios.post(window.location.origin + '/api/events/reply/delete', data)
                .then(() => {

                })
                .catch((error:any) => {

                    let notify_title = 'Error';
                    let notify_text = '';

                    //401 is when you cannot cancel because you are no longer replying
                    //can happen when cronjob cancels first
                    if('request' in error && 'response' in error){

                        if(error.request.status === 401){

                            return;
                        }

                        notify_text = error.response.data['message'];
                    }

                    if(context === "deleted"){
                        notify_title = "Reply deletion failed";
                    }else if(context === "expired"){
                        notify_title = "Reply expiry failed";
                    }

                    notify({
                        title: notify_title,
                        text: notify_text,
                        type: 'error'
                    }, 4000);

                }).finally(()=>{

                    handler();
                });
            },
            async getEvent() : Promise<void> {

                if(this.event_id === null){

                    return;
                }

                this.event = null;

                //prepare audio_clips, then separate
                await axios.get(window.location.origin + '/api/events/get/' + this.event_id.toString())
                .then((result:any) => {

                    if(result.data['data'].length === 0){

                        return;
                    }

                    //API always returns list, even if there is only one event
                    this.event = result.data['data'][0];

                    //if user is replying, auto-handles everything else
                    this.checkUserIsReplying(result.data['data'][0]);

                })
                .catch((error:any) => {

                    let error_text = '';

                    if('request' in error && 'response' in error){

                        error_text = error.response.data['message'];
                    }

                    notify({
                        title: "Error",
                        text: error_text,
                        type: "error"
                    }, 4000);

                }).finally(()=>{

                    this.is_searching = false;
                });
            },
            async handleIsSubmitSuccessful(new_value:boolean) : Promise<void> {

                if(new_value === true){

                    this.is_this_user_replying = false;
                    this.reply_is_deleted = false;
                    this.reply_is_expired = false;
                    this.reply_expiry_interval !== null ? clearInterval(this.reply_expiry_interval) : null;
                    this.reply_expiry_interval = null;

                    //patch store
                    this.unfinished_reply_store.$patch({
                        status: "replying_successful"
                    });

                    //redirect is taken care of by CreateAudioClips
                }
            },
            async handleIsSubmitting(new_value:boolean) : Promise<void> {

                this.is_submitting = new_value;
            },
            async scrollToReplyArea() : Promise<void> {

                const target = document.getElementById('is-replying-area');
                const nav_bar = document.getElementById('nav-bar-app');

                if(target === null || nav_bar === null){

                    return;
                }

                window.scrollTo({
                    top: Math.round(target.offsetTop - (nav_bar.offsetHeight)),
                    left: target.offsetLeft,
                });
            },
            async handleNewSelectedAudioClip(audio_clip:AudioClipsAndLikeDetailsTypes|null) : Promise<void> {

                this.selected_audio_clip = audio_clip;
            },
            async startReplyExpiryInterval() : Promise<void> {

                if(
                    this.is_this_user_replying === false ||
                    this.event === null ||
                    this.event.event.when_locked === null
                ){

                    return;
                }

                //reset interval, just in case
                this.reply_expiry_interval !== null ? clearInterval(this.reply_expiry_interval) : null;
                this.reply_expiry_interval = null;

                const when_locked_ms = new Date(this.event.event.when_locked);
                const time_elapsed_ms = timeFromNowMS(when_locked_ms);

                //time is up
                if(time_elapsed_ms >= this.reply_expiry_max_ms){

                    this.stopReplying("expired");
                    return;
                }

                //proceed

                //run every 1s if <120s remaining, else run every 60s
                //change this again once sped up
                let interval_ms:number = (
                    (this.reply_expiry_max_ms - time_elapsed_ms) <= this.expiry_interval_checkpoint_ms ?
                    this.fastest_expiry_interval_ms : this.slowest_expiry_interval_ms
                );

                //set possible first time expiry string
                const time_remaining = prettyTimeRemaining(time_elapsed_ms, this.reply_expiry_max_ms);
                this.reply_expiry_string = time_remaining === '' ? '' : time_remaining as string;

                //declare this here for reusability
                const interval_function = ()=>{

                    //get time difference
                    const time_elapsed_ms = timeFromNowMS(when_locked_ms);

                    //time is up
                    if(time_elapsed_ms >= this.reply_expiry_max_ms){
                        
                        this.stopReplying("expired");
                    }

                    //if interval started with >1000, be prepared for reinitialisation for new interval with shorter time
                    if(
                        interval_ms === this.slowest_expiry_interval_ms &&
                        (this.reply_expiry_max_ms - time_elapsed_ms) <= this.expiry_interval_checkpoint_ms
                    ){

                        clearInterval(this.reply_expiry_interval!);

                        this.reply_expiry_interval = window.setInterval(interval_function, this.fastest_expiry_interval_ms);

                        //change interval_ms as lazy way to skip this part after the first time
                        interval_ms = this.fastest_expiry_interval_ms;
                    }

                    //set string
                    const time_remaining = prettyTimeRemaining(time_elapsed_ms, this.reply_expiry_max_ms);
                    this.reply_expiry_string = time_remaining === '' ? '' : time_remaining as string;
                }

                //start interval
                this.reply_expiry_interval = window.setInterval(interval_function, interval_ms);
            },
        },
        beforeMount(){

            //get user_id
            this.user_id = getDataFromTemplateJSONScript('data-user-id') as number|null;

            const container = (document.getElementById('data-container-get-events') as HTMLElement);

            //get essential data first, where we don't proceed if they don't exist
            const audio_clip_choice_expiry_seconds = (container.getAttribute('data-event-reply-choice-expiry-seconds') as string);
            const audio_clip_reply_expiry_seconds = (container.getAttribute('data-event-reply-expiry-seconds') as string);

            if(audio_clip_choice_expiry_seconds === null || audio_clip_reply_expiry_seconds === null){

                //don't proceed because we lack essential data
                console.log('Essential data was not passed into template.');
                return;
            }

            //get data from SSR template
            this.choice_expiry_max_ms = parseInt(audio_clip_choice_expiry_seconds) * 1000;
            this.reply_expiry_max_ms = parseInt(audio_clip_reply_expiry_seconds) * 1000;
            this.event_id = parseInt(container.getAttribute('data-event-id') as string);
            this.is_deleted = JSON.parse(container.getAttribute('data-is-deleted') as string);
            this.audio_clip_count = JSON.parse(container.getAttribute('data-audio-clip-count') as string);
            this.is_this_user_replying = JSON.parse(container.getAttribute('data-is-this-user-replying') as string);

            (async ()=>{
                await this.getEvent().then(()=>{

                    if(this.is_this_user_replying === true){

                        this.startReplyExpiryInterval();
                    }
                });
            })();

            //change '1 Jan 2023' to '1 century ago'
            //we are passing 'YYYY-MM-DD HH:mm:ss' from template
            //for best reliability, Date() expects 'YYYY-MM-DDTHH:mm:ssZ'
            if(container.getElementsByClassName('when-created').length === 1){

                const when_created_element = container.getElementsByClassName('when-created')[0];
                const when_created = (container.getAttribute('data-when-created') as string).replace(/ /g, 'T') + 'Z';
                when_created_element.textContent = prettyTimePassed(new Date(when_created));
            }

            //handle deletion/expiry from elsewhere
            this.unfinished_reply_store.$subscribe(async ()=>{

                await this.handleUnfinishedReplyStoreChange();
            });

            //listen to store
            this.currently_playing_audio_clip_store.$subscribe((mutation, state)=>{

                this.handleNewSelectedAudioClip(state.playing_audio_clip as AudioClipsAndLikeDetailsTypes|null);
            });
        },
    });
</script>