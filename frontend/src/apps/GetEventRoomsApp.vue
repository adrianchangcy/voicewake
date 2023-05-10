<template>
    <div v-if="event_room !== null" class="flex flex-col gap-8">
        <EventRoomCard
            :propEventRoom="event_room"
            :propShowTitle="false"
            :propShowOnePlaybackPerEvent="event_room.responder.length === 0"
            :propShowReplyMenu="true"
            :propIsInContainer="false"
            class="px-2"
        />

        <div class="h-0 pb-10"></div>

        <div class="flex flex-col text-theme-black border border-x-theme-light-gray rounded-lg divide-y divide-theme-light-gray">
            <div class="text-base font-medium flex flex-row">
                <i class="fas fa-lock p-2 px-4 top-0 bottom-0 my-auto"></i>
                <span class="p-2 pl-0 w-full">Someone else is replying</span>
            </div>
            <div class="text-base flex flex-row p-4 items-center relative">
                <span>Check progress</span>
                <button
                    class="absolute w-fit h-10 right-4 top-0 bottom-0 m-auto cursor-pointer hover:scale-105 transition-transform duration-150 ease-in-out"
                    type="button"
                    @keyup.enter.stop="check_is_replying = !check_is_replying"
                    @click.stop="check_is_replying = !check_is_replying"
                >
                    <div
                        :class="check_is_replying ? 'bg-theme-lead/75 hover:shadow-theme-lead' : 'bg-theme-medium-gray/75 shadow-theme-medium-gray'"
                        class="relative my-1 inline-flex h-7 w-14 shrink-0 shadow-inner rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out"
                    >
                        <span class="sr-only">auto-check availability, currently {{ check_is_replying }}</span>
                        <span
                            aria-hidden="true"
                            :class="check_is_replying ? 'translate-x-7' : 'translate-x-0'"
                            class="pointer-events-none inline-block h-6 w-6 transform rounded-full bg-theme-light border-t-2 border-theme-light-trim shadow-lg ring-0 transition duration-200 ease-in-out"
                        />
                    </div>
                </button>
            </div>
            <div v-show="check_is_replying_interval !== null" class="text-sm flex flex-row">
                <span class="p-2 px-4 w-full">{{ check_is_replying_text }}</span>
            </div>
        </div>

    </div>
</template>


<script setup lang="ts">
    import EventRoomCard from '@/components/main/EventRoomCard.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { timeDifferenceUTC } from '@/helper_functions';
    import EventRoomTypes from '@/types/EventRooms.interface';
    const axios = require('axios');

    export default defineComponent({
        name: 'GetEventRoomsApp',
        data() {
            return {
                event_room_id: null as number|null,
                event_room: null as EventRoomTypes|null,

                check_is_replying: false,
                check_is_replying_text: 'Checking...',
                check_is_replying_countdown: 10,
                check_is_replying_interval: null as number|null,
            };
        },
        watch: {
            check_is_replying(new_value){

                if(new_value === true && this.check_is_replying_interval === null){

                    this.check_is_replying_interval = window.setInterval(this.checkIsReplyingCallback, 1000);

                }else if(new_value === false){

                    //reset
                    clearInterval(this.check_is_replying_interval!);
                    this.check_is_replying_interval = null;
                    this.check_is_replying_countdown = 10;
                    this.check_is_replying_text = 'Checking...';
                }
            },
        },
        methods: {
            checkIsReplyingCallback() : void {

                if(this.check_is_replying_countdown <= 1){

                    //reset
                    this.check_is_replying_countdown = 10;

                    //do API check here
                    this.check_is_replying_text = 'Checking...';

                }else{

                    this.check_is_replying_countdown -= 1;
                    this.check_is_replying_text = 'Checking in ' + this.check_is_replying_countdown.toString() + '...';
                }
            },
            async getEventRoom() : Promise<void> {

                if(this.event_room_id === null){

                    return;
                }

                //prepare events, then separate
                await axios.get('http://127.0.0.1:8000/api/events/get/event-room/' + this.event_room_id.toString())
                .then((results:any) => {

                    if(results.data.length > 0){

                        this.event_room = results.data[0];
                    }
                })
                .catch((errors:any) => {

                    console.log(errors);
                });
            },
        },
        beforeMount(){
        
            const container = document.getElementsByClassName('event-room')[0];

            //get event_room_id
            this.event_room_id = parseInt(container.getAttribute('data-event-room-id') as string);

            //check for empty element, e.g. when deleted
            if(container.getElementsByClassName('when-created').length === 0){

                return;
            }

            //change '1 Jan 2023' to '1 century ago'
            //we are passing 'YYYY-MM-DD HH:mm:ss' from template
            //for best reliability, Date() expects 'YYYY-MM-DDTHH:mm:ssZ'
            const when_created_element = container.getElementsByClassName('when-created')[0];
            const when_created = (container.getAttribute('data-when-created') as string).replace(/ /g, 'T') + 'Z';
            when_created_element.textContent = timeDifferenceUTC(new Date(when_created));
        },
        mounted(){

            //get responders
            this.getEventRoom();
        },
    });
</script>