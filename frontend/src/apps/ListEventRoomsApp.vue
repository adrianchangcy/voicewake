<template>
    <div>

        <div class="relative">
            <TransitionGroupFade>

                <!--search and any dialog, or searching skeleton-->
                <div
                    v-show="(canSearch || is_searching || hasUnfinishedReply) && !canChooseReplyChoices"
                    ref="search_button_container"
                    class="w-full h-fit"
                >

                    <!--title-->
                    <!--must be here instead of in parent to prevent jolt-->
                    <VTitle
                        propFontSize="l"
                        class="py-8"
                    >
                        <template #title>
                            <div class="flex flex-col">
                                <i class="fas fa-comments block text-2xl w-full text-center"></i>
                                <span class="block w-full text-center">Reply</span>
                            </div>
                        </template>
                    </VTitle>

                    <TransitionGroupFade>

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
                                <TransitionGroupFade>

                                    <!--no new events-->
                                    <span
                                        v-show="current_simple_dialog === simple_dialogs[0]"
                                        class="w-full h-fit flex flex-col text-xl font-medium text-center text-theme-black"
                                    >
                                        <i class="far fa-face-meh-blank block w-full"></i>
                                        <span class="block w-full">No new events found.</span>
                                    </span>

                                    <!--reply choice expired-->
                                    <span
                                        v-show="current_simple_dialog === simple_dialogs[1]"
                                        class="w-full h-fit flex flex-col text-xl font-medium text-center text-theme-black"
                                    >
                                        <i class="fas fa-hourglass-end block w-full"></i>
                                        <span class="block w-full">The event choice has expired.</span>
                                    </span>
                                </TransitionGroupFade>
                            </div>
                        </div>

                        <!--searching-->
                        <div
                            v-show="is_searching"
                            class="w-full h-fit"
                        >
                            <!--skeleton-->
                            <EventRoomCardSkeleton
                                :prop-event-quantity="1"
                                :prop-can-reply="true"
                            />
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
                                    <span class="block">1 unfinished reply found:</span>
                                </template>
                                <template #content>
                                    <span class="block text-center">
                                        You can search for new event choices after 
                                        completing or deleting your unfinished reply.
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
                                            @click.stop="deletePreviousReply()"
                                            :propIsEnabled="!is_loading"
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
    
                <!--can show reply choices-->
                <div
                    v-show="canChooseReplyChoices"
                    class="w-full h-fit"
                >

                    <i class="fas fa-comments block text-2xl text-theme-black w-full text-center pt-8 pb-4"></i>

                    <!--event_room preview-->
                    <!--must use v-if since EventRoomCard cannot exist with null-->
                    <TransitionFade>
                        <EventRoomCard
                            v-if="canChooseReplyChoices"
                            :propEventRoom="getMainEventRoom"
                            :propShowTitle="true"
                        />
                    </TransitionFade>

                    <div class="w-full h-fit sticky mt-8 grid grid-cols-2 gap-4 items-center">

                        <!--reply-->
                        <div class="col-span-1 justify-self-end">
                            <VActionSpecial
                                @click.stop="confirmReplyChoice(getMainEventRoom)"
                                :propIsEnabled="!is_loading"
                                propElement="button"
                                type="button"
                                propElementSize="xl"
                                propFontSize="xl"
                                :propIsRound="true"
                                class="w-32"
                            >
                                <span>Reply</span>
                            </VActionSpecial>
                        </div>

                        <!--skip-->
                        <div class="col-span-1">
                            <VAction
                                @click.stop="getEventRooms()"
                                :propIsEnabled="canSearch"
                                propElement="button"
                                type="button"
                                propElementSize="xl"
                                propFontSize="xl"
                                :propIsRound="true"
                                class="w-32"
                            >
                                <span>Skip</span>
                            </VAction>
                        </div>
                    </div>
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
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import { timeFromNowMS, prettyTimeRemaining } from '@/helper_functions';
    import anime from 'animejs';
    import EventRoomTypes from '@/types/EventRooms.interface';
    const axios = require('axios');

    export default defineComponent({
        name: "ListEventRoomsApp",
        data() {
            return {
                event_rooms: [] as EventRoomTypes[] | [],
                still_replying_event_room: null as EventRoomTypes | null,
                redirect_url: "",
                main_anime: null as InstanceType<typeof anime> | null,

                expiry_interval: null as number | null,
                expiry_string: "",
                choice_expiry_max_ms: 0,   //will be replaced with SSR data on beforeMount()
                still_replying_expiry_max_ms: 0,   //will be replaced with SSR data on beforeMount()
                shorten_interval_ceiling_ms: 80000,
                slowest_interval_ms: 10000,
                fastest_interval_ms: 1000,

                is_searching: false,
                is_loading: false,

                simple_dialogs: ["no_new_reply_choice", "reply_choice_expired"],
                current_simple_dialog: "",
            };
        },
        computed: {
            getMainEventRoom() : EventRoomTypes|null {

                //only useful for current 1-event-room-per-instance
                //use v-for when > 1 in the future

                if(this.event_rooms.length === 0){

                    return null;

                }else{

                    return this.event_rooms[0];
                }
            },
            stillReplyingExpiryString() : string {

                if(this.expiry_string === ""){

                    return "";
                }

                return this.expiry_string + " to decide";
            },
            replyChoiceExpiryString() : string {

                if(this.expiry_string === ""){

                    return "";
                }

                return this.expiry_string + " to decide";
            },
            hasUnfinishedReply() : boolean {

                return this.still_replying_event_room !== null &&
                    this.is_searching === false &&
                    this.is_loading === false;
            },
            canChooseReplyChoices() : boolean {

                return this.event_rooms.length > 0 &&
                    this.is_searching === false &&
                    this.is_loading === false &&
                    this.hasUnfinishedReply === false;
            },
            canSearch(): boolean {

                return this.still_replying_event_room === null &&
                    this.is_searching === false &&
                    this.is_loading === false;
            },
        },
        methods: {
            async expireReplyChoices(): Promise<void> {

                if(this.is_loading === true){

                    return;
                }

                this.is_loading = true;

                let data = new FormData();
                data.append("to_reply", JSON.stringify(false));

                await axios.post(window.location.origin + "/api/user-actions", data)
                .then(() => {

                    this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                    this.expiry_string = "";
                    this.current_simple_dialog = this.simple_dialogs[1];
                    this.event_rooms = [];
                    this.is_loading = false;
                })
                .catch((error: any) => {

                    this.is_loading = false;
                    console.log(error.response.data["message"]);
                });
            },
            //you can call this for new reply choices, the API will remove previous reply choices for us
            async getEventRooms(): Promise<void> {

                if(!this.canSearch){
                    return;
                }

                //reset
                this.current_simple_dialog = "";
                this.event_rooms = [];
                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_string = "";

                this.is_searching = true;

                await axios.get(window.location.origin + "/api/events/get/event-room/status/incomplete")
                .then((results: any) => {

                    if(results.data["data"].length === 0){

                        //no events
                        this.current_simple_dialog = this.simple_dialogs[0];

                    }else if(results.data["data"].length > 0 && results.data["data"][0]["event_room"]["is_replying"] === true){

                        //user has unfinished reply
                        this.still_replying_event_room = results.data["data"][0];
                        this.redirect_url = "hear/" + this.still_replying_event_room!.event_room.id.toString();
                        this.startExpiryInterval();

                    }else{

                        //user has new reply choices
                        this.event_rooms = results.data["data"];
                        this.startExpiryInterval();
                    }

                    this.is_searching = false;
                })
                .catch((error: any) => {
                    console.log(error.response.data["message"]);
                    this.is_searching = false;
                });
            },
            async deletePreviousReply(): Promise<void> {

                if(this.still_replying_event_room === null || this.is_loading === true){
                    return;
                }

                this.is_loading = true;
                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_string = "";

                //cancel previous reply choice
                let data = new FormData();
                data.append("event_room_id", JSON.stringify(this.still_replying_event_room.event_room.id));
                data.append("to_reply", JSON.stringify(false));

                await axios.post(window.location.origin + "/api/user-actions", data)
                .then(() => {

                    this.still_replying_event_room = null;

                    this.is_loading = false;

                    window.setTimeout(() => {
                        this.getEventRooms();
                    }, 500);
                })
                .catch((error: any) => {

                    this.is_loading = false;
                    console.log(error.response.data["message"]);
                });
            },
            async confirmReplyChoice(event_room: EventRoomTypes|null): Promise<void> {

                if (event_room === null || this.is_searching === true || this.is_loading === true) {

                    return;
                }
                
                this.is_loading = true;
                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_string = "";

                let data = new FormData();
                data.append("event_room_id", JSON.stringify(event_room.event_room.id));
                data.append("to_reply", JSON.stringify(true));

                await axios.post(window.location.origin + "/api/user-actions", data)
                .then((results: any) => {

                    if(results.status === 202){

                        window.location.href = window.location.origin + "/hear/" + event_room.event_room.id.toString();

                    }else{

                        console.log(results);
                    }

                    //don't do is_loading=true here
                })
                .catch((error: any) => {

                    console.log(error.response.data["message"]);
                    this.is_loading = false;
                    this.startExpiryInterval();
                });
            },
            startExpiryInterval(): void {

                let target_event_room: EventRoomTypes | null = null;
                let target_max_ms = 0;

                if(this.still_replying_event_room !== null){

                    target_event_room = this.still_replying_event_room;
                    target_max_ms = this.still_replying_expiry_max_ms;

                }else if(this.event_rooms.length > 0){

                    target_event_room = this.event_rooms[0];
                    target_max_ms = this.choice_expiry_max_ms;

                }else{

                    return;
                }

                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;

                const when_locked_ms = new Date(target_event_room.event_room.when_locked);
                const time_elapsed_ms = timeFromNowMS(when_locked_ms);

                //time is up
                if (time_elapsed_ms >= target_max_ms) {

                    this.still_replying_event_room === null ? this.expireReplyChoices() : this.deletePreviousReply();
                    return;
                }

                //proceed

                //run every 1s if <120s remaining, else run every 60s
                //change this again once sped up
                let interval_ms: number = target_max_ms - time_elapsed_ms <= this.shorten_interval_ceiling_ms ? this.fastest_interval_ms : this.slowest_interval_ms;

                //set possible first time expiry string
                const time_remaining = prettyTimeRemaining(time_elapsed_ms, target_max_ms);
                this.expiry_string = time_remaining === false ? "" : time_remaining as string;

                //declare this here for reusability
                const interval_function = () => {

                    //get time difference
                    const time_elapsed_ms = timeFromNowMS(when_locked_ms);

                    //time is up
                    if (time_elapsed_ms >= target_max_ms) {

                        this.still_replying_event_room === null ? this.expireReplyChoices() : this.deletePreviousReply();
                    }

                    //if interval started with >1000, be prepared for reinitialisation for new interval with shorter time
                    if (interval_ms === this.slowest_interval_ms && target_max_ms - time_elapsed_ms <= this.shorten_interval_ceiling_ms) {

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

            const container = (document.getElementById('data-container-list-event-rooms') as HTMLElement);

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
            this.still_replying_expiry_max_ms = parseInt(event_reply_expiry_seconds) * 1000;
        },
    });
</script>