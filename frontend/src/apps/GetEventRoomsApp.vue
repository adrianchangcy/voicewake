<template>
    <div v-if="!is_deleted" class="flex flex-col">

        <div v-if="is_searching" class="flex flex-col gap-8">

            <!--events-->
            <div v-for="x in event_count" :key="x">
                <VEventCardSkeleton/>
            </div>
        </div>

        <div v-else-if="event_room !== null">

            <!--events-->
            <EventRoomCard
                :propEventRoom="event_room"
                :propShowTitle="false"
                @newSelectedEvent=handleNewSelectedEvent($event)
            />

            <!--reply area-->
            <TransitionFadeSlow>
                <div
                    v-if="is_this_user_replying"
                    id="is-replying-area"
                    class="flex flex-col gap-2 pt-10"
                >
                    <VUser
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

                        <CreateEvents
                            :propIsOriginator="false"
                            :propEventRoomId="event_room.event_room.id"
                            :propCanSubmit="canSubmit"
                            @isSubmitting="handleIsSubmitting($event)"
                            @isSubmitSuccessful="handleIsSubmitSuccessful($event)"
                        />
                    </div>
                </div>

                <!--just deleted while replying-->
                <span
                    v-else-if="reply_is_deleted"
                    class="w-full h-fit mt-10 flex flex-col text-xl font-medium text-center text-theme-black"
                >
                    <i class="fas fa-eraser block w-full"></i>
                    <span class="block w-full">Your reply has been deleted.</span>
                    <VActionTextOnly
                        propElement="a"
                        href="/hear"
                        propElementSize="s"
                        propFontSize="s"
                        class="w-fit mx-auto"
                    >
                        <span class="flex flex-row">
                            <span class="font-bold block">More event choices</span>
                            <i class="fas fa-arrow-right block text-2xl pl-2"></i>
                        </span>
                    </VActionTextOnly>
                </span>

                <!--just expired while replying-->
                <span
                    v-else-if="reply_is_expired"
                    class="w-full h-fit mt-10 flex flex-col text-xl font-medium text-center text-theme-black"
                >
                    <i class="fas fa-hourglass-end block w-full"></i>
                    <span class="block w-full">Your reply has expired.</span>
                    <VActionTextOnly
                        propElement="a"
                        href="/hear"
                        propElementSize="s"
                        propFontSize="s"
                        class="w-fit mx-auto"
                    >
                        <span class="flex flex-row">
                            <span class="font-bold block">More event choices</span>
                            <i class="fas fa-arrow-right block text-2xl pl-2"></i>
                        </span>
                    </VActionTextOnly>
                </span>
            </TransitionFadeSlow>

            <div v-if="selected_event !== null">
                <Teleport :to="playback_teleport_id">
                    <VPlayback
                        :propIsOpen="true"
                        :propAudioVolumePeaks="selected_event.audio_volume_peaks"
                        :propAudioURL="selected_event.audio_file"
                        :propBucketQuantity="selected_event.audio_volume_peaks.length"
                        :propEventTone="selected_event.event_tone"
                        :propAutoPlayOnSourceChange="true"
                    />
                </Teleport>
            </div>
        </div>
    </div>
</template>


<script setup lang="ts">
    import EventRoomCard from '@/components/main/EventRoomCard.vue';
    import VActionButtonDangerS from '@/components/small/VActionButtonDangerS.vue';
    import VActionTextOnly from '@/components/small/VActionTextOnly.vue';
    import CreateEvents from '@/components/main/CreateEvents.vue';
    import VTitle from '@/components/small/VTitle.vue';
    import TransitionFadeSlow from '@/transitions/TransitionFadeSlow.vue';
    import VPlayback from '@/components/medium/VPlayback.vue';
    import VUser from '@/components/small/VUser.vue';
    import VEventCardSkeleton from '@/components/skeleton/VEventCardSkeleton.vue';
    import VLoading from '@/components/small/VLoading.vue';
</script>


