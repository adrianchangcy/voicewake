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

            <!--open/close options, arrow-->
            <div class="w-fit">

                <!--open/close options-->
                <VActionSpecial
                    @click="openSortMenu()"
                    prop-element="button"
                    type="button"
                    prop-element-size="s"
                    prop-font-size="s"
                    :prop-is-icon-only="false"
                    :prop-is-enabled="true"
                    class="w-fit px-4 flex-row"
                >
                    <span class="pr-2">Sort</span>
                    <i
                        :class="[
                            is_sort_menu_open ? '-rotate-180' : 'rotate-0',
                            'fas text-xs fa-chevron-down transition-transform'
                        ]"
                    ></i>
                </VActionSpecial>

                <!--arrow-->
                <!--needs mt-4 to stay to prevent snapping-->
                <div class="mt-4 relative">
                    <div
                        v-show="is_sort_menu_open"
                        class="z-20 w-2 h-2 absolute -top-1 left-0 right-0 m-auto bg-theme-light border-l-2 border-t-2 border-theme-black rotate-45"
                    ></div>
                </div>
            </div>

            <div
                v-show="is_sort_menu_open"
                class="w-[75%] h-0 relative"
            >

                <!--options-->
                <div class="absolute w-full h-fit z-10">

                    <!--use gap-3 because VEventToneMenu.vue has py-1-->
                    <div class="flex flex-col p-4 gap-3 rounded-lg border-2 border-theme-black bg-theme-light/60 backdrop-blur">

                        <!--filter type-->
                        <div class="flex flex-row items-center gap-2">
                            <VActionTextOnly
                                v-for="(filter_type, index) in filtered_grouped_events_store.getFilterTypes" :key="index"
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
                            </VActionTextOnly>
                        </div>

                        <!--event tones-->
                        <VEventToneMenu
                            :prop-is-open="true"
                            :prop-close-when-selected="false"
                            :prop-has-deselect-option="true"
                            :prop-must-track-selected-option="true"
                            @eventToneSelected="handleNewSelectedEventTone($event)"
                        />
                    </div>
                </div>
            </div>
        </div>

        <!--event_rooms-->
        <TransitionGroupFade>
            <div class="flex flex-col gap-8">
                <EventRoomCard
                    v-for="(event_room, index) in filtered_grouped_events_store.getEventRoomsForBrowsing" :key="event_room.event_room.id"
                    :prop-filtered-grouped-events-store-event-room-index="index"
                    :prop-show-title="true"
                    :prop-event-room="event_room"
                    :prop-has-border="true"
                    @newSelectedEvent=handleNewSelectedEvent($event)
                />

                <!--loading event_rooms-->
                <EventRoomCardSkeleton
                    v-show="is_fetching"
                    :prop-has-border="true"
                    :prop-event-quantity="2"
                />
            </div>
        </TransitionGroupFade>

        <VActionSpecial
            @click="getEventRooms(
                filtered_grouped_events_store.getSelectedEventTone,
                filtered_grouped_events_store.getCurrentFilterTypeIndex,
                false
            )"
            prop-element="button"
            type="button"
            prop-element-size="l"
            prop-font-size="l"
            :prop-is-icon-only="false"
            :prop-is-enabled="!is_fetching"
            class="w-full mt-16"
        >
            <span v-show="!is_fetching" class="mx-auto">
                Load more events
            </span>
            <VLoading v-show="is_fetching" propElementSize="l" class="mx-auto">
                <span class="pl-2">Loading events...</span>
            </VLoading>
        </VActionSpecial>


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
    import EventRoomCardSkeleton from '@/components/skeleton/EventRoomCardSkeleton.vue';
    import VTitle from '@/components/small/VTitle.vue';
    import VPlayback from '@/components/medium/VPlayback.vue';
    import VBackdropAnime from '@/components/small/VBackdropAnime.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
    import VEventToneMenu from '@/components/medium/VEventToneMenu.vue';
    import VActionSpecial from '@/components/small/VActionSpecial.vue';
    import VActionTextOnly from '@/components/small/VActionTextOnly.vue';
    import VLoading from '/src/components/small/VLoading.vue';
</script>


