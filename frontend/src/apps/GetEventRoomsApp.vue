<template>
    <div v-if="event_room !== null" class="flex flex-col">

        <!--event-->
        <EventRoomCard
            :propEventRoom="event_room"
            :propShowTitle="false"
            @newSelectedEvent=handleNewSelectedEvent($event)
        />

        <!--reply area-->
        <TransitionFadeSlow>
            <div
                v-if="is_this_user_replying"
                class="flex flex-col gap-2 py-6"
            >
                <VUser
                    :propUsername="getUsername()"
                />
                <div class="border border-theme-light-gray rounded-lg px-2 py-4">
                    <div class="flex flex-row">
                        
                        <VTitleL class="w-full">
                            <template #title>
                                <span>Replying</span>
                            </template>
                            <template #titleDescription>
                                <span>{{ reply_expiry_string }}</span>
                            </template>
                        </VTitleL>
                        
                        <div class="pt-0.5">
                            <VActionButtonDangerS
                                class="w-fit flex items-center"
                                @click.stop="stopReplying()"
                            >
                                <span class="px-2 text-base font-medium mx-auto">Cancel</span>
                            </VActionButtonDangerS>
                        </div>
                    </div>

                    <VCreateEvents
                        :propIsOriginator="false"
                        :propEventRoomId="event_room.event_room.id"
                    />
                </div>
            </div>
        </TransitionFadeSlow>

        <div v-if="selected_event !== null">
            <Teleport :to="playback_teleport_id">
                <VPlayback
                    :propIsOpen="true"
                    :propAudioVolumePeaks="selected_event.audio_volume_peaks"
                    :propAudioURL="selected_event.audio_file"
                    :propBucketQuantity="selected_event.audio_volume_peaks.length"
                    :propEventTone="selected_event.event_tone"
                    :propHasHighlight="true"
                    :propAutoPlayOnSourceChange="true"
                />
            </Teleport>
        </div>
    </div>
</template>


<script setup lang="ts">
    import EventRoomCard from '@/components/main/EventRoomCard.vue';
    import VActionButtonDangerS from '@/components/small/VActionButtonDangerS.vue';
    import VCreateEvents from '@/components/medium/VCreateEvents.vue';
    import VTitleL from '@/components/small/VTitleL.vue';
    import TransitionFadeSlow from '@/transitions/TransitionFadeSlow.vue';
    import VPlayback from '@/components/medium/VPlayback.vue';
    import VUser from '@/components/small/VUser.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { prettyTimePassed, prettyTimeRemaining, getUsername, timeFromNowMS } from '@/helper_functions';
    import EventRoomTypes from '@/types/EventRooms.interface';
    import EventTypes from '@/types/Events.interface';
    const axios = require('axios');

    export default defineComponent({
        name: 'GetEventRoomsApp',
        data() {
            return {
                event_room_id: null as number|null,
                is_this_user_replying: false,
                event_room: null as EventRoomTypes|null,
                selected_event: null as EventTypes|null,
                playback_teleport_id: '',

                reply_expiry_interval: null as number|null,
                reply_expiry_string: '',

                reply_expiry_max_ms: 30 * 60 * 1000,  //30 minutes
                shorten_interval_ceiling_ms: 80000, //add double slowest_interval_ms to transition from minute to seconds smoothly
                slowest_interval_ms: 10000,
                fastest_interval_ms: 1000,
            };
        },
        methods: {
            async stopReplying() : Promise<void> {

                let data = new FormData();

                data.append('event_room_id', JSON.stringify(this.event_room_id));
                data.append('to_reply', JSON.stringify(false));

                await axios.post('http://127.0.0.1:8000/api/user-actions', data)
                .then(() => {

                    this.is_this_user_replying = false;

                    this.reply_expiry_interval !== null ? clearInterval(this.reply_expiry_interval) : null;

                })
                .catch((error:any) => {

                    console.log(error.response.data['message']);
                });
            },
            async getEventRoom() : Promise<void> {

                if(this.event_room_id === null){

                    return;
                }

                //prepare events, then separate
                await axios.get('http://127.0.0.1:8000/api/events/get/event-room/' + this.event_room_id.toString())
                .then((results:any) => {

                    if(results.data['data'].length > 0){

                        //API always returns list, even if there is only one event_room
                        this.event_room = results.data['data'][0];

                        this.startReplyExpiryInterval();
                    }
                })
                .catch((error:any) => {

                    console.log(error.response.data['message']);
                });
            },
            handleNewSelectedEvent(event:EventTypes|null) : void {

                this.selected_event = event;

                if(event !== null){

                    //must be the same as in VEventCard
                    this.playback_teleport_id = '#playback-teleport-' + event.id.toString();
                }
            },
            startReplyExpiryInterval() : void {

                if(this.is_this_user_replying === false){

                    return;
                }

                this.reply_expiry_interval !== null ? clearInterval(this.reply_expiry_interval) : null;

                const when_locked_ms = new Date(this.event_room!.event_room.when_locked);
                const time_elapsed_ms = timeFromNowMS(when_locked_ms);

                //time is up
                if(time_elapsed_ms >= this.reply_expiry_max_ms){

                    this.stopReplying();
                    return;
                }

                //proceed

                //run every 1s if <120s remaining, else run every 60s
                //change this again once sped up
                let interval_ms:number = this.reply_expiry_max_ms - time_elapsed_ms <= this.shorten_interval_ceiling_ms ? this.fastest_interval_ms : this.slowest_interval_ms;

                //set possible first time expiry string
                const time_remaining = prettyTimeRemaining(time_elapsed_ms, this.reply_expiry_max_ms);
                this.reply_expiry_string = time_remaining === false ? '' : time_remaining as string;

                //declare this here for reusability
                const interval_function = ()=>{

                    //get time difference
                    const time_elapsed_ms = timeFromNowMS(when_locked_ms);

                    //time is up
                    if(time_elapsed_ms >= this.reply_expiry_max_ms){
                        
                        this.stopReplying();
                    }

                    //if interval started with >1000, be prepared for reinitialisation for new interval with shorter time
                    if(interval_ms === this.slowest_interval_ms && this.reply_expiry_max_ms - time_elapsed_ms <= this.shorten_interval_ceiling_ms){

                        clearInterval(this.reply_expiry_interval!);

                        this.reply_expiry_interval = window.setInterval(interval_function, this.fastest_interval_ms);

                        //change interval_ms as lazy way to skip this part after the first time
                        interval_ms = this.fastest_interval_ms;
                    }

                    //set string
                    const time_remaining = prettyTimeRemaining(time_elapsed_ms, this.reply_expiry_max_ms);
                    this.reply_expiry_string = time_remaining === false ? '' : time_remaining as string;
                }

                //start interval
                this.reply_expiry_interval = window.setInterval(interval_function, interval_ms);
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
                when_created_element.textContent = prettyTimePassed(new Date(when_created));
            }
        },
    });
</script>