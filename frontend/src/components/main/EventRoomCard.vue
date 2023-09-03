<template>
    <div
        :class="[
            propHasBorder === true ? 'px-4 pt-10 pb-12 mb-8      border border-theme-light-gray rounded-lg' : '',
            'flex flex-col'
        ]"
    >

        <!--title and datetime-->
        <div
            v-if="propShowTitle === true"
            class="h-fit pb-10"
        >
            <VTitle
                propFontSize="s"
                class="w-full"
            >
                <template #title>
                    <span>{{ propEventRoom.event_room.event_room_name }}</span>
                </template>
                <template #titleDescription>
                    <span>{{ pretty_when_created }}</span>
                </template>
            </VTitle>
        </div>

        <!--more than 1 event total-->
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
                    @isSelected="handleNewSelectedEvent($event)"
                    :propIsSelected="checkIsSelected(propEventRoom.originator!.id)"
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
                <VUser
                    :propUsername="event.user.username"
                />
                <VEventCard
                    :propEvent="event"
                    @isSelected="handleNewSelectedEvent($event)"
                    :propIsSelected="checkIsSelected(event.id)"
                />
                <VEventTools
                    :propEvent="event"
                    :propEventRoomId="propEventRoom.event_room.id"
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
                <VPlayback
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
            <div
                v-for="event in propEventRoom.responder" :key="event.id"
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
                />
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
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import { prettyTimePassed } from '@/helper_functions';
    import GroupedEventsTypes from '@/types/GroupedEvents.interface';
    import EventsAndLikeDetailsTypes from '@/types/EventsAndLikeDetails.interface';
    import { useCurrentlyPlayingEventStore } from '@/stores/CurrentlyPlayingEventStore';
    const axios = require('axios');

    export default defineComponent({
        data() {
            return {
                currently_playing_event_store: useCurrentlyPlayingEventStore(),
                selected_event: null as EventsAndLikeDetailsTypes|null,
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
            checkIsSelected(event_id:number) : boolean {

                return this.selected_event !== null && this.selected_event.id === event_id;
            },
            handleNewSelectedEvent(event:EventsAndLikeDetailsTypes) : void {

                this.currently_playing_event_store.$patch({
                    playing_event: event
                });
            }
        },
        mounted(){

            //set up Axios appropriately
            this.axiosSetup();

            this.pretty_when_created = prettyTimePassed(new Date(this.propEventRoom.event_room.when_created));

            //listen to store
            this.currently_playing_event_store.$subscribe((mutation, state)=>{

                this.selected_event = state.playing_event;
            });
        },
    });
</script>