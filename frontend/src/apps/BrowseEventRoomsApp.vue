<template>
    <div>

        <!--backdrop and title-->
        <!--height is VTitle + py-8-->
        <div class="h-32 relative">

            <!--backdrop-->
            <VBackdropAnime
                class="h-full pb-14"
            />

            <!--title-->
            <!--needs padding for more area to smoothen the transparent part, else a faint cutoff/border is visible-->
            <div class="w-fit h-fit absolute inset-0 m-auto p-8 flex items-center rounded-lg bg-gradient-radial from-theme-light to-transparent">
                <VTitle
                    propFontSize="l"
                >
                    <template #title>
                        <span>VoiceWake</span>
                    </template>
                </VTitle>
            </div>
        </div>

        <!--sorting options-->
        <div class="pb-8 flex flex-col">


            <label class="text-base font-medium">Filters</label>
            
            <VEventToneMenu
                :prop-is-open="true"
                :prop-close-when-selected="false"
                :prop-has-deselect-option="true"
                :prop-must-track-selected-option="true"
            />

            <!--options-->
            <div class="flex flex-row items-center gap-2">
                <VAction
                    v-for="(filter_type, index) in filter_types" :key="index"
                    @click="updateCurrentFilterTypeIndex(index)"
                    prop-element="button"
                    prop-element-size="s"
                    prop-font-size="s"
                    :prop-is-icon-only="true"
                    class="px-2"
                >
                    <div class="flex flex-row items-center gap-2">
                        <i
                            :class="[
                                isFilterTypeSelected(index) === true ? 'fa-square-check' : 'fa-square',
                                'far text-xl'
                            ]"
                        ></i>
                        <span class="pb-0.5">{{ filter_type }}</span>
                    </div>
                </VAction>
            </div>
        </div>

        <!--event_rooms-->
        <TransitionGroupFade>
            <div
                v-for="event_room in event_rooms" :key="event_room.event_room.id"
            >
                <EventRoomCard
                    :prop-show-title="true"
                    :prop-event-room="event_room"
                    :prop-has-border="true"
                    @newSelectedEvent=handleNewSelectedEvent($event)
                />
            </div>
        </TransitionGroupFade>

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
    </div>
</template>


<script setup lang="ts">
    import EventRoomCard from '@/components/main/EventRoomCard.vue';
    import VTitle from '@/components/small/VTitle.vue';
    import VPlayback from '@/components/medium/VPlayback.vue';
    import VBackdropAnime from '@/components/small/VBackdropAnime.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
    import VEventToneMenu from '@/components/medium/VEventToneMenu.vue';
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

                current_fitler_type_index: 0,
                filter_types: ["Best", "Latest"],

                api_page_increment: 1,
                event_rooms: [] as GroupedEventsTypes[],
                selected_event: null as EventsAndLikeDetailsTypes|null,
                playback_teleport_event_id: '',
            };
        },
        computed: {
        },
        methods: {
            updateCurrentFilterTypeIndex(index:number) : void {

                this.current_fitler_type_index = index;
            },
            isFilterTypeSelected(index:number) : boolean {

                return this.current_fitler_type_index === index;
            },
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