<template>
    <div>

        <!--sorting options-->
        <div class="pb-8 flex flex-col">

            <!--open/close options, arrow-->
            <div
                ref="open_close_sort_menu_button"
                class="w-fit"
            >

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
                    <span class="pr-2">Filters</span>
                    <i
                        :class="[
                            is_sort_menu_open ? '-rotate-180' : 'rotate-0',
                            'fas text-xs fa-chevron-down transition-transform'
                        ]"
                        aria-hidden="true"
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
                v-click-outside="{
                    var_name_for_element_bool_status: 'is_sort_menu_open',
                    refs_to_exclude: ['open_close_sort_menu_button']
                }"
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
                                        aria-hidden="true"
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

        <div class="flex flex-col gap-8">
            <TransitionGroupFade>

                <!--event_rooms-->
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

                <!--no event_rooms-->
                <VDialogPlain
                    v-show="canShowEventRoomsEmptyMessage"
                    :prop-has-border="false"
                    :prop-has-auto-spacing="false"
                >
                    <template #logo>
                        <i class="far fa-face-meh-blank" aria-hidden="true"></i>
                    </template>
                    <template #title>
                        <span>No events found.</span>
                    </template>
                    <template #content>
                        <span>The filters can be changed to explore other content!</span>
                    </template>
                </VDialogPlain>

                <!--reconsider loading more events -->
                <VDialogPlain
                    v-show="canPauseScrolling"
                    :prop-has-auto-spacing="true"
                    :prop-has-border="true"
                >
                    <template #title>
                        <span>
                            {{ getPlayedEventsLength }} recordings played!
                        </span>
                    </template>
                    <template #content>
                        <div class="flex flex-col gap-4">
                            <span>
                                Hope you're having a good time. Don't forget to take a break!
                            </span>
                            <VActionSpecial
                                @click="continueScrolling()"
                                prop-element="button"
                                prop-element-size="s"
                                prop-font-size="s"
                                :prop-is-icon-only="false"
                                type="button"
                                class="w-full"
                            >
                                <span class="mx-auto">Load more events</span>
                            </VActionSpecial>
                        </div>
                    </template>
                </VDialogPlain>
            </TransitionGroupFade>
        </div>

        <div id="load-more-event-rooms-observer-target"></div>

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
    import VPlayback from '@/components/medium/VPlayback.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
    import VEventToneMenu from '@/components/medium/VEventToneMenu.vue';
    import VActionSpecial from '@/components/small/VActionSpecial.vue';
    import VActionTextOnly from '@/components/small/VActionTextOnly.vue';
    import VDialogPlain from '@/components/small/VDialogPlain.vue';
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

                is_fetching: false,
                can_observer_fetch: true,

                selected_event: null as EventsAndLikeDetailsTypes|null,
                playback_teleport_event_id: '',
                played_events_by_id: [] as number[],
                played_events_quantity_to_pause_scrolling: 50,
                can_pause_scrolling: false,
            };
        },
        computed: {
            getPlayedEventsLength() : number {

                return this.played_events_by_id.length;
            },
            canPauseScrolling() : boolean {

                return this.is_fetching === false && this.can_pause_scrolling === true;
            },
            canShowEventRoomsEmptyMessage() : boolean {

                return this.is_fetching === false && this.filtered_grouped_events_store.getEventRoomsForBrowsing.length === 0;
            },
        },
        methods: {
            async continueScrolling() : Promise<void> {

                const is_first_page = this.filtered_grouped_events_store.getEventRoomsForBrowsing.length === 0;

                this.can_pause_scrolling = false;

                await this.getEventRooms(
                    this.filtered_grouped_events_store.selected_event_tone,
                    this.filtered_grouped_events_store.current_filter_type_index,
                    is_first_page
                );
            },
            openSortMenu() : void {

                this.is_sort_menu_open = !this.is_sort_menu_open;
            },
            updateCurrentFilterTypeIndex(index:number) : void {

                this.filtered_grouped_events_store.updateCurrentFilterTypeIndex(index);
                
                const selected_event_tone = this.filtered_grouped_events_store.getSelectedEventTone;

                this.getEventRooms(selected_event_tone, index, true);
            },
            isFilterTypeSelected(index:number) : boolean {

                return this.filtered_grouped_events_store.getCurrentFilterTypeIndex === index;
            },
            async getEventRooms(
                event_tone:EventTonesTypes|null,
                current_filter_type_index:number,
                is_first_page:boolean
            ): Promise<void> {

                this.is_fetching = true;
                this.can_observer_fetch = false;

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
                    this.is_fetching = false;
                    this.can_observer_fetch = true;
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

                await axios.get(full_url)
                .then((results: any) => {

                    this.filtered_grouped_events_store.insertEventRooms(event_tone, current_filter_type_index, results.data['data']);
                    console.log('API success');
                })
                .catch((error: any) => {

                    notify({
                        title: "Could not get events",
                        text: error.response.data['message'],
                        type: "error"
                    }, 3000);

                }).finally(()=>{

                    this.is_fetching = false;
                    this.can_observer_fetch = true;
                });
            },
            async handleNewSelectedEventTone(event_tone:EventTonesTypes|null) : Promise<void> {

                this.filtered_grouped_events_store.updateSelectedEventTone(event_tone);

                this.getEventRooms(event_tone, this.filtered_grouped_events_store.getCurrentFilterTypeIndex, true);
            },
            handleNewSelectedEvent(event:EventsAndLikeDetailsTypes|null) : void {

                this.selected_event = event;

                if(event === null){

                    return;
                }

                //must be the same as in VEventCard
                this.playback_teleport_event_id = '#playback-teleport-event-id-' + event.id.toString();

                //record how many unique events have been played
                if(this.played_events_by_id.includes(event.id) === false){

                    this.played_events_by_id.push(event.id);
                }

                //check whether can stop scrolling
                if(
                    this.can_pause_scrolling === false &&
                    (this.played_events_by_id.length % this.played_events_quantity_to_pause_scrolling) === 0
                ){

                    this.can_pause_scrolling = true;
                }
            },
        },
        beforeMount(){

            //listen to store
            this.currently_playing_event_store.$subscribe((mutation, state)=>{

                this.handleNewSelectedEvent(state.playing_event);
            });

            this.getEventRooms(
                this.filtered_grouped_events_store.getSelectedEventTone,
                this.filtered_grouped_events_store.getCurrentFilterTypeIndex,
                true,
            );
        },
        mounted(){

            //set up observer for infinite scroll
            const observer_target = document.querySelector('#load-more-event-rooms-observer-target');

            const observer = new IntersectionObserver(()=>{

                if(
                    this.can_observer_fetch === false ||
                    this.can_pause_scrolling === true ||
                    this.filtered_grouped_events_store.getEventRoomsForBrowsing.length === 0
                ){

                    return;
                }

                this.getEventRooms(
                    this.filtered_grouped_events_store.getSelectedEventTone,
                    this.filtered_grouped_events_store.getCurrentFilterTypeIndex,
                    false,
                );
            }, {
                threshold: 1,
            });

            if(observer_target !== null){

                observer.observe(observer_target);
            }
        },
    });
</script>