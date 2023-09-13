<template>
    <div class="text-theme-black">

        <!--title-->
        <!--logo only here, since "Reply" goes away for certain parts, and putting it here would make things jolt-->
        <!--you can find "Reply" at areas that need it instead-->
        <VTitle
            propFontSize="l"
            class="pt-8"
        >
            <template #title>
                <div class="flex flex-col">
                    <i class="fas fa-comments text-2xl w-full text-center"></i>
                </div>
            </template>
        </VTitle>

        <!--content-->
        <div class="relative">

            <TransitionGroupFade
                :propHasAbsolute="true"
            >

                <!--search and any dialog-->
                <div
                    v-show="(canSearch || hasUnfinishedReply) && !canChooseReplyChoices"
                    class="w-full h-fit"
                >

                    <VTitle
                        propFontSize="l"
                        class="pb-8"
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
                    <TransitionGroupFade
                        :propHasAbsolute="true"
                    >

                        <!--can search-->
                        <div
                            v-show="canSearch"
                            class="w-full h-fit"
                        >
                            <!--search-->
                            <VActionSpecial
                                @click.stop="getEventRooms()"
                                :propIsEnabled="canSearch"
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
                            <div class="mt-10 relative">

                                <TransitionGroupFade
                                    :propHasAbsolute="true"
                                >

                                    <!--no new events-->
                                    <span
                                        v-show="current_simple_dialog === simple_dialogs[0]"
                                        class="w-full h-fit flex flex-col text-center text-theme-black"
                                    >
                                        <i class="far fa-face-meh-blank block w-full text-xl"></i>
                                        <span class="block w-full text-xl font-medium">No new events found.</span>
                                        <span class="block w-full text-base">Search again in a moment!</span>
                                    </span>

                                    <!--reply choice expired-->
                                    <span
                                        v-show="current_simple_dialog === simple_dialogs[1]"
                                        class="w-full h-fit flex flex-col text-center text-theme-black"
                                    >
                                        <i class="fas fa-hourglass-end block w-full text-xl"></i>
                                        <span class="block w-full text-xl font-medium">Event choice has expired.</span>
                                        <span class="block w-full text-base">Search again for more!</span>
                                    </span>
                                </TransitionGroupFade>
                            </div>
                        </div>

                        <!--is_replying dialog-->
                        <div
                            v-show="hasUnfinishedReply"
                            class="w-full h-fit"
                        >

                            <!--dialog to complete or delete unfinished reply before continuing-->
                            <VDialogPlain
                                class="w-full h-fit"
                            >
                                <template #title>
                                    <span class="block">1 unfinished reply found</span>
                                </template>
                                <template #content>
                                    <span class="block text-center">
                                        Please open and complete, or delete, before searching.
                                    </span>
                                    <div
                                        class="grid grid-rows-1 grid-cols-2 mt-4 gap-2"
                                    >
                                        <VActionSpecial
                                            propElement="a"
                                            :href="redirect_url"
                                            propElementSize="s"
                                            propFontSize="s"
                                            class="col-span-1"
                                        >
                                            <span class="block mx-auto">Open</span>
                                        </VActionSpecial>
                                        <VAction
                                            @click.stop="deleteUnfinishedReply()"
                                            :propIsEnabled="!is_unfinished_reply_deleting"
                                            propElement="button"
                                            type="button"
                                            propElementSize="s"
                                            propFontSize="s"
                                            class="col-span-1"
                                        >
                                            <span class="block mx-auto">Delete</span>
                                        </VAction>
                                    </div>
                                </template>
                            </VDialogPlain>
                        </div>
                    </TransitionGroupFade>
                </div>

                <!--all loading-related stuff-->
                <div
                    v-show="isLoading"
                    class="w-full h-fit"
                >

                    <TransitionGroupFade
                        :propHasAbsolute="true"
                    >

                        <!--searching-->
                        <div
                            v-show="is_searching"
                            class="w-full h-fit"
                        >
                            <!--reply/skip skeleton-->
                            <div class="w-full h-fit grid grid-cols-2 gap-4 pb-8">
                                <div class="col-span-1 justify-self-end">
                                    <div class="w-24 h-24 rounded-full skeleton"></div>
                                </div>
                                <div class="col-span-1">
                                    <div class="w-24 h-24 rounded-full skeleton"></div>
                                </div>
                            </div>
                            <!--event room skeleton-->
                            <EventRoomCardSkeleton
                                :prop-has-border="true"
                                :prop-event-quantity="1"
                            />
                        </div>

                        <!--deleting unfinished reply-->
                        <div
                            v-show="is_unfinished_reply_deleting"
                            class="w-full h-fit"
                        >

                            <VTitle
                                propFontSize="l"
                                class="pb-8"
                            >
                                <template #title>
                                    <div class="flex flex-col">
                                        <span class="block w-full text-center">
                                            Reply
                                        </span>
                                    </div>
                                </template>
                            </VTitle>

                            <div class="w-full h-40 flex items-center text-xl font-medium">
                                <div class="w-full flex flex-col">
                                    <i class="fas fa-eraser block mx-auto animate-pulse"></i>
                                    <span class="block mx-auto">Deleting unfinished reply...</span>
                                </div>
                            </div>
                        </div>

                        <!--confirming new reply choice-->
                        <div
                            v-show="is_new_reply_choice_confirming"
                            class="w-full h-fit"
                        >

                            <VTitle
                                propFontSize="l"
                                class="pb-8"
                            >
                                <template #title>
                                    <div class="flex flex-col">
                                        <span class="block w-full text-center">
                                            Reply
                                        </span>
                                    </div>
                                </template>
                            </VTitle>

                            <div class="w-full h-40 flex items-center text-xl font-medium">
                                <div class="w-full flex flex-col">
                                    <VLoading
                                        propElementSize="m"
                                        class="mx-auto"
                                    />
                                    <span class="mx-auto">Confirming reply choice...</span>
                                </div>
                            </div>
                        </div>

                        <!--expiring new reply choice-->
                        <div
                            v-show="is_expiry_loading"
                            class="w-full h-fit"
                        >

                            <VTitle
                                propFontSize="l"
                                class="pb-8"
                            >
                                <template #title>
                                    <div class="flex flex-col">
                                        <span class="block w-full text-center">
                                            Reply
                                        </span>
                                    </div>
                                </template>
                            </VTitle>

                            <div class="w-full h-40 flex items-center text-xl font-medium">
                                <div class="w-full flex flex-col">
                                    <VLoading
                                        propElementSize="m"
                                        class="mx-auto"
                                    />
                                    <span class="mx-auto">Loading...</span>
                                </div>
                            </div>
                        </div>

                    </TransitionGroupFade>
                </div>

                <!--can show reply choices-->
                <div
                    v-show="canChooseReplyChoices"
                    class="w-full h-fit"
                >

                    <div class="w-full h-fit pb-8 grid grid-cols-2 gap-4">

                        <!--reply-->
                        <div class="col-span-1 justify-self-end">
                            <VActionSpecial
                                @click.stop="confirmReplyChoice(getMainEventRoom)"
                                :propIsEnabled="!is_new_reply_choice_confirming"
                                propElement="button"
                                type="button"
                                propElementSize="l"
                                propFontSize="m"
                                :propIsRound="true"
                                class="w-24"
                            >
                                <span class="block mx-auto">Reply</span>
                            </VActionSpecial>
                        </div>

                        <!--skip-->
                        <div class="col-span-1">
                            <VAction
                                @click.stop="getEventRooms()"
                                :propIsEnabled="canSearch"
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

                    <!--event_room preview-->
                    <!--must use v-if since EventRoomCard cannot exist with null-->
                    <TransitionFade>
                        <EventRoomCard
                            v-if="canChooseReplyChoices"
                            :propEventRoom="getMainEventRoom"
                            :propShowTitle="true"
                            :propHasBorder="true"
                        />
                    </TransitionFade>
                </div>
            </TransitionGroupFade>
        </div>
    </div>
