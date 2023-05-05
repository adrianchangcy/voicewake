<template>
    <div>
        <VSectionTitle
            propTitle="Reply"
        />

        <div v-if="event_rooms !== null" class="flex flex-col gap-y-32">
            <div v-for="event_room in event_rooms" :key="event_room">
                <EventRoomCard
                    :propEventRoom="event_room"
                    :propShowTitle="true"
                    :propShowOnePlaybackPerEvent="true"
                    :propShowReplyMenu="false"
                    :propIsInContainer="true"
                />
            </div>
        </div>

        <div
            :class="[
                mustShowExtraDetails ? 'h-32' : 'h-0',
                'w-full'
            ]"
        >
            <!--details-->
            <div
                ref="reply_search_details_container"
                class="w-full h-full text-theme-black hidden flex-col gap-2 place-content-center"
            >
                <i class="text-4xl text-center" :class="current_status_logo"></i>
                <span class="block w-fit h-fit text-xl text-center mx-auto whitespace-pre-line">{{ current_status }}</span>

                <div
                    ref="existing_reply_options_container"
                    class="hidden grid-cols-4 gap-2"
                >
                    <VActionButtonSmall
                        class="col-span-2"
                    >
                        <span class="text-xl">Reply</span>
                    </VActionButtonSmall>
                    <VActionButtonSmall
                        class="col-span-2"
                    >
                        <span class="text-xl">Cancel</span>
                    </VActionButtonSmall>
                </div>
            </div>
            <!--spinner-->
            <div
                ref="reply_search_spinner_container"
                class="w-full h-full text-theme-black hidden flex-col place-content-center"
            >
                <i class="py-2 text-4xl text-center fas fa-spinner"></i>
            </div>
        </div>

        <div class="py-8">
            <VActionButtonSpecial
                :propIsEnabled="!is_searching"
                @click.stop="getEventRooms()"
                class="block"
            >
                Search
            </VActionButtonSpecial>
        </div>
    </div>
</template>


<script setup lang="ts">
    import VSectionTitle from '/src/components/small/VSectionTitle.vue';
    import VActionButtonSpecial from '/src/components/small/VActionButtonSpecial.vue';
    import VActionButtonSmall from '/src/components/small/VActionButtonSmall.vue';
    import EventRoomCard from '/src/components/main/EventRoomCard.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import anime from 'animejs';
    const axios = require('axios');

    export default defineComponent({
        name: 'ListEventRoomsApp',
        data(){
            return {
                event_rooms: null as any,
                current_status: '',
                current_status_logo: '',
                is_searching: false,
                details_anime: null as InstanceType<typeof anime> | null,
                spinner_anime: null as InstanceType<typeof anime> | null,
            };
        },
        computed: {
            mustShowExtraDetails() : boolean {

                if(this.current_status !== '' || this.is_searching === true){

                    return true;
                }

                return false;
            },
        },
        methods: {
            async getEventRooms() : Promise<void> {

                if(this.is_searching === true){

                    return;
                }

                this.event_rooms = null;

                //show spinner
                this.is_searching = true;
                this.handleStartSearchAnime();

                //prepare events, then separate
                await axios.get('http://127.0.0.1:8000/api/events/get/status/incomplete')
                .then((results:any) => {

                    if(results.data.length === 0){

                        this.current_status_logo = 'far fa-face-meh-blank';
                        this.current_status = 'No events found.\nSearch again in a moment!';

                    }else if(results.data.length > 0 && results.data[0]['event_room']['is_replying'] === true){

                        this.current_status_logo = 'fas fa-triangle-exclamation';
                        this.current_status = 'You are already replying to an event.\nChoose an action:';

                    }else{

                        this.current_status_logo = 'fas fa-triangle-exclamation';
                        this.current_status = '';
                        this.event_rooms = results.data;
                    }

                })
                .catch((errors:any) => {

                    console.log(errors);
                });

                this.is_searching = false;
                this.handleStopSearchAnime();
            },
            handleStartSearchAnime(){

                this.details_anime !== null ? this.details_anime.pause() : null;

                const details_container = (this.$refs.reply_search_details_container as HTMLElement);
                const spinner_container = (this.$refs.reply_search_spinner_container as HTMLElement);

                this.details_anime = anime.timeline({
                    easing: 'linear',
                    autoplay: true
                }).add({
                    targets: details_container,
                    opacity: ['1', '0'],
                    duration: 200,
                    loop: false,
                    complete: ()=>{
                        details_container.style.display = 'none';
                        spinner_container.style.display = 'flex';
                        spinner_container.style.opacity = '0';
                    }
                }).add({
                    targets: spinner_container,
                    opacity: ['0', '1'],
                    duration: 200,
                    loop: false,
                });

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
            handleStopSearchAnime(){

                this.details_anime !== null ? this.details_anime.pause() : null;

                const details_container = (this.$refs.reply_search_details_container as HTMLElement);
                const spinner_container = (this.$refs.reply_search_spinner_container as HTMLElement);

                this.details_anime = anime.timeline({
                    easing: 'linear',
                    autoplay: true
                }).add({
                    targets: spinner_container,
                    opacity: ['1', '0'],
                    duration: 200,
                    loop: false,
                    complete: ()=>{
                        this.spinner_anime.pause();
                        spinner_container.style.display = 'none';
                        if(this.current_status !== ''){
                            details_container.style.display = 'flex';
                            anime({
                                targets: details_container,
                                opacity: ['0', '1'],
                                duration: 200,
                                loop: false,
                                easing: 'linear',
                                autoplay: true,
                            });
                        }
                    }
                });
            },
        },
        mounted(){

        },
    });
</script>