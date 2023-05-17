<template>
    <div v-if="event_room !== null" class="flex flex-col gap-8">
        <EventRoomCard
            :propEventRoom="event_room"
            :propShowTitle="false"
            :propShowOnePlaybackPerEvent="event_room.responder.length === 0"
            :propShowReplyMenu="true"
            :propIsInContainer="false"
        />

        <div v-if="is_this_user_replying">
            <VCreateEvents
                :propIsOriginator="false"
                :propEventRoomId="event_room.event_room.id"
            />
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
    import VCreateEvents from '@/components/medium/VCreateEvents.vue';
    import anime from 'animejs';
    const axios = require('axios');

    export default defineComponent({
        name: 'GetEventRoomsApp',
        data() {
            return {
                event_room_id: null as number|null,
                is_this_user_replying: false,
                event_room: null as EventRoomTypes|null,

                keep_reply_active_interval: null as number|null,
                reply_active_interval_ms: 60 * 1000,
            };
        },
        watch: {
            is_this_user_replying(new_value){

                const target = (document.getElementById('is-replying-page-title') as HTMLElement);

                if(new_value === true){

                    anime({
                        targets: target,
                        opacity: 1,
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
                        opacity: 0,
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
                            }
                            break;

                        case 205:
                            {
                                //when user wants to ping to_reply=True but it returns 205,
                                //it means the last ping was too long ago, so it is no longer locked for this user
                                if(to_reply === true){

                                    console.log('Toast that user was inactive for over an hour');
                                }

                                this.is_this_user_replying = false;
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

                        //API always returns list, even if there is only one event_room
                        this.event_room = results.data[0];
                    }
                })
                .catch((errors:any) => {

                    console.log(errors);
                });
            },
            axiosSetup() : boolean {

                //your template must have {% csrf_token %}
                const token = document.getElementsByName("csrfmiddlewaretoken")[0];

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

            //get everything
            this.getEventRoom();

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


        },
    });
</script>