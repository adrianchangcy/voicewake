<template>
    <div>
        <VSectionTitle
            propTitle="Reply"
        />

        <div class="flex flex-col gap-8">

            <div
                :class="[
                    is_search_button_shrinked ? 'w-full h-20' : 'w-full h-32 sm:h-40',
                    'transition-all duration-150 ease-in-out'
                ]"
            >
                <!--search button-->
                <div ref="search_button_container">
                    <VActionButtonSpecialXL
                        ref="search_button"
                        :propIsEnabled="canSearch"
                        :propIsSmaller="is_search_button_shrinked"
                        @click.stop="getEventRooms()"
                    >
                        {{ search_button_text }}
                    </VActionButtonSpecialXL>
                </div>

                <!--spinner-->
                <div
                    ref="spinner_container"
                    class="h-full text-theme-black hidden opacity-0 flex-col place-content-center"
                >
                    <i class="fas fa-spinner text-4xl text-center"></i>
                </div>

                <!--status logo-->
                <div
                    ref="status_logo_container"
                    class="h-full text-theme-black hidden opacity-0 flex-col place-content-center"
                >
                    <i class="text-4xl text-center" :class="status_logo"></i>
                </div>
            </div>

            <!--details-->
            <div
                ref="details_container"
                class="w-full h-full text-theme-black hidden opacity-0 flex-col gap-2 place-content-center"
            >
                <i
                    ref="details_logo"
                    class="w-full text-center text-3xl"
                    :class="details_logo"
                ></i>

                <span class="block w-fit h-fit text-lg text-center mx-auto whitespace-pre-line">
                    {{ details_text }}
                </span>

                <div
                    ref="still_replying_container"
                    class="grid-rows-1 grid-cols-4 gap-2 hidden opacity-0"
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
            <TransitionGroupFadeSlow>
                <div v-for="event_room in event_rooms" :key="event_room.event_room.id">
                    <div class="flex flex-col">
                        <EventRoomCard
                            :propEventRoom="event_room"
                            :propShowTitle="true"
                            :propShowOnePlaybackPerEvent="true"
                        />
                        <VActionButtonSpecialL
                            :propIsSmaller="true"
                            @click.stop="confirmReplyChoice(event_room)"
                        >
                            Reply
                        </VActionButtonSpecialL>
                    </div>
                </div>
            </TransitionGroupFadeSlow>
        </div>
    </div>
</template>