<script lang="ts">
    import { defineComponent, } from 'vue';
    import { prettyTimePassed, prettyTimeRemaining, getDataFromTemplateJSONScript, timeFromNowMS } from '@/helper_functions';
    import EventRoomTypes from '@/types/EventRooms.interface';
    import EventTypes from '@/types/Events.interface';
    import Statuses from '@/types/values/Statuses';
    import { notify } from 'notiwind';
    import { useUnfinishedReplyStore } from '@/stores/UnfinishedReplyStore';
    const axios = require('axios');

    export default defineComponent({
        name: 'GetEventRoomsApp',
        data() {
            return {
                unfinished_reply_store: useUnfinishedReplyStore(),

                user_id: null as number|null,
                event_room_id: null as number|null,
                event_count: 0, //from DOM
                is_this_user_replying: false,
                is_deleted: false,

                reply_is_deleted: false,    //set True once, only to show message
                reply_is_expired: false,  //set True once, only to show message

                event_room: null as EventRoomTypes|null,

                is_searching: false,
                is_deleting: false,
                is_expiring: false,
                is_submitting: false,
                
                selected_event: null as EventTypes|null,
                playback_teleport_id: '',
                reply_expiry_interval: null as number|null,
                reply_expiry_string: '',

                choice_expiry_max_ms: 0,   //will be replaced with SSR data on beforeMount()
                reply_expiry_max_ms: 0, //will be replaced with SSR data on beforeMount()
                minimum_ms_to_speed_up_interval: 80000, //transitions from minute to seconds smoothly
                slowest_interval_ms: 10000,
                fastest_interval_ms: 1000,
            };
        },
        computed: {

            canSubmit() : boolean {

                return this.is_this_user_replying === true && this.is_searching === false &&
                    this.is_deleting === false && this.is_expiring === false && this.is_submitting === false;
            },
            canDelete() : boolean {

                return this.canSubmit;
            }
        },
        watch: {
        },
        methods: {
            handleUnfinishedReplyStoreChange() : void {

                const store_status = this.unfinished_reply_store.getStatus;
                const relevant_statuses:Statuses[] = [
                    "replying", "replying_deleted", "replying_expired"
                ];

                if(
                    relevant_statuses.includes(store_status) === false ||
                    this.unfinished_reply_store.event_room === null ||
                    this.unfinished_reply_store.event_room.event_room.id !== this.event_room_id
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
                        this.getEventRoom();
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
            checkUserIsReplying(event_room:EventRoomTypes){

                //check if user is supposed to reply to this
                //might not seem important to do this much if journey is standard reply --> open
                //but doing this helps us guarantee, and also handle is_this_user_replying's false --> true

                //basic validation
                if(
                    event_room.event_room.id !== this.event_room_id ||
                    this.user_id === null
                ){

                    return;
                }

                //validate whether user is replying
                if(
                    event_room.event_room.is_replying === true &&
                    event_room.event_room.locked_for_user.id === this.user_id
                ){

                    //is replying
                    this.is_this_user_replying = true;
                    this.startReplyExpiryInterval();
                    this.scrollToReplyArea();

                    //patch store
                    this.unfinished_reply_store.$patch({
                        event_room: event_room,
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

                //do API request
                let data = new FormData();
                data.append('event_room_id', JSON.stringify(this.event_room_id));
                data.append('to_reply', JSON.stringify(false));

                await axios.post(window.location.origin + '/api/user-actions', data)
                .then(() => {

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

                })
                .catch((error:any) => {

                    if(context === "deleted"){
                        this.is_deleting = false;
                    }else if(context === "expired"){
                        this.is_expiring = false;
                    }

                    notify({
                        title: "Deleting reply failed",
                        text: error.response.data['message'],
                        type: "error"
                    }, 3000);
                });
            },
            async getEventRoom() : Promise<void> {

                if(this.event_room_id === null){

                    return;
                }

                this.is_searching = true;

                //prepare events, then separate
                await axios.get(window.location.origin + '/api/events/get/event-room/' + this.event_room_id.toString())
                .then((results:any) => {

                    if(results.data['data'].length === 0){

                        this.is_searching = false;
                        return;
                    }

                    //API always returns list, even if there is only one event_room
                    this.event_room = results.data['data'][0];

                    //if user is replying, auto-handles everything else
                    this.checkUserIsReplying(results.data['data'][0]);
                    this.is_searching = false;
                })
                .catch((error:any) => {

                    notify({
                        title: "Event search failed",
                        text: error.response.data['message'],
                        type: "error"
                    }, 3000);
                    this.is_searching = false;
                });
            },
            handleIsSubmitSuccessful(new_value:boolean) : void {

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

                    //redirect is taken care of by CreateEvents
                }
            },
            handleIsSubmitting(new_value:boolean) : void {

                this.is_submitting = new_value;
            },
            scrollToReplyArea() : void {

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
            handleNewSelectedEvent(event:EventTypes|null) : void {

                this.selected_event = event;

                if(event !== null){

                    //must be the same as in VEventCard
                    this.playback_teleport_id = '#playback-teleport-' + event.id.toString();
                }
            },
            startReplyExpiryInterval() : void {

                if(this.is_this_user_replying === false){

                    return;
                }

                //reset interval, just in case
                this.reply_expiry_interval !== null ? clearInterval(this.reply_expiry_interval) : null;
                this.reply_expiry_interval = null;

                const when_locked_ms = new Date(this.event_room!.event_room.when_locked);
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
                    (this.reply_expiry_max_ms - time_elapsed_ms) <= this.minimum_ms_to_speed_up_interval ?
                    this.fastest_interval_ms : this.slowest_interval_ms
                );

                //set possible first time expiry string
                const time_remaining = prettyTimeRemaining(time_elapsed_ms, this.reply_expiry_max_ms);
                this.reply_expiry_string = time_remaining === false ? '' : time_remaining as string;

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
                        interval_ms === this.slowest_interval_ms &&
                        (this.reply_expiry_max_ms - time_elapsed_ms) <= this.minimum_ms_to_speed_up_interval
                    ){

                        clearInterval(this.reply_expiry_interval!);

                        this.reply_expiry_interval = window.setInterval(interval_function, this.fastest_interval_ms);

                        //change interval_ms as lazy way to skip this part after the first time
                        interval_ms = this.fastest_interval_ms;
                    }

                    //set string
                    const time_remaining = prettyTimeRemaining(time_elapsed_ms, this.reply_expiry_max_ms);
                    this.reply_expiry_string = time_remaining === false ? '' : time_remaining as string;
                }

                //start interval
                this.reply_expiry_interval = window.setInterval(interval_function, interval_ms);
            },
            axiosSetup() : boolean {

                //your template must have {% csrf_token %}
                const token = document.getElementsByName("csrfmiddlewaretoken")[0];

                if(token === undefined){

                    console.log('CSRF not found.');
                    return false;
                }

                axios.defaults.headers.common['X-CSRFToken'] = (token as HTMLFormElement).value;
                axios.defaults.headers.post['Content-Type'] = 'multipart/form-data';
                return true;
            },
        },
        beforeMount(){

            //prepare axios
            this.axiosSetup();

            //get user_id
            this.user_id = getDataFromTemplateJSONScript('data-user-id') as number|null;

            const container = (document.getElementById('data-container-get-event-rooms') as HTMLElement);

            //get essential data first, where we don't proceed if they don't exist
            const event_choice_expiry_seconds = (container.getAttribute('data-event-choice-expiry-seconds') as string);
            const event_reply_expiry_seconds = (container.getAttribute('data-event-reply-expiry-seconds') as string);

            if(event_choice_expiry_seconds === null || event_reply_expiry_seconds === null){

                //don't proceed because we lack essential data
                console.log('Essential data was not passed into template.');
                return;
            }

            //get data from SSR template
            this.choice_expiry_max_ms = parseInt(event_choice_expiry_seconds) * 1000;
            this.reply_expiry_max_ms = parseInt(event_reply_expiry_seconds) * 1000;
            this.event_room_id = parseInt(container.getAttribute('data-event-room-id') as string);
            this.is_deleted = JSON.parse(container.getAttribute('data-is-deleted') as string);
            this.event_count = JSON.parse(container.getAttribute('data-event-count') as string);

            //if not deleted, get everything
            if(this.is_deleted === false){

                this.getEventRoom();
            }

            //change '1 Jan 2023' to '1 century ago'
            //we are passing 'YYYY-MM-DD HH:mm:ss' from template
            //for best reliability, Date() expects 'YYYY-MM-DDTHH:mm:ssZ'
            if(container.getElementsByClassName('when-created').length === 1){

                const when_created_element = container.getElementsByClassName('when-created')[0];
                const when_created = (container.getAttribute('data-when-created') as string).replace(/ /g, 'T') + 'Z';
                when_created_element.textContent = prettyTimePassed(new Date(when_created));
            }

            //handle deletion/expiry from elsewhere
            this.unfinished_reply_store.$subscribe(()=>{

                this.handleUnfinishedReplyStoreChange();
            });
        },
    });
</script>