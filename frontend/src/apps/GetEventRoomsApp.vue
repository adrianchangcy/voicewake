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

        <div
            v-if="can_poll_for_reply"
            class="flex flex-col text-theme-black border-2 border-theme-medium-gray rounded-lg divide-y divide-theme-light-gray"
        >
            <div class="text-base font-medium flex flex-row">
                <i class="fas fa-lock p-2 px-4 top-0 bottom-0 my-auto"></i>
                <span class="p-2 pl-0 w-full">Someone else is replying</span>
            </div>
            <VSwitch
                propScreenReaderText="Toggle to auto-check availability, currently "
                @isToggled="handleCheckIsReplyingToggle($event)"
                class="p-4"
            >
                <span class="text-base">Reply if available</span>
            </VSwitch>
            <div
                v-show="check_is_replying_interval !== null"
                class="text-sm flex flex-row"
            >
                <span class="p-2 px-4 w-full">{{ check_is_replying_text }}</span>
            </div>
        </div>

    </div>
</template>


<script setup lang="ts">
    import EventRoomCard from '@/components/main/EventRoomCard.vue';
    import VSwitch from '@/components/small/VSwitch.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { timeDifferenceUTC } from '@/helper_functions';
    import EventRoomTypes from '@/types/EventRooms.interface';
    import anime from 'animejs';
    const axios = require('axios');

    export default defineComponent({
        name: 'GetEventRoomsApp',
        data() {
            return {
                event_room_id: null as number|null,
                is_this_user_replying: false,
                is_another_user_replying: false,
                can_poll_for_reply: false,

                event_room: null as EventRoomTypes|null,
                
                check_is_replying: false,
                check_is_replying_text: 'Checking...',
                check_is_replying_countdown: 2,    //same as countdown_start
                countdown_start: 2,
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
                    this.check_is_replying_countdown = this.countdown_start;
                    this.check_is_replying_text = 'Checking...';
                }
            },
            is_this_user_replying(new_value){

                const target = (document.getElementById('is-replying-page-title') as HTMLElement);

                if(new_value === true){

                    anime({
                        targets: target,
                        opacity: ['0', '1'],
                        easing: 'linear',
                        loop: false,
                        duration: 1000,
                        autoplay: true,
                        begin: ()=>{
                            target.style.display = 'block';
                        }
                    });

                }else{

                    anime({
                        targets: target,
                        opacity: ['1', '0'],
                        easing: 'linear',
                        loop: false,
                        duration: 150,
                        autoplay: true,
                        complete: ()=>{
                            target.style.display = 'none';
                        }
                    });
                }
            },
        },
        methods: {
            handleCheckIsReplyingToggle(new_value:boolean){

                this.check_is_replying = new_value;
            },
            checkIsReplyingCallback() : void {

                if(this.check_is_replying_countdown <= 1){

                    //reset
                    this.check_is_replying_countdown = this.countdown_start;

                    //do API
                    this.check_is_replying_text = 'Checking...';
                    this.updateReplyDecision(true);

                }else{

                    this.check_is_replying_countdown -= 1;
                    this.check_is_replying_text = 'Checking in ' + this.check_is_replying_countdown.toString() + '...';
                }
            },
            //true to try/continue reply, false to skip
            async updateReplyDecision(to_reply:boolean) : Promise<void> {

                let data = new FormData();

                data.append('event_room_id', JSON.stringify(this.event_room_id));
                data.append('to_reply', JSON.stringify(to_reply));

                await axios.post('http://127.0.0.1:8000/api/user-actions', data)
                .then((results:any) => {

                    switch(results.status){

                        case 202:
                            {
                                //user can now reply
                                this.is_this_user_replying = true;
                                this.is_another_user_replying = false;
                                this.can_poll_for_reply = false;
                                this.check_is_replying = false;
                            }
                            break;

                        case 205:
                            {
                                //user successfully cancelled reply
                                this.is_this_user_replying = false;
                                this.is_another_user_replying = false;
                                this.can_poll_for_reply = false;
                                this.check_is_replying = false;
                            }
                            break;

                        default:
                            break;
                    }
                })
                .catch((errors:any) => {

                    console.log(errors);
                });
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
        beforeMount(){
        
            //prepare axios
            this.axiosSetup();

            const container = (document.getElementById('get-event-room') as HTMLElement);

            //get data from SSR template
            this.event_room_id = parseInt(container.getAttribute('data-event-room-id') as string);
            this.is_this_user_replying = JSON.parse(container.getAttribute('data-is-this-user-replying') as string);
            this.is_another_user_replying = JSON.parse(container.getAttribute('data-is-another-user-replying') as string);
            this.can_poll_for_reply = JSON.parse(container.getAttribute('data-can-poll-for-reply') as string);

            //change '1 Jan 2023' to '1 century ago'
            //we are passing 'YYYY-MM-DD HH:mm:ss' from template
            //for best reliability, Date() expects 'YYYY-MM-DDTHH:mm:ssZ'
            if(container.getElementsByClassName('when-created').length === 1){

                const when_created_element = container.getElementsByClassName('when-created')[0];
                const when_created = (container.getAttribute('data-when-created') as string).replace(/ /g, 'T') + 'Z';
                when_created_element.textContent = timeDifferenceUTC(new Date(when_created));
            }
        },
        mounted(){

            //get responders
            this.getEventRoom();
        },
    });
</script>