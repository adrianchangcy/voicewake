<template>
    <div class="flex flex-col gap-2 py-8">

        <VTitle
            propFontSize="l"
            class="w-full"
        >
            <template #title>
                <span>Best events today</span>
            </template>
        </VTitle>

        <!--sorting options-->
        <div class="flex flex-row items-center gap-2">
            <VAction
                prop-element="button"
                prop-element-size="s"
                prop-font-size="s"
                :prop-is-icon-only="false"
                class="px-2"
            >
                <div class="flex flex-row items-center gap-1">
                    <i class="fas fa-check"></i>
                    <span>Latest</span>
                </div>
            </VAction>
            <VAction
                prop-element="button"
                prop-element-size="s"
                prop-font-size="s"
                :prop-is-icon-only="false"
                class="px-2"
            >
                <span>Best</span>
            </VAction>
        </div>
    </div>

    <!--event_rooms-->
    <div>
        <div
            v-for="event_room in event_rooms" :key="event_room.event_room.id"
            class="border rounded-lg px-2 pt-14 pb-16 mb-8   border-theme-light-gray"
        >
            <EventRoomCard
                :prop-show-title="true"
                :prop-event-room="event_room"
                @newSelectedEvent=handleNewSelectedEvent($event)
            />
        </div>
    </div>

    <!--VEventCard emits selection, which triggers :to, thus teleporting-->
    <!--presence of VEventCard depends on VEventRoomCard-->
    <div v-if="selected_event !== null">
        <Teleport :to="playback_teleport_event_id">
            <VPlayback
                :propEvent="selected_event"
                :propIsOpen="true"
                :propAudioVolumePeaks="selected_event.audio_volume_peaks"
                :propBucketQuantity="selected_event.audio_volume_peaks.length"
                :propAutoPlayOnSourceChange="true"
            />
        </Teleport>
    </div>

</template>


<script setup lang="ts">
    import EventRoomCard from '@/components/main/EventRoomCard.vue';
    import VTitle from '@/components/small/VTitle.vue';
    import VPlayback from '@/components/medium/VPlayback.vue';
</script>


<script lang="ts">
    import { defineComponent, } from 'vue';
    import { notify } from 'notiwind';
    import GroupedEventsTypes from '@/types/GroupedEvents.interface';
    import EventsAndLikeDetailsTypes from '@/types/EventsAndLikeDetails.interface';
    import { useCurrentlyPlayingEventStore } from '@/stores/CurrentlyPlayingEventStore';
    import VAction from '@/components/small/VAction.vue';
    const axios = require('axios');

    export default defineComponent({
        name: 'BrowseEventRoomsApp',
        data(){
            return {
                currently_playing_event_store: useCurrentlyPlayingEventStore(),
                api_page_increment: 1,
                event_rooms: [] as GroupedEventsTypes[],
                selected_event: null as EventsAndLikeDetailsTypes|null,
                playback_teleport_event_id: '',
            };
        },
        methods: {
            async getEventRooms(): Promise<void> {

                await axios.get(window.location.origin + "/api/event-rooms/list/completed/best/all/" + this.api_page_increment)
                .then((results: any) => {

                    //add new grouped events
                    for(let x=0; x < results.data['data'].length; x++){

                        this.event_rooms.push(results.data['data'][x]);
                    }

                    //increment page for next request
                    this.api_page_increment += 1;
                })
                .catch((error: any) => {

                    notify({
                        title: "Could not get events",
                        text: error.response.data['message'],
                        type: "error"
                    }, 3000);
                });
            },
            handleNewSelectedEvent(event:EventsAndLikeDetailsTypes|null) : void {

                this.selected_event = event;

                if(event !== null){

                    //must be the same as in VEventCard
                    this.playback_teleport_event_id = '#playback-teleport-event-id-' + event.id.toString();
                }
            },
        },
        beforeMount(){

            this.getEventRooms();

            //listen to store
            this.currently_playing_event_store.$subscribe((mutation, state)=>{

                this.handleNewSelectedEvent(state.playing_event);
            });
        }
    });
</script>