<script lang="ts">
    import { defineComponent, } from 'vue';
    import { notify } from 'notiwind';
    import EventsAndLikeDetailsTypes from '@/types/EventsAndLikeDetails.interface';
    import EventTonesTypes from '@/types/EventTones.interface';
    import { useCurrentlyPlayingEventStore } from '@/stores/CurrentlyPlayingEventStore';
    import { useFilteredGroupedEventsStore } from '@/stores/FilteredGroupedEventsStore';
    const axios = require('axios');


    export default defineComponent({
        name: 'BrowseEventRoomsApp',
        data(){
            return {
                currently_playing_event_store: useCurrentlyPlayingEventStore(),
                filtered_grouped_events_store: useFilteredGroupedEventsStore(),

                is_sort_menu_open: false,

                fetching_event_rooms_timeout: null as number|null,
                is_fetching: false,

                selected_event: null as EventsAndLikeDetailsTypes|null,
                playback_teleport_event_id: '',
            };
        },
        computed: {
        },
        methods: {
            openSortMenu() : void {

                this.is_sort_menu_open = !this.is_sort_menu_open;
            },
            updateCurrentFilterTypeIndex(index:number) : void {

                this.filtered_grouped_events_store.updateCurrentFilterTypeIndex(index);
                
                const selected_event_tone = this.filtered_grouped_events_store.getSelectedEventTone;

                this.fetching_event_rooms_timeout = window.setTimeout(()=>{

                    this.getEventRooms(selected_event_tone, index, true);

                }, 500);
            },
            isFilterTypeSelected(index:number) : boolean {

                return this.filtered_grouped_events_store.getCurrentFilterTypeIndex === index;
            },
            async getEventRooms(
                event_tone:EventTonesTypes|null,
                current_filter_type_index:number,
                is_first_page:boolean
            ): Promise<void> {

                
                //initialise to have all necessary keys available
                //will only do so when no data exists
                if(is_first_page === true){

                    this.filtered_grouped_events_store.initialiseDataOnFirstPageAfterFilterChange(
                        event_tone, current_filter_type_index
                    );
                }

                //check if we already have data
                if(
                    is_first_page === true &&
                    this.filtered_grouped_events_store.hasDataOnFirstPageAfterFilterChange(
                        event_tone, current_filter_type_index
                    ) === true
                ){

                    //do nothing else, as template uses getter, which auto-retrieves for us
                    return;
                }

                //no existing data, proceed

                //construct URL
                let full_url = window.location.origin + "/api/event-rooms/list/completed/best/all/";

                if(event_tone === null){

                    full_url += (
                        this.filtered_grouped_events_store.getNoEventToneEventRooms[current_filter_type_index]['current_page'] + 1
                    ).toString();

                }else{

                    full_url += event_tone.event_tone_slug + "/";
                    full_url += (
                        this.filtered_grouped_events_store.getSelectedEventToneEventRooms[event_tone.id][current_filter_type_index]['current_page'] + 1
                    ).toString();
                }

                this.is_fetching = true;

                await axios.get(full_url)
                .then((results: any) => {

                    this.filtered_grouped_events_store.insertEventRooms(event_tone, current_filter_type_index, results.data['data']);

                })
                .catch((error: any) => {

                    notify({
                        title: "Could not get events",
                        text: error.response.data['message'],
                        type: "error"
                    }, 3000);

                }).finally(()=>{

                    this.is_fetching = false;
                });
            },
            async handleNewSelectedEventTone(event_tone:EventTonesTypes|null) : Promise<void> {

                this.filtered_grouped_events_store.updateSelectedEventTone(event_tone);

                this.fetching_event_rooms_timeout !== null ? window.clearTimeout(this.fetching_event_rooms_timeout) : null;

                this.fetching_event_rooms_timeout = window.setTimeout(()=>{

                    this.getEventRooms(event_tone, this.filtered_grouped_events_store.getCurrentFilterTypeIndex, true);

                }, 500);
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

            //do first API call in setTimeout to ensure that handleNewSelectedEventTone() won't clash
            this.fetching_event_rooms_timeout = window.setTimeout(()=>{

                this.getEventRooms(null, this.filtered_grouped_events_store.getCurrentFilterTypeIndex, true);
            }, 0);

            //listen to store
            this.currently_playing_event_store.$subscribe((mutation, state)=>{

                this.handleNewSelectedEvent(state.playing_event);
            });
        }
    });
</script>