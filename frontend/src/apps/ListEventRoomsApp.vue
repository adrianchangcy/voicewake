<template>
    <div>
        <!--big title-->
        <VTitleXL
            :class="mustShrinkTitle ? '' : 'py-10'"
        >
            <template #title>
                <div class="flex flex-col">
                    <i class="fas fa-comments block text-xl w-full text-center"></i>
                    <span class="block w-full text-center">Reply</span>
                </div>
            </template>
        </VTitleXL>

        <!--content-->
        <div>
            <EventRoomCardSkeleton
                v-show="is_searching"
                :prop-event-quantity="2"
                :prop-can-reply="true"
            />
        </div>

        <!--search-->
        <div
            ref="search_button_container"
        >
            <VActionButtonSpecialXL
                :propIsEnabled="canSearch"
                :propIsSmaller="is_search_button_shrinked"
                @click.stop="getEventRooms()"
                class="mx-auto"
            >
                {{ search_button_text }}
            </VActionButtonSpecialXL>
        </div>





        <!--details-->
        <div
            ref="details_container"
            class="w-full text-theme-black hidden flex-col place-content-center"
            style="opacity: 0;"
        >
            <!--follows search_spinner_container to place logo at spinner precisely-->
            <div
                class="m-auto relative"
                :class="is_search_button_shrinked ? 'w-24 h-24' : 'w-36 h-36 sm:w-44 sm:h-44'"
            >
                <i
                    ref="details_logo"
                    class="w-fit h-fit text-3xl absolute left-0 right-0 top-0 bottom-0 m-auto"
                    :class="details_logo"
                ></i>
            </div>

            <span class="block w-fit h-fit text-lg text-center mx-auto whitespace-pre-line">
                {{ details_text }} <span v-show="expiry_string !== ''"><br>with {{ expiry_string }}.</span>
            </span>

            <div
                ref="still_replying_container"
                class="grid-rows-1 grid-cols-4 pt-2 gap-2 hidden"
                style="opacity: 0;"
            >
                <a :href="redirect_url" class="row-start-1 col-span-2">
                    <VActionButtonSpecialS
                        class="w-full flex items-center"
                    >
                        <span class="text-base font-medium mx-auto">Open</span>
                    </VActionButtonSpecialS>
                </a>
                <VActionButtonS
                    @click.stop="deletePreviousReply()"
                    class="row-start-1 col-span-2 flex items-center"
                >
                    <span class="text-base font-medium mx-auto">Delete</span>
                </VActionButtonS>
            </div>
        </div>



        <!--event_rooms-->
        <div class="flex flex-col">
            <TransitionGroupFadeSlow>
                <div v-for="event_room in event_rooms" :key="event_room.event_room.id">
                    <div class="flex flex-col">
                        <EventRoomCard
                            :propEventRoom="event_room"
                            :propShowTitle="true"
                        />
                        <VActionButtonSpecialL
                            :propIsSmaller="false"
                            @click.stop="confirmReplyChoice(event_room)"
                            class="mt-6"
                        >
                            Reply
                        </VActionButtonSpecialL>
                        <span
                            v-show="expiry_string !== ''"
                            class="w-full h-fit py-2 text-base text-center text-theme-black"
                        >
                            {{ expiry_string }} to decide
                        </span>
                    </div>
                </div>
            </TransitionGroupFadeSlow>
        </div>
    </div>
</template>