<script setup lang="ts">
    import VSectionTitle from '/src/components/small/VSectionTitle.vue';
    import VActionButtonSpecialXL from '/src/components/small/VActionButtonSpecialXL.vue';
    import VActionButtonSpecialS from '/src/components/small/VActionButtonSpecialS.vue';
    import VActionButtonS from '/src/components/small/VActionButtonS.vue';
    import VActionButtonSpecialL from '@/components/small/VActionButtonSpecialL.vue';
    import EventRoomCard from '/src/components/main/EventRoomCard.vue';
    import TransitionGroupFadeSlow from '@/transitions/TransitionGroupFadeSlow.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import { timeFromNowMS } from '@/helper_functions';
    import anime from 'animejs';
    import EventRoomTypes from '@/types/EventRooms.interface';
    const axios = require('axios');

    export default defineComponent({
        name: 'ListEventRoomsApp',
        data(){
            return {
                event_rooms: [] as EventRoomTypes[] | [],
                status_logo: '',
                details_logo: '',
                details_text: '',
                is_searching: false,
                spinner_anime: null as InstanceType<typeof anime> | null,

                choice_expiry_interval: null as number|null,
                // choice_expiry_interval_ms: 10000,
                // choice_expiry_max_ms: 10 * 60, //10 minutes
                choice_expiry_interval_ms: 2000,
                choice_expiry_max_ms: 4,

                is_search_button_shrinked: false,
                search_button_text: 'Search',

                still_replying: false,
                still_replying_event_room: null as EventRoomTypes | null,
                redirect_url: '',

            };
        },
        computed: {
            canSearch(): boolean {

                //removed still_replying===true check to allow getEventRooms() to update still_replying
                if(this.is_searching === false){

                    return true;

                }

                return false;
            },
        },
        methods: {
            async stopReplying() : Promise<void> {

                let data = new FormData();

                await axios.post('http://127.0.0.1:8000/api/user-actions', data)
                .then((response:any) => {

                    if(response.status === 205){

                        this.choice_expiry_interval !== null ? clearInterval(this.choice_expiry_interval) : null;
                        this.details_logo = 'fas fa-hourglass-end';
                        this.details_text = 'You ran out of time.\nFeel free to search again!';
                        this.is_search_button_shrinked = false;
                        this.search_button_text = 'Search';
                        this.event_rooms = [];
                        
                        this.handleEndLoadingAnime();
                    }

                    //do nothing if 204

                })
                .catch((error:any) => {

                    console.log(error.response.data['message']);
                });
            },
            async getEventRooms() : Promise<void> {

                if(!this.canSearch){

                    return;
                }

                //reset
                this.status_logo = '';
                this.details_logo = '';
                this.details_text = '';
                this.still_replying = false;
                this.still_replying_event_room = null;
                this.event_rooms = [];
                this.redirect_url = '';
                this.choice_expiry_interval !== null ? clearInterval(this.choice_expiry_interval) : null;

                this.handleStartLoadingAnime();
                this.is_searching = true;

                //prepare events, then separate
                await axios.get('http://127.0.0.1:8000/api/events/get/event-room/status/incomplete')
                .then((results:any) => {

                    if(results.data['data'].length === 0){

                        this.is_search_button_shrinked = false;
                        this.details_logo = 'far fa-face-meh-blank';
                        this.details_text = 'No events found.\nTry again in a moment!';
                        this.search_button_text = 'Search';

                    }else if(results.data['data'].length > 0 && results.data['data'][0]['event_room']['is_replying'] === true){

                        this.is_search_button_shrinked = true;
                        this.status_logo = 'fas fa-circle-exclamation';
                        this.details_text = 'You have an unfinished reply.';
                        this.still_replying = true;
                        this.still_replying_event_room = results.data['data'][0];
                        this.redirect_url = 'hear/' + this.still_replying_event_room!.event_room.id.toString();

                    }else{

                        this.is_search_button_shrinked = true;
                        this.event_rooms = results.data['data'];
                        this.search_button_text = 'Skip';
                        
                        this.startChoiceExpiryInterval();
                    }

                    this.is_searching = false;

                })
                .catch((error:any) => {

                    console.log(error.response.data['message']);
                });

                this.handleEndLoadingAnime();
            },
            async deletePreviousReply() : Promise<void> {

                if(this.still_replying_event_room === null){

                    return;
                }

                this.handleStartLoadingAnime();

                //cancel previous reply choice
                let data = new FormData();

                data.append('event_room_id', JSON.stringify(this.still_replying_event_room.event_room.id));
                data.append('to_reply', JSON.stringify(false));

                await axios.post('http://127.0.0.1:8000/api/user-actions', data)
                .then((results:any) => {

                    if(results.status === 205){

                        this.still_replying = false;
                        this.still_replying_event_room = null;
                        this.status_logo = 'fas fa-check';
                        this.details_text = 'Deleted unfinished reply.\nSearching for new events...';
                        
                        this.handleEndLoadingAnime();
                        window.setTimeout(this.getEventRooms, 500);
                    }

                })
                .catch((error:any) => {

                    console.log(error.response.data['message']);
                });


                //automatically search
                // this.getEventRooms();
            },
            async confirmReplyChoice(event_room:EventRoomTypes) : Promise<void> {

                if(event_room === null || this.is_searching === true){

                    return;
                }

                let data = new FormData();

                data.append('event_room_id', JSON.stringify(event_room.event_room.id));
                data.append('to_reply', JSON.stringify(true));

                await axios.post('http://127.0.0.1:8000/api/user-actions', data)
                .then((results:any) => {

                    if(results.status === 202){

                        window.location.href = "http://127.0.0.1:8000/hear/" + event_room.event_room.id.toString();

                    }else{

                        console.log(results);
                    }
                })
                .catch((error:any) => {

                    console.log(error.response.data['message']);
                });
            },
            startChoiceExpiryInterval() : void {

                //start interval
                this.choice_expiry_interval = window.setInterval(()=>{

                    //time is up
                    //all event_rooms will have the same when_locked
                    if(timeFromNowMS(new Date(this.event_rooms![0].event_room.when_locked)) <= 0){

                        this.stopReplying();
                    }

                }, this.choice_expiry_interval_ms);
            },
            handleStartLoadingAnime(){

                //run this before values are reset in getEventRooms()

                const search_button_container = (this.$refs.search_button_container as HTMLElement);
                const details_container = (this.$refs.details_container as HTMLElement);
                const spinner_container = (this.$refs.spinner_container as HTMLElement);
                const status_logo_container = (this.$refs.status_logo_container as HTMLElement);
                const still_replying_container = (this.$refs.still_replying_container as HTMLElement);

                //conditionally add elements to hide
                const el_targets = [
                    search_button_container, details_container, status_logo_container,
                    still_replying_container,
                ];

                anime.timeline({
                    easing: 'linear',
                    autoplay: true,
                    loop: false,
                    duration: 150,
                }).add({
                    //hide
                    targets: el_targets,
                    opacity: ['1', '0'],
                    complete: ()=>{
                        search_button_container.style.display = 'none';
                        details_container.style.display = 'none';
                        status_logo_container.style.display = 'none';
                        still_replying_container.style.display = 'none';
                    }
                }).add({
                    //show
                    targets: spinner_container,
                    begin: ()=>{
                        spinner_container.style.display = 'flex';

                        //create or play spinner anime
                        if(this.spinner_anime === null){

                            this.spinner_anime = anime({
                                targets: spinner_container,
                                rotate: 360,
                                duration: 800,
                                loop: true,
                                easing: 'linear',
                                autoplay: true
                            });
                        
                        }else{

                            this.spinner_anime.play();
                        }
                    },
                    opacity: ['0', '1'],
                });


            },
            handleEndLoadingAnime(){

                const search_button_container = (this.$refs.search_button_container as HTMLElement);
                const details_container = (this.$refs.details_container as HTMLElement);
                const spinner_container = (this.$refs.spinner_container as HTMLElement);
                const status_logo_container = (this.$refs.status_logo_container as HTMLElement);
                const still_replying_container = (this.$refs.still_replying_container as HTMLElement);

                anime.timeline({
                    easing: 'linear',
                    autoplay: true
                }).add({
                    //hide spinner
                    targets: spinner_container,
                    opacity: ['1', '0'],
                    duration: 150,
                    loop: false,
                    complete: ()=>{

                        //pause spinner
                        this.spinner_anime.pause();
                        spinner_container.style.display = 'none';

                        //conditionally add elements to show
                        const el_targets:HTMLElement[] = [];
                        
                        if(this.details_text !== ''){
                            el_targets.push(details_container);
                            details_container.style.display = 'flex';
                        }

                        if(this.status_logo !== ''){
                            el_targets.push(status_logo_container);
                            status_logo_container.style.display = 'flex';
                        }else if(search_button_container.style.display !== 'block'){
                            el_targets.push(search_button_container);
                            search_button_container.style.display = 'block';
                        }

                        if(this.still_replying === true){
                            el_targets.push(still_replying_container);
                            still_replying_container.style.display = 'grid';
                        }

                        anime({
                            targets: el_targets,
                            opacity: ['0', '1'],
                            duration: 150,
                            loop: false,
                            easing: 'linear',
                            autoplay: true
                        });
                    }
                });
            },
            axiosSetup() : boolean {

                //your template must have {% csrf_token %}
                let token = document.getElementsByName("csrfmiddlewaretoken")[0];

                if(token === undefined){

                    console.log('CSRF not found.');
                    return false;
                }

                axios.defaults.headers.common['X-CSRFToken'] = (token as HTMLFormElement).value;
                axios.defaults.headers.post['Content-Type'] = 'multipart/form-data';
                return true;
            },
        },
        mounted(){

            this.axiosSetup();
        },
    });
</script>