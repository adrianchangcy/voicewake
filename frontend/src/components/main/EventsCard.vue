<template>
    <div
        :class="[
            propHasBorder === true ? 'px-4 pt-4 pb-14      border border-theme-light-gray rounded-lg' : '',
            'flex flex-col'
        ]"
    >

        <!--events-->
        <div
            class="flex flex-col gap-8"
        >
            <TransitionGroupFade>
                <div
                    v-for="event in propEvents" :key="event.id"
                >
                    <VEventCard
                        :propEvent="event"
                        :propIsSelected="checkIsSelected(event.id)"
                        @isSelected="handleNewSelectedEvent($event)"
                    />
                </div>

                <div v-show="propIsFetching" class="flex flex-col gap-8">
                    <div class="w-full h-20 rounded-lg skeleton"></div>
                    <div class="w-full h-20 rounded-lg skeleton"></div>
                </div>
                
            </TransitionGroupFade>
        </div>
    </div>
</template>

<script setup lang="ts">
    import VEventCard from '/src/components/small/VEventCard.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import EventsTypes from '@/types/Events.interface';
    import { useCurrentlyPlayingEventStore } from '@/stores/CurrentlyPlayingEventStore';

    export default defineComponent({
        data() {
            return {
                currently_playing_event_store: useCurrentlyPlayingEventStore(),
                selected_event: null as EventsTypes|null,
                pretty_when_created: '',
            };
        },
        props: {
            propEvents: {
                type: Object as PropType<EventsTypes[]>,
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
            propIsFetching: {
                type: Boolean,
                default: false
            },
        },
        computed: {
        },
        methods: {
            checkIsSelected(event_id:number) : boolean {

                return this.selected_event !== null && this.selected_event.id === event_id;
            },
            handleNewSelectedEvent(event:EventsTypes) : void {

                this.currently_playing_event_store.$patch({
                    playing_event: event
                });
            },
        },
        mounted(){

            //listen to store
            this.currently_playing_event_store.$subscribe((mutation, state)=>{

                this.selected_event = state.playing_event as EventsTypes|null;
            });
        },
    });
</script>