<script setup lang="ts">
    import VTitleXL from '/src/components/small/VTitleXL.vue';
    import VActionButtonSpecialXL from '/src/components/small/VActionButtonSpecialXL.vue';
    import VActionButtonSpecialS from '/src/components/small/VActionButtonSpecialS.vue';
    import VActionButtonS from '/src/components/small/VActionButtonS.vue';
    import VActionButtonSpecialL from '@/components/small/VActionButtonSpecialL.vue';
    import EventRoomCard from '/src/components/main/EventRoomCard.vue';
    import TransitionGroupFadeSlow from '@/transitions/TransitionGroupFadeSlow.vue';
    import EventRoomCardSkeleton from '@/components/skeleton/EventRoomCardSkeleton.vue';
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
                details_text: "",
                main_anime: null as InstanceType<typeof anime> | null,

                expiry_interval: null as number | null,
                expiry_string: "",
                choice_expiry_max_ms: 10 * 60 * 1000,
                reply_expiry_max_ms: 30 * 60 * 1000,
                shorten_interval_ceiling_ms: 80000,
                slowest_interval_ms: 10000,
                fastest_interval_ms: 1000,

                is_searching: false,
                search_button_anime: null as InstanceType<typeof anime> | null,
                is_search_button_shrinked: false,
                search_button_text: "Search",

            };
        },
        computed: {
            mustShrinkTitle() : boolean {

                return this.event_rooms.length > 0;
            },
            canSearch(): boolean {

                return this.is_searching === false && this.still_replying_event_room === null;
            },
        },
        methods: {
            async expireReplyChoices(): Promise<void> {

                this.handleStartLoadingAnime();

                let data = new FormData();
                data.append("to_reply", JSON.stringify(false));

                await axios.post("http://127.0.0.1:8000/api/user-actions", data)
                .then(() => {
                    this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                    this.expiry_string = "";
                    this.details_logo = "fas fa-hourglass-end";
                    this.details_text = "You ran out of time.\nFeel free to search again!";
                    this.is_search_button_shrinked = false;
                    this.search_button_text = "Search";
                    this.event_rooms = [];
                    this.handleEndLoadingAnime();
                })
                .catch((error: any) => {
                    this.handleEndLoadingAnime();
                    console.log(error.response.data["message"]);
                });
            },
            async getEventRooms(): Promise<void> {

                if(!this.canSearch){
                    return;
                }

                this.handleStartLoadingAnime();
                this.is_searching = true;

                await axios.get("http://127.0.0.1:8000/api/events/get/event-room/status/incomplete")
                .then((results: any) => {
                    //reset
                    this.details_logo = "";
                    this.details_text = "";
                    this.event_rooms = [];
                    this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                    this.expiry_string = "";

                    if(results.data["data"].length === 0){

                        this.is_search_button_shrinked = false;
                        this.details_logo = "far fa-face-meh-blank";
                        this.details_text = "No events found.\nTry again in a moment!";
                        this.search_button_text = "Search";

                    }else if(results.data["data"].length > 0 && results.data["data"][0]["event_room"]["is_replying"] === true){

                        this.is_search_button_shrinked = false;
                        this.details_logo = "fas fa-circle-exclamation";
                        this.details_text = "You have an unfinished reply";
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

                if(this.still_replying_event_room === null){
                    return;
                }

                this.handleStartLoadingAnime();

                //cancel previous reply choice
                let data = new FormData();
                data.append("event_room_id", JSON.stringify(this.still_replying_event_room.event_room.id));
                data.append("to_reply", JSON.stringify(false));

                await axios.post("http://127.0.0.1:8000/api/user-actions", data)
                .then(() => {
                    this.expiry_interval !== null ? clearInterval(this.expiry_interval) : null;
                    this.expiry_string = "";
                    this.still_replying_event_room = null;
                    this.details_logo = "fas fa-check";
                    this.details_text = "Deleted unfinished reply.\nSearching for new events...";

                    this.handleEndLoadingAnime();

                    window.setTimeout(() => {
                        this.getEventRooms();
                    }, 5000);
                })
                .catch((error: any) => {
                    this.handleEndLoadingAnime();
                    console.log(error.response.data["message"]);
                });
            },
            async confirmReplyChoice(event_room: EventRoomTypes): Promise<void> {

                if (event_room === null || this.is_searching === true) {

                    return;
                }
                
                let data = new FormData();
                data.append("event_room_id", JSON.stringify(event_room.event_room.id));
                data.append("to_reply", JSON.stringify(true));

                await axios.post("http://127.0.0.1:8000/api/user-actions", data)
                .then((results: any) => {
                    if (results.status === 202) {
                        window.location.href = "http://127.0.0.1:8000/hear/" + event_room.event_room.id.toString();
                    }
                    else {
                        console.log(results);
                    }
                })
                .catch((error: any) => {
                    console.log(error.response.data["message"]);
                });
            },
            startExpiryInterval(): void {

                let target_event_room: EventRoomTypes | null = null;
                let target_max_ms = 0;

                if(this.still_replying_event_room !== null){

                    target_event_room = this.still_replying_event_room;
                    target_max_ms = this.reply_expiry_max_ms;

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