</template>


<script setup lang="ts">
    import VTitle from '/src/components/small/VTitle.vue';
    import EventRoomCard from '/src/components/main/EventRoomCard.vue';
    import EventRoomCardSkeleton from '@/components/skeleton/EventRoomCardSkeleton.vue';
    import VActionSpecial from '@/components/small/VActionSpecial.vue';
    import VAction from '@/components/small/VAction.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VDialogPlain from '/src/components/small/VDialogPlain.vue';
    import VLoading from '/src/components/small/VLoading.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import { timeFromNowMS, prettyTimeRemaining } from '@/helper_functions';
    import { notify } from 'notiwind';
    import GroupedEventsTypes from '@/types/GroupedEvents.interface';
    import StatusValues from '@/types/values/StatusValues';
    import { useUnfinishedReplyStore } from '@/stores/UnfinishedReplyStore';

    const axios = require('axios');

    export default defineComponent({
        name: "ListEventRoomChoicesApp",
        data() {
            return {
                unfinished_reply_store: useUnfinishedReplyStore(),

                new_reply_choice_event_rooms: [] as GroupedEventsTypes[] | [],
                unfinished_reply_event_room: null as GroupedEventsTypes | null,
                redirect_url: "",

                expiry_interval: null as number | null,
                expiry_string: "",
                new_reply_choice_expiry_max_ms: 0,   //will be replaced with SSR data on beforeMount()
                unfinished_reply_expiry_max_ms: 0,   //will be replaced with SSR data on beforeMount()
                shorten_interval_ceiling_ms: 80000, //when to switch from slowest_interval_ms to fastest_interval_ms
                slowest_interval_ms: 10000,
                fastest_interval_ms: 1000,

                is_searching: false,
                is_unfinished_reply_deleting: false,
                is_expiry_loading: false,
                is_new_reply_choice_confirming: false,

                simple_dialogs: ["no_reply_choices", "choosing_event_choice_expired", "reply_deleted"] as StatusValues[],
                current_simple_dialog: "",
            };
        },
        computed: {
            getMainEventRoom() : GroupedEventsTypes|null {

                //only useful for current 1-event-room-per-instance
                //use v-for when > 1 in the future

                if(this.new_reply_choice_event_rooms.length === 0){

                    return null;

                }else{

                    return this.new_reply_choice_event_rooms[0];
                }
            },
            isLoading() : boolean {
                return this.is_searching === true || this.is_unfinished_reply_deleting === true ||
                    this.is_expiry_loading === true || this.is_new_reply_choice_confirming === true;
            },
            hasUnfinishedReply() : boolean {

                return this.unfinished_reply_event_room !== null && this.isLoading === false;
            },
            canChooseReplyChoices() : boolean {

                return this.new_reply_choice_event_rooms.length > 0 && this.hasUnfinishedReply === false &&
                    this.isLoading === false;
            },
            canSearch() : boolean {

                return this.unfinished_reply_event_room === null && this.isLoading === false;
            },
        },
        methods: {
            handleUnfinishedReplyStoreChange() : void {

                const store_status = this.unfinished_reply_store.getStatus;
                const extra_allowed_store_status:StatusValues[] = [
                    "replying", "replying_deleted", "replying_expired", "replying_successful"
                ];

                //store_status must be "", or
                if(
                    this.simple_dialogs.includes(store_status) === false &&
                    extra_allowed_store_status.includes(store_status) === false
                ){

                    return;
                }

                switch(store_status){

                    case 'choosing_event_choice_expired':

                        this.current_simple_dialog = store_status;
                        this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                        this.expiry_interval = null;
                        this.new_reply_choice_event_rooms = [];
                        this.unfinished_reply_event_room = null;
                        break;

                    case 'replying_deleted':

                        this.current_simple_dialog = store_status;
                        this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                        this.expiry_interval = null;
                        this.new_reply_choice_event_rooms = [];
                        this.unfinished_reply_event_room = null;
                        break;

                    case 'replying_expired':

                        this.current_simple_dialog = "";
                        this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                        this.expiry_interval = null;
                        this.new_reply_choice_event_rooms = [];
                        this.unfinished_reply_event_room = null;
                        break;

                    case 'replying':

                        this.current_simple_dialog = "";
                        this.new_reply_choice_event_rooms = [];
                        break;

                    case 'replying_successful':

                        this.current_simple_dialog = "";
                        this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                        this.expiry_interval = null;
                        this.new_reply_choice_event_rooms = [];
                        this.unfinished_reply_event_room = null;
                        break;

                    default:

                        break;
                }
            },
            async doExpire(context:"unfinished_reply"|"new_reply_choices"): Promise<void> {

                if(this.is_expiry_loading === true){

                    return;
                }

                this.is_expiry_loading = true;

                let data = new FormData();
                const specific_url = context === "unfinished_reply" ? "reply/cancel" : "reply-choices/expire";

                if(context === "unfinished_reply" && this.unfinished_reply_event_room !== null){

                    data.append("event_room_id", JSON.stringify(this.unfinished_reply_event_room.event_room.id));
                }


                await axios.post(window.location.origin + "/api/event-rooms/" + specific_url, data)
                .then(() => {

                    this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                    this.expiry_string = "";
                    this.current_simple_dialog = this.simple_dialogs[1];
                    this.new_reply_choice_event_rooms = [];
                    this.is_expiry_loading = false;

                    //patch store
                    if(context === "unfinished_reply"){

                        this.unfinished_reply_store.$patch({
                            status: "replying_expired"
                        });
                    
                    }else{

                        this.unfinished_reply_store.$patch({
                            event_room: null,
                            status: "choosing_event_choice_expired"
                        });
                    }
                })
                .catch(() => {

                    //whether expiring fails or not,
                    //it is better to reset as usual to prevent any further confusing actions
                    this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                    this.expiry_string = "";
                    this.current_simple_dialog = this.simple_dialogs[1];
                    this.new_reply_choice_event_rooms = [];
                    this.is_expiry_loading = false;

                    //patch store
                    if(context === "unfinished_reply"){

                        this.unfinished_reply_store.$patch({
                            status: "replying_expired"
                        });
                    
                    }else{

                        this.unfinished_reply_store.$patch({
                            event_room: null,
                            status: "choosing_event_choice_expired"
                        });
                    }
                });
            },
            //you can call this for new reply choices, the API will remove previous reply choices for us
            async getEventRooms(): Promise<void> {

                if(this.canSearch === false){

                    return;
                }

                //reset
                this.current_simple_dialog = "";
                this.new_reply_choice_event_rooms = [];
                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_string = "";

                this.is_searching = true;

                await axios.post(window.location.origin + "/api/event-rooms/reply-choices/list")
                .then((results: any) => {

                    if(results.data["data"].length === 0){

                        //no events
                        this.current_simple_dialog = this.simple_dialogs[0];

                        //reset
                        //patch store
                        this.unfinished_reply_store.$patch({
                            event_room: null,
                            status: "no_reply_choices"
                        });

                    }else if(results.data["data"].length > 0 && results.data["data"][0]["event_room"]["is_replying"] === true){

                        //user has unfinished reply
                        this.unfinished_reply_event_room = results.data["data"][0];
                        this.redirect_url = "hear/" + this.unfinished_reply_event_room!.event_room.id.toString();
                        this.startExpiryInterval("unfinished_reply");

                        //patch store
                        this.unfinished_reply_store.$patch({
                            event_room: results.data["data"][0],
                            status: "replying"
                        });

                    }else{

                        //user has new reply choices
                        this.new_reply_choice_event_rooms = results.data["data"];
                        this.startExpiryInterval("new_reply_choices");

                        //patch store
                        this.unfinished_reply_store.$patch({
                            event_room: null,
                            status: "choosing_event_choice"
                        });
                    }

                    this.is_searching = false;
                })
                .catch((error: any) => {

                    this.is_searching = false;

                    notify({
                        title: "Event search failed",
                        text: error.response.data['message'],
                        type: "error"
                    }, 3000);
                });
            },
            async deleteUnfinishedReply(): Promise<void> {

                if(this.unfinished_reply_event_room === null || this.is_unfinished_reply_deleting === true){
                    return;
                }

                this.is_unfinished_reply_deleting = true;
                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_string = "";

                //cancel previous reply choice
                let data = new FormData();
                data.append("event_room_id", JSON.stringify(this.unfinished_reply_event_room.event_room.id));

                await axios.post(window.location.origin + "/api/event-rooms/reply/cancel", data)
                .then(() => {

                    this.is_unfinished_reply_deleting = false;
                    this.unfinished_reply_event_room = null;

                    //patch store
                    this.unfinished_reply_store.$patch({
                        status: "replying_deleted"
                    });

                    //auto-search
                    this.getEventRooms();
                })
                .catch((error: any) => {

                    this.is_unfinished_reply_deleting = false;

                    notify({
                        title: "Deleting reply failed",
                        text: error.response.data['message'],
                        type: "error"
                    }, 3000);
                });
            },
            async confirmReplyChoice(event_room: GroupedEventsTypes|null): Promise<void> {

                if (event_room === null || this.is_new_reply_choice_confirming === true){

                    return;
                }
                
                this.is_new_reply_choice_confirming = true;
                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_string = "";

                let data = new FormData();
                data.append("event_room_id", JSON.stringify(event_room.event_room.id));

                await axios.post(window.location.origin + "/api/event-rooms/reply/start", data)
                .then((results: any) => {

                    if(results.status === 202){

                        //store unfinished reply
                        //we have no backend<-->store relation to trigger reset when server deems it expired
                        //so we just override the store when user confirms reply choice, only possible without unfinished reply
                        //patch store
                        this.unfinished_reply_store.$patch({
                            event_room: this.getMainEventRoom,
                            status: "replying"
                        });

                        //redirect
                        window.location.href = window.location.origin + "/hear/" + event_room.event_room.id.toString();

                    }else{

                        this.is_new_reply_choice_confirming = false;

                        notify({
                            title: "Reply confirmation failed",
                            text: results.data['message'],
                            type: "error"
                        }, 3000);
                    }

                })
                .catch((error: any) => {

                    //restart expiry interval
                    this.is_new_reply_choice_confirming = false;
                    this.startExpiryInterval("new_reply_choices");

                    notify({
                        title: "Reply confirmation failed",
                        text: error.response.data['message'],
                        type: "error"
                    }, 3000);
                });
            },
            startExpiryInterval(context:"new_reply_choices"|"unfinished_reply"): void {

                let target_event_room: GroupedEventsTypes | null = null;
                let target_max_ms = 0;

                if(
                    context === "unfinished_reply" &&
                    this.unfinished_reply_event_room !== null
                ){

                    target_event_room = this.unfinished_reply_event_room;
                    target_max_ms = this.unfinished_reply_expiry_max_ms;

                }else if(context === "new_reply_choices" && this.new_reply_choice_event_rooms.length > 0){

                    target_event_room = this.new_reply_choice_event_rooms[0];
                    target_max_ms = this.new_reply_choice_expiry_max_ms;

                }else{

                    return;
                }

                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_interval = null;

                //check when_locked
                if(target_event_room.event_room.when_locked === null){

                    return;
                }

                const when_locked_ms = new Date(target_event_room.event_room.when_locked);
                const time_elapsed_ms = timeFromNowMS(when_locked_ms);

                //time is up
                if (time_elapsed_ms >= target_max_ms) {

                    this.unfinished_reply_event_room === null ? this.doExpire(context) : this.deleteUnfinishedReply();
                    return;
                }

                //proceed

                //run every 1s if <120s remaining, else run every 60s
                //change this again once sped up
                let interval_ms:number = (
                    (target_max_ms - time_elapsed_ms) <= this.shorten_interval_ceiling_ms ?
                    this.fastest_interval_ms : this.slowest_interval_ms
                );

                //set possible first time expiry string
                const time_remaining = prettyTimeRemaining(time_elapsed_ms, target_max_ms);
                this.expiry_string = time_remaining === false ? "" : time_remaining as string;

                //declare this here for reusability
                const interval_function = () => {

                    //get time difference
                    const time_elapsed_ms = timeFromNowMS(when_locked_ms);

                    //time is up
                    if (time_elapsed_ms >= target_max_ms) {

                        this.unfinished_reply_event_room === null ? this.doExpire(context) : this.deleteUnfinishedReply();
                    }

                    //if interval started with >1000, reinitialise itself for new interval with shorter time
                    if (
                        interval_ms === this.slowest_interval_ms &&
                        (target_max_ms - time_elapsed_ms) <= this.shorten_interval_ceiling_ms
                    ){

                        clearInterval(this.expiry_interval!);

                        this.expiry_interval = window.setInterval(interval_function, this.fastest_interval_ms);

                        //change interval_ms as a lazy way to ensure this 'if' block runs once only
                        interval_ms = this.fastest_interval_ms;
                    }

                    //set string
                    const time_remaining = prettyTimeRemaining(time_elapsed_ms, target_max_ms);
                    this.expiry_string = time_remaining === false ? "" : time_remaining as string;
                };

                //start interval
                this.expiry_interval = window.setInterval(interval_function, interval_ms);
            },
            axiosSetup(): boolean {
                //your template must have {% csrf_token %}
                let token = document.getElementsByName("csrfmiddlewaretoken")[0];
                if (token === undefined) {
                    console.log("CSRF not found.");
                    return false;
                }
                axios.defaults.headers.common["X-CSRFToken"] = (token as HTMLFormElement).value;
                axios.defaults.headers.post["Content-Type"] = "multipart/form-data";
                return true;
            },
        },
        beforeMount(){

            this.axiosSetup();

            const container = (document.getElementById('data-container-list-event-room-choices') as HTMLElement);

            //get essential data first, where we don't proceed if they don't exist
            const event_choice_expiry_seconds = (container.getAttribute('data-event-room-reply-choice-expiry-seconds') as string);
            const event_reply_expiry_seconds = (container.getAttribute('data-event-room-reply-expiry-seconds') as string);

            if(event_choice_expiry_seconds === null || event_reply_expiry_seconds === null){

                //don't proceed because we lack essential data
                console.log('Essential data was not passed into template.');
                return;
            }

            //get data from SSR template
            this.new_reply_choice_expiry_max_ms = parseInt(event_choice_expiry_seconds) * 1000;
            this.unfinished_reply_expiry_max_ms = parseInt(event_reply_expiry_seconds) * 1000;

            //handle unfinished reply being cancelled/expired from elsewhere
            this.unfinished_reply_store.$subscribe(()=>{

                this.handleUnfinishedReplyStoreChange();
            });
        },
    });
</script>