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

            <VTitle
                propFontSize="s"
                class="w-full"
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
        </div>

        <!--more than 1 event each-->
        <div v-if="originatorCount > 0 && responderCount > 0" class="flex flex-col gap-10">

            <!--originator-->
            <div
                v-show="originatorCount > 0"
                class="flex flex-col gap-2"
            >
                <VUsernameURL
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
                />
            </div>

            <!--responders-->
            <div
                v-for="event in propEventRoom.responder" :key="event.id"
                class="flex flex-col gap-2"
            >
                <VUsernameURL
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
                />
            </div>
        </div>

        <!--only 1 event total-->
        <!--must use v-if here, else VPlayback error, unsure why its code runs when it's using v-else and not v-show-->
        <div v-else class="flex flex-col gap-10">

            <!--originator-->
            <div
                v-show="originatorCount > 0"
                class="flex flex-col gap-2"
            >
                <VUsernameURL
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
                />
            </div>

            <!--responders-->
            <div v-show="responderCount > 0">
                <div v-if="propLoadVEventCardsOnly">
                    <div
                        v-for="event in propEventRoom.responder" :key="event.id"
                        class="flex flex-col gap-2"
                    >
                        <VUsernameURL
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
                        />
                    </div>
                </div>
                <div v-else>
                    <div
                        v-for="event in propEventRoom.responder" :key="event.id"
                        class="flex flex-col gap-2"
                    >
                        <VUsernameURL
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
    import VEventCard from '/src/components/medium/VEventCard.vue';
    import VEventTools from '/src/components/medium/VEventTools.vue';
    import VUsernameURL from '/src/components/small/VUsernameURL.vue';
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
                pretty_when_created: '',
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
        watch: {

        },
        methods: {
            checkIsSelected(event_id:number) : boolean {

                const playing_event = this.currently_playing_event_store.getPlayingEvent;

                return (
                    playing_event !== null &&
                    playing_event.id === event_id
                );
            },
            handleNewSelectedEvent(event:EventsAndLikeDetailsTypes) : void {

                this.currently_playing_event_store.$patch({
                    playing_event: event
                });
            },
        },
        beforeMount(){

            this.pretty_when_created = prettyTimePassed(new Date(this.propEventRoom.event_room.when_created));
        },
    });
</script>