<template>
    <div>
        <!--big title-->
        <VTitleXL
            :class="mustShrinkTitle ? '-translate-y-8' : 'translate-y-0'"
            class="py-10 transition-transform"
        >
            <template #title>
                <div class="flex flex-col">
                    <i class="fas fa-comments block text-xl w-full text-center"></i>
                    <span class="block w-full text-center">Reply</span>
                </div>
            </template>
        </VTitleXL>

        <!--search button and potential dialog after hiding it-->
        <div>

            <!--search-->
            <!--don't show if user has is_replying choice-->
            <div
                v-show="!stillReplying"
                ref="search_button_container"
                :class="[
                    mustShrinkTitle ? '-translate-y-24' : 'translate-y-0',
                    'transition-transform'
                ]"
            >
                <VActionButtonSpecialXL
                    :propIsEnabled="canSearch"
                    :propIsSmaller="mustShrinkTitle"
                    @click.stop="getEventRooms()"
                    class="mx-auto"
                >
                    {{ search_button_text }}
                </VActionButtonSpecialXL>
            </div>

            <!--is_replying dialog-->
            <VDialogPlain
                v-if="stillReplying"
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
                        <VActionSpecialS
                            propElement="a"
                            :href="redirect_url"
                            class="col-span-2 flex items-center"
                        >
                            <span class="text-base font-medium mx-auto">Open</span>
                        </VActionSpecialS>
                        <VActionButtonS
                            @click.stop="deletePreviousReply()"
                            :propIsEnabled="!is_loading"
                            class="col-span-2 flex items-center"
                        >
                            <span class="text-base font-medium mx-auto">Delete</span>
                        </VActionButtonS>
                    </div>
                </template>
            </VDialogPlain>
        </div>

        <!--content-->
        <div
            :class="mustShrinkTitle ? '-translate-y-24' : 'translate-y-0'"
            class="transition-transform"
        >

            <!--searching-->
            <EventRoomCardSkeleton
                v-show="is_searching"
                :prop-event-quantity="1"
                :prop-can-reply="true"
            />

            <!--can show reply choices-->
            <div v-show="!is_searching && hasReplyChoices && !stillReplying">
                <div class="flex flex-col">
                    <div v-for="event_room in event_rooms" :key="event_room.event_room.id">
                        <div class="flex flex-col">
                            <EventRoomCard
                                :propEventRoom="event_room"
                                :propShowTitle="true"
                            />
                            <VActionButtonSpecialL
                                :prop-is-enabled="!is_loading"
                                @click.stop="confirmReplyChoice(event_room)"
                                class="mt-8"
                            >
                                Reply
                            </VActionButtonSpecialL>
                            <span v-show="!is_loading" class="w-full h-fit py-2 text-base text-center text-theme-black">
                                {{ replyChoiceExpiryString }}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!--for dialogs that don't involve hiding 'search' button-->
        <VDialogPlain
            v-show="hasDetailsForDialog"
            class="mt-10"
        >
            <template #logo>
                <i class="block" :class="details_logo"></i>
            </template>
            <template #title>
                <span class="block">{{ details_title }}</span>
            </template>
            <template #content>
                <span>{{ details_content }}</span>
            </template>
        </VDialogPlain>
    </div>
</template>


<script setup lang="ts">
    import VTitleXL from '/src/components/small/VTitleXL.vue';
    import VActionButtonSpecialXL from '/src/components/small/VActionButtonSpecialXL.vue';
    import VActionSpecialS from '/src/components/small/VActionSpecialS.vue';
    import VActionButtonS from '/src/components/small/VActionButtonS.vue';
    import VActionButtonSpecialL from '@/components/small/VActionButtonSpecialL.vue';
    import EventRoomCard from '/src/components/main/EventRoomCard.vue';
    import EventRoomCardSkeleton from '@/components/skeleton/EventRoomCardSkeleton.vue';
    import VDialogPlain from '@/components/small/VDialogPlain.vue';
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
                details_logo: "",
                details_title: "",
                details_content: "",
                main_anime: null as InstanceType<typeof anime> | null,

                expiry_interval: null as number | null,
                expiry_string: "",
                choice_expiry_max_ms: 10 * 60 * 1000,
                still_replying_expiry_max_ms: 30 * 60 * 1000,
                shorten_interval_ceiling_ms: 80000,
                slowest_interval_ms: 10000,
                fastest_interval_ms: 1000,

                is_searching: false,
                search_button_anime: null as InstanceType<typeof anime> | null,
                is_search_button_shrinked: false,
                search_button_text: "Search",
                is_loading: false,

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
            hasDetailsForDialog() : boolean {

                return this.details_logo !== "" && this.details_title !== "" && this.details_content !== "";
            },
            stillReplying() : boolean {

                return this.still_replying_event_room !== null;
            },
            hasReplyChoices() : boolean {

                return this.event_rooms.length > 0;
            },
            mustShrinkTitle() : boolean {

                return this.is_searching === true || this.event_rooms.length > 0 || this.still_replying_event_room !== null;
            },
            canSearch(): boolean {

                return this.is_searching === false && this.still_replying_event_room === null && this.is_loading === false;
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

                await axios.post("http://127.0.0.1:8000/api/user-actions", data)
                .then(() => {

                    this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                    this.expiry_string = "";
                    this.details_logo = "fas fa-hourglass-end";
                    this.details_title = "Reply choice expired";
                    this.details_content = "You ran out of time. Feel free to search again!";
                    this.is_search_button_shrinked = false;
                    this.search_button_text = "Search";
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
                this.details_logo = "";
                this.details_title = "";
                this.details_content = "";
                this.event_rooms = [];
                this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                this.expiry_string = "";

                this.handleStartLoadingAnime();
                this.is_searching = true;

                await axios.get("http://127.0.0.1:8000/api/events/get/event-room/status/incomplete")
                .then((results: any) => {

                    if(results.data["data"].length === 0){

                        this.is_search_button_shrinked = false;
                        this.details_logo = "far fa-face-meh-blank";
                        this.details_title = "No new events found";
                        this.details_content = "Try again in a moment!";
                        this.search_button_text = "Search";

                    }else if(results.data["data"].length > 0 && results.data["data"][0]["event_room"]["is_replying"] === true){

                        //no need to add details here, currently pre-written in template
                        this.is_search_button_shrinked = false;
                        this.still_replying_event_room = results.data["data"][0];
                        this.redirect_url = "hear/" + this.still_replying_event_room!.event_room.id.toString();
                        this.startExpiryInterval();

                    }else{

                        this.is_search_button_shrinked = true;
                        this.event_rooms = results.data["data"];
                        this.search_button_text = "Skip";
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

                await axios.post("http://127.0.0.1:8000/api/user-actions", data)
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

                await axios.post("http://127.0.0.1:8000/api/user-actions", data)
                .then((results: any) => {

                    if(results.status === 202){

                        window.location.href = "http://127.0.0.1:8000/hear/" + event_room.event_room.id.toString();

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