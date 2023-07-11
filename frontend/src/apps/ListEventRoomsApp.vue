<template>
    <div>

        <!--big title-->
        <VTitleXL class="py-10">
            <template #title>
                <div class="flex flex-col">
                    <i class="fas fa-comments block text-2xl w-full text-center"></i>
                    <span class="block w-full text-center">Reply</span>
                </div>
            </template>
        </VTitleXL>

        <div class="relative">
            <TransitionGroupFade>

                <!--search and any dialog-->
                <div
                    v-show="canSearch"
                    ref="search_button_container"
                    class="w-full h-fit"
                >
                    <!--search-->
                    <VActionSpecial
                        @click.stop="getEventRooms()"
                        :propIsEnabled="canSearch"
                        propElement="button"
                        type="button"
                        propElementSize="xl"
                        propFontSize="xl"
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
                            <VDialogPlain
                                v-show="current_simple_dialog === simple_dialogs[0]"
                                class="w-full"
                            >
                                <template #logo>
                                    <i class="far fa-face-meh-blank block"></i>
                                </template>
                                <template #title>
                                    <span class="block">No new events found</span>
                                </template>
                                <template #content>
                                    <span>Try again in a moment!</span>
                                </template>
                            </VDialogPlain>

                            <!--reply choice expired-->
                            <VDialogPlain
                                v-show="current_simple_dialog === simple_dialogs[1]"
                                class="w-full"
                            >
                                <template #logo>
                                    <i class="fas fa-hourglass-end block"></i>
                                </template>
                                <template #title>
                                    <span class="block">Reply choice expired</span>
                                </template>
                                <template #content>
                                    <span>You ran out of time. Feel free to search again!</span>
                                </template>
                            </VDialogPlain>
                        </TransitionGroupFade>
                    </div>
                </div>

                <!--is_replying dialog-->
                <VDialogPlain
                    v-show="hasUnfinishedReply"
                    class="w-full h-fit"
                >
                    <template #logo>
                        <i class="fas fa-file-audio block"></i>
                    </template>
                    <template #title>
                        <span class="block">Unfinished reply found</span>
                    </template>
                    <template #content>
                        <span class="block text-left">Please complete or delete it before searching for new reply choices.</span>
                        <span v-show="!is_loading" class="block text-left pt-2">{{ stillReplyingExpiryString }}</span>
                        <div
                            class="grid grid-rows-1 grid-cols-4 mt-2 gap-2"
                        >
                            <VActionSpecial
                                propElement="a"
                                :href="redirect_url"
                                propElementSize="s"
                                propFontSize="s"
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
                            >
                                <span class="block mx-auto">Delete</span>
                            </VAction>
                        </div>
                    </template>
                </VDialogPlain>

                <!--searching-->
                <EventRoomCardSkeleton
                    v-show="is_searching"
                    :prop-event-quantity="1"
                    :prop-can-reply="true"
                    class="w-full h-fit"
                />

                <!--can show reply choices-->
                <div v-show="canChooseReplyChoices">
                    <div class="flex flex-col">
                        <div v-for="event_room in event_rooms" :key="event_room.event_room.id">
                            <div class="flex flex-col">
                                <EventRoomCard
                                    :propEventRoom="event_room"
                                    :propShowTitle="true"
                                />
                                <VActionSpecial
                                    @click.stop="confirmReplyChoice(event_room)"
                                    :propIsEnabled="!is_loading"
                                    propElement="button"
                                    type="button"
                                    propElementSize="l"
                                    propFontSize="l"
                                    class="mt-8"
                                >
                                    <span class="block mx-auto">Reply</span>
                                </VActionSpecial>
                                <span v-show="!is_loading" class="w-full h-fit py-2 text-base text-center text-theme-black">
                                    {{ replyChoiceExpiryString }}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </TransitionGroupFade>
        </div>
    </div>
</template>


<script setup lang="ts">
    import VTitleXL from '/src/components/small/VTitleXL.vue';
    import EventRoomCard from '/src/components/main/EventRoomCard.vue';
    import EventRoomCardSkeleton from '@/components/skeleton/EventRoomCardSkeleton.vue';
    import VDialogPlain from '@/components/small/VDialogPlain.vue';
    import VActionSpecial from '@/components/small/VActionSpecial.vue';
    import VAction from '@/components/small/VAction.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
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
                choice_expiry_max_ms: 10 * 60 * 1000,
                still_replying_expiry_max_ms: 30 * 60 * 1000,
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
            stillReplyingExpiryString() : string {

                if(this.expiry_string === ""){

                    return "";
                }

                return this.expiry_string + " to decide:";
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

                this.handleStartLoadingAnime();
                this.is_loading = true;

                let data = new FormData();
                data.append("to_reply", JSON.stringify(false));

                await axios.post(window.location.origin + "/api/user-actions", data)
                .then(() => {

                    this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                    this.expiry_string = "";
                    this.current_simple_dialog = this.simple_dialogs[1];
                    this.event_rooms = [];
                    this.handleEndLoadingAnime();
                    this.is_loading = false;
                })
                .catch((error: any) => {

                    this.handleEndLoadingAnime();
                    this.is_loading = false;
                    console.log(error.response.data["message"]);
                });
            },
            async getEventRooms(): Promise<void> {

                if(!this.canSearch){
                    return;
                }

                //reset
                this.current_simple_dialog = "";
                this.event_rooms = [];
                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_string = "";

                this.handleStartLoadingAnime();
                this.is_searching = true;

                await axios.get(window.location.origin + "/api/events/get/event-room/status/incomplete")
                .then((results: any) => {

                    if(results.data["data"].length === 0){

                        this.current_simple_dialog = this.simple_dialogs[0];

                    }else if(results.data["data"].length > 0 && results.data["data"][0]["event_room"]["is_replying"] === true){

                        this.still_replying_event_room = results.data["data"][0];
                        this.redirect_url = "hear/" + this.still_replying_event_room!.event_room.id.toString();
                        this.startExpiryInterval();

                    }else{

                        this.event_rooms = results.data["data"];
                        this.startExpiryInterval();
                    }

                    this.is_searching = false;
                    this.handleEndLoadingAnime();
                })
                .catch((error: any) => {
                    console.log(error.response.data["message"]);
                    this.is_searching = false;
                    this.handleEndLoadingAnime();
                });
            },
            async deletePreviousReply(): Promise<void> {

                if(this.still_replying_event_room === null || this.is_loading === true){
                    return;
                }

                this.handleStartLoadingAnime();
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

                    this.handleEndLoadingAnime();
                    this.is_loading = false;

                    window.setTimeout(() => {
                        this.getEventRooms();
                    }, 500);
                })
                .catch((error: any) => {

                    this.handleEndLoadingAnime();
                    this.is_loading = false;
                    console.log(error.response.data["message"]);
                });
            },
            async confirmReplyChoice(event_room: EventRoomTypes): Promise<void> {

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
            handleStartLoadingAnime() : void {

                return;
            },
            handleEndLoadingAnime() : void {

                return;
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
        mounted() {
            this.axiosSetup();
        },
    });
</script>