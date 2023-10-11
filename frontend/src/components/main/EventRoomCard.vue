<template>
    <div
        :class="[
            propHasBorder === true ? 'px-4 pt-8 pb-12      border border-theme-light-gray rounded-lg' : '',
            'flex flex-col'
        ]"
    >

        <!--title and datetime-->
        <div
            v-if="propShowTitle === true"
            class="pb-10"
        >

            <VActionTextOnly
                prop-element="a"
                :href="event_room_url"
                rel="ugc"
                class="h-fit"
            >
                <VTitle
                    propFontSize="s"
                    class="w-full shade-text-when-hover transition-colors"
                >

                    <template #title>
                        <span
                            v-if="propEventRoom.event_room.generic_status.generic_status_name === 'deleted'"
                            class="italic"
                        >
                            Event and original recording deleted.
                        </span>
                        <span v-else>
                            {{ propEventRoom.event_room.event_room_name }}
                        </span>
                    </template>
                    <template v-if="propEventRoom.event_room.generic_status.generic_status_name !== 'deleted'" #titleDescription>
                        <span>{{ pretty_when_created }}</span>
                    </template>
                </VTitle>
            </VActionTextOnly>
        </div>

        <!--more than 1 event each-->
        <div v-if="originatorCount > 0 && responderCount > 0" class="flex flex-col gap-10">

            <!--originator-->
            <div
                v-if="originatorCount > 0"
                class="flex flex-col gap-2"
            >
                <VUser
                    :propUsername="propEventRoom.originator!.user.username"
                />
                <VEventCard
                    :propEvent="propEventRoom.originator"
                    :propIsSelected="checkIsSelected(propEventRoom.originator!.id)"
                    @isSelected="handleNewSelectedEvent($event)"
                />
                <VEventTools
                    :propEvent="propEventRoom.originator"
                    :propEventRoomId="propEventRoom.event_room.id"
                    :prop-filtered-grouped-events-store-event-room-index="propFilteredGroupedEventsStoreEventRoomIndex"
                />
            </div>

            <!--responders-->
            <div
                v-for="(event, index) in propEventRoom.responder" :key="event.id"
                class="flex flex-col gap-2"
            >
                <VUser
                    :propUsername="event.user.username"
                />
                <VEventCard
                    :propEvent="event"
                    :propIsSelected="checkIsSelected(event.id)"
                    @isSelected="handleNewSelectedEvent($event)"
                />
                <VEventTools
                    :propEvent="event"
                    :propEventRoomId="propEventRoom.event_room.id"
                    :prop-filtered-grouped-events-store-event-room-index="propFilteredGroupedEventsStoreEventRoomIndex"
                    :prop-filtered-grouped-events-store-event-index="index"
                />
            </div>
        </div>

        <!--only 1 event total-->
        <div v-else class="flex flex-col gap-10">

            <!--originator-->
            <div
                v-if="originatorCount > 0"
                class="flex flex-col gap-2"
            >
                <VUser
                    :propUsername="propEventRoom.originator!.user.username"
                />
                <VEventCard
                    v-if="propLoadVEventCardsOnly"
                    :propEvent="propEventRoom.originator"
                    :propIsSelected="checkIsSelected(propEventRoom.originator!.id)"
                    @isSelected="handleNewSelectedEvent($event)"
                />
                <VPlayback
                    v-else
                    :propEvent="propEventRoom.originator"
                    :propAudioVolumePeaks="propEventRoom.originator!.audio_volume_peaks"
                    :propBucketQuantity="propEventRoom.originator!.audio_volume_peaks.length"
                />
                <VEventTools
                    :propEvent="propEventRoom.originator"
                    :propEventRoomId="propEventRoom.event_room.id"
                    :prop-filtered-grouped-events-store-event-room-index="propFilteredGroupedEventsStoreEventRoomIndex"
                />
            </div>

            <!--responders-->
            <div v-if="responderCount > 0">
                <div v-if="propLoadVEventCardsOnly">
                    <div
                        v-for="(event, index) in propEventRoom.responder" :key="event.id"
                        class="flex flex-col gap-2"
                    >
                        <VUser
                            :propUsername="event.user.username"
                        />
                        <VEventCard
                            :propEvent="event"
                            :propIsSelected="checkIsSelected(event.id)"
                            @isSelected="handleNewSelectedEvent($event)"
                        />
                        <VEventTools
                            :propEvent="event"
                            :propEventRoomId="propEventRoom.event_room.id"
                            :prop-filtered-grouped-events-store-event-room-index="propFilteredGroupedEventsStoreEventRoomIndex"
                            :prop-filtered-grouped-events-store-event-index="index"
                        />
                    </div>
                </div>
                <div v-else>
                    <div
                        v-for="(event, index) in propEventRoom.responder" :key="event.id"
                        class="flex flex-col gap-2"
                    >
                        <VUser
                            :propUsername="event.user.username"
                        />
                        <VPlayback
                            :propEvent="event"
                            :propAudioVolumePeaks="event.audio_volume_peaks"
                            :propBucketQuantity="event.audio_volume_peaks.length"
                        />
                        <VEventTools
                            :propEvent="event"
                            :propEventRoomId="propEventRoom.event_room.id"
                            :prop-filtered-grouped-events-store-event-room-index="propFilteredGroupedEventsStoreEventRoomIndex"
                            :prop-filtered-grouped-events-store-event-index="index"
                        />
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    import VTitle from '../small/VTitle.vue';
    import VPlayback from '/src/components/medium/VPlayback.vue';
    import VEventCard from '/src/components/small/VEventCard.vue';
    import VEventTools from '/src/components/medium/VEventTools.vue';
    import VUser from '/src/components/small/VUser.vue';
    import VActionTextOnly from '../small/VActionTextOnly.vue';
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import { prettyTimePassed } from '@/helper_functions';
    import GroupedEventsTypes from '@/types/GroupedEvents.interface';
    import EventsAndLikeDetailsTypes from '@/types/EventsAndLikeDetails.interface';
    import { useCurrentlyPlayingEventStore } from '@/stores/CurrentlyPlayingEventStore';

    export default defineComponent({
        data() {
            return {
                currently_playing_event_store: useCurrentlyPlayingEventStore(),
                selected_event: null as EventsAndLikeDetailsTypes|null,
                pretty_when_created: '',

                event_room_url: '',
            };
        },
        props: {
            propEventRoom: {
                type: Object as PropType<GroupedEventsTypes>,
                required: true,
            },
            propShowTitle: {
                type: Boolean,
                default: true
            },
            propHasBorder: {
                type: Boolean,
                default: false
            },
            propFilteredGroupedEventsStoreEventRoomIndex: {
                type: Number,
                required: false
            },
            propLoadVEventCardsOnly: {
                type: Boolean,
                default: false
            },
        },
        computed: {
            originatorCount() : number {

                if(this.propEventRoom === null || this.propEventRoom.originator === null){

                    return 0;
                }

                return 1;
            },
            responderCount() : number {

                if(this.propEventRoom === null){

                    return 0;
                }

                return this.propEventRoom.responder.length;
            },
        },
        methods: {
            checkIsSelected(event_id:number) : boolean {

                return this.selected_event !== null && this.selected_event.id === event_id;
            },
            handleNewSelectedEvent(event:EventsAndLikeDetailsTypes) : void {

                this.currently_playing_event_store.$patch({
                    playing_event: event
                });
            },
        },
        mounted(){

            //set up Axios appropriately

            this.pretty_when_created = prettyTimePassed(new Date(this.propEventRoom.event_room.when_created));

            //listen to store
            this.currently_playing_event_store.$subscribe((mutation, state)=>{

                this.selected_event = state.playing_event as EventsAndLikeDetailsTypes|null;
            });

            if(this.propShowTitle === true){

                this.event_room_url = window.location.origin + '/event/' + this.propEventRoom.event_room.id.toString();
            }
        },
    });
</script>