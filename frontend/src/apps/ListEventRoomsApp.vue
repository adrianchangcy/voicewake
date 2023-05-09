<template>
    <div>
        <VSectionTitle
            propTitle="Reply"
        />

        <div class="flex flex-col gap-8">

            <div>
                <div ref="search_button_container">
                    <VActionButtonSpecialXL
                        ref="search_button"
                        :propCanClick="canSearch"
                        @click.stop="getEventRooms()"
                    >
                        Search
                    </VActionButtonSpecialXL>
                </div>
                <div
                    ref="spinner_container"
                    class="w-full h-32 sm:h-40 text-theme-black hidden opacity-0 flex-col place-content-center"
                >
                    <i class="fas fa-spinner text-4xl text-center"></i>
                </div>
            </div>
            
            <div ref="event_rooms_container" class="h-0 opacity-0">
                <div v-for="event_room in event_rooms" :key="event_room.event_room.id">
                    <div class="border-2 border-theme-light-gray rounded-lg px-4 py-6 flex flex-col gap-10">
                        <EventRoomCard
                            :propEventRoom="event_room"
                            :propShowTitle="false"
                            :propShowOnePlaybackPerEvent="true"
                            :propShowReplyMenu="false"
                            :propIsInContainer="true"
                        />
                        <VActionButtonBig
                            :propIsSmaller="true"
                            @click.stop="confirmReplyChoice(event_room)"
                        >
                            Reply
                        </VActionButtonBig>
                    </div>
                </div>
            </div>

            <!--details-->
            <div
                ref="details_container"
                class="w-full h-full text-theme-black hidden opacity-0 flex-col gap-2 place-content-center"
            >
                <i class="text-4xl text-center" :class="current_status_logo"></i>
                <span class="block w-fit h-fit text-xl text-center mx-auto whitespace-pre-line">
                    {{ current_status }}
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
                    <VActionButtonSmall
                        @click.stop="deletePreviousReply()"
                        class="row-start-1 col-span-2 flex items-center"
                    >
                        <span class="text-base font-medium mx-auto">Delete</span>
                    </VActionButtonSmall>
                </div>
            </div>
        </div>
    </div>
</template>


<script setup lang="ts">
    import VSectionTitle from '/src/components/small/VSectionTitle.vue';
    import VActionButtonSpecialXL from '/src/components/small/VActionButtonSpecialXL.vue';
    import VActionButtonSpecialS from '/src/components/small/VActionButtonSpecialS.vue';
    import VActionButtonSmall from '/src/components/small/VActionButtonSmall.vue';
    import VActionButtonBig from '@/components/small/VActionButtonBig.vue';
    import EventRoomCard from '/src/components/main/EventRoomCard.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import anime from 'animejs';
    import EventRoomTypes from '@/types/EventRooms.interface';
    const axios = require('axios');

    export default defineComponent({
        name: 'ListEventRoomsApp',
        data(){
            return {
                event_rooms: null as EventRoomTypes[] | null,
                current_status_logo: '',
                current_status: '',
                is_searching: false,
                keep_search_disabled: false,    //used for auto-search after deletion
                spinner_anime: null as InstanceType<typeof anime> | null,

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
            async getEventRooms() : Promise<void> {

                if(!this.canSearch){

                    return;
                }

                this.handleStartLoadingAnime();
                this.event_rooms = null;
                this.is_searching = true;
                this.still_replying = false;
                this.redirect_url = '';

                //prepare events, then separate
                await axios.get('http://127.0.0.1:8000/api/events/get/status/incomplete')
                .then((results:any) => {

                    if(results.data.length === 0){

                        this.current_status_logo = 'far fa-face-meh-blank';
                        this.current_status = 'No events found.\nTry again in a moment!';
                        this.still_replying = false;

                    }else if(results.data.length > 0 && results.data[0]['event_room']['is_replying'] === true){

                        this.current_status_logo = 'fas fa-circle-exclamation';
                        this.current_status = 'You have an unfinished reply.';
                        this.still_replying = true;
                        this.still_replying_event_room = results.data[0];
                        this.redirect_url = 'hear/' + this.still_replying_event_room!.event_room.id.toString();

                    }else{

                        this.current_status_logo = 'fas fa-face-meh-blank';
                        this.current_status = '';
                        this.still_replying = false;
                        this.event_rooms = results.data;
                    }

                    this.is_searching = false;

                })
                .catch((errors:any) => {

                    console.log(errors);
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

                    console.log(results);
                    this.still_replying = false;

                    this.handleEndLoadingAnime();
                    this.current_status_logo = 'fas fa-check';
                    this.current_status = 'Deleted unfinished reply.\nSearching for new events...';

                    window.setTimeout(this.getEventRooms, 500);

                })
                .catch((errors:any) => {

                    console.log(errors);
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

                    console.log(results);
                })
                .catch((errors:any) => {

                    console.log(errors);
                });
            },
            searchButtonAnime(to_show=false) : void {

                const target = (this.$refs.search_button_container as HTMLElement);

                anime({
                    targets: target,
                    opacity: to_show === true ? ['0', '1'] : ['1', '0'],
                    easing: 'linear',
                    loop: false,
                    autoplay: true,
                    duration: 150,
                    complete: ()=>{
                        
                        target.style.display = to_show === true ? 'block' : 'none';
                    }
                });
            },
            handleStartLoadingAnime(){

                //run this before values are reset in getEventRooms()

                const search_button_container = (this.$refs.search_button_container as HTMLElement);
                const details_container = (this.$refs.details_container as HTMLElement);
                const spinner_container = (this.$refs.spinner_container as HTMLElement);
                const still_replying_container = (this.$refs.still_replying_container as HTMLElement);
                const event_rooms_container = (this.$refs.event_rooms_container as HTMLElement);

                //conditionally add elements to hide
                const el_targets = [search_button_container, details_container, event_rooms_container];
                this.still_replying === true ? el_targets.push(still_replying_container) : null;

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
                        still_replying_container.style.display = 'none';
                        event_rooms_container.style.height = '0';
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
                const still_replying_container = (this.$refs.still_replying_container as HTMLElement);
                const event_rooms_container = (this.$refs.event_rooms_container as HTMLElement);

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
                        const el_targets = [];
                        this.current_status !== '' ? el_targets.push(details_container) : null;
                        this.event_rooms !== null ? el_targets.push(event_rooms_container) : null;

                        if(this.still_replying === false){
                            el_targets.push(search_button_container);
                            search_button_container.style.display = 'block';
                        }
                        if(this.current_status !== ''){
                            el_targets.push(details_container);
                            details_container.style.display = 'flex';
                        }
                        if(this.still_replying === true){
                            el_targets.push(still_replying_container);
                            still_replying_container.style.display = 'grid';
                        }
                        if(this.event_rooms !== null){
                            el_targets.push(event_rooms_container);
                            event_rooms_container.style.height = 'fit-content';
                        }

                        anime({
                            targets: el_targets,
                            opacity: ['0', '1'],
                            duration: 150,
                            loop: false,
                            easing: 'linear',
                            autoplay: true,
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