<template>
    <div>

        <!--sorting options-->
        <div class="flex flex-col pb-14">

            <!--options-->
            <div ref="open_close_sort_menu_button">

                <!--open/close options-->
                <VAction
                    @click="toggleSortMenu()"
                    prop-element="button"
                    type="button"
                    prop-element-size="s"
                    prop-font-size="s"
                    :prop-is-icon-only="false"
                    :prop-is-enabled="true"
                    class="w-fit mx-auto px-4 flex-row"
                >
                    <span class="pr-2">Filters</span>
                    <i
                        :class="[
                            is_sort_menu_open ? '-rotate-180' : 'rotate-0',
                            'fas text-xs fa-chevron-down transition-transform'
                        ]"
                        aria-hidden="true"
                    ></i>
                </VAction>

                <!--options menu-->
                <div class="h-0 relative">

                    <!--arrow-->
                    <div
                        v-show="is_sort_menu_open"
                        class="z-30 w-2 h-2 absolute top-3 left-0 right-0 m-auto bg-theme-light border-l-2 border-t-2 border-theme-black rotate-45"
                    ></div>

                    <!--menu-->
                    <div
                        v-show="is_sort_menu_open"
                        v-click-outside="{
                            var_name_for_element_bool_status: 'is_sort_menu_open',
                            refs_to_exclude: ['open_close_sort_menu_button']
                        }"
                        class="absolute w-full h-fit top-4 z-20 flex flex-col p-4 gap-4 rounded-lg border-2 border-theme-black bg-theme-light"
                    >
    
                        <!--filter type-->
                        <div class="w-fit flex flex-row items-center border rounded-lg border-theme-light-gray px-2">
                            <VActionTextOnly
                                v-for="(filter_type, index) in filtered_grouped_events_store.getFilterTypes" :key="index"
                                @click="updateCurrentFilterTypeIndex(index)"
                                prop-element="button"
                                prop-element-size="s"
                                prop-font-size="s"
                                :prop-is-icon-only="true"
                                :class="[
                                    isSelectedFilterType(index) ? 'border-b-theme-black' : 'border-b-transparent',
                                    'border-b-2 rounded-b-none p-2'
                                ]"
                            >
                                <span>{{ filter_type }}</span>
                            </VActionTextOnly>
                        </div>
    
                        <!--event tones-->
                        <VEventToneMenu
                            :prop-is-open="true"
                            :prop-close-when-selected="false"
                            :prop-has-deselect-option="true"
                            :prop-must-track-selected-option="true"
                            @eventToneSelected="handleNewSelectedEventTone($event)"
                            class="border rounded-l-lg border-theme-light-gray"
                        />
                    </div>
                </div>
            </div>

            <!--event roles-->
            <div v-show="propIsUserProfilePage" class="w-full grid grid-cols-2">
                <VActionTextOnly
                    @click="updateCurrentEventRoleNameIndex(0)"
                    prop-element="button"
                    prop-element-size="s"
                    prop-font-size="s"
                    :prop-is-icon-only="true"
                    :class="[
                        isSelectedEventRoleName(0) ? 'border-b-theme-black' : 'border-b-theme-medium-gray',
                        'col-span-1 border-b-2 rounded-b-none p-2'
                    ]"
                >
                    <span class="mx-auto">
                        <i class="fas fa-comment"></i>
                        <span class="pl-2">Started</span>
                    </span>
                </VActionTextOnly>
                <VActionTextOnly
                    @click="updateCurrentEventRoleNameIndex(1)"
                    prop-element="button"
                    prop-element-size="s"
                    prop-font-size="s"
                    :prop-is-icon-only="true"
                    :class="[
                        isSelectedEventRoleName(1) ? 'border-b-theme-black' : 'border-b-theme-medium-gray',
                        'col-span-1 border-b-2 rounded-b-none p-2'
                    ]"
                >
                    <span class="mx-auto">
                        <i class="fas fa-comments"></i>
                        <span class="pl-2">Replied</span>
                    </span>
                </VActionTextOnly>
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
                    :prop-load-v-event-cards-only="true"
                    @newSelectedEvent=handleNewSelectedEvent($event)
                />

                <!--loading event_rooms-->
                <EventRoomCardSkeleton
                    v-show="is_fetching"
                    :prop-has-border="true"
                    :prop-event-quantity="2"
                />
            </TransitionGroupFade>

            <!--dialogs-->
            <!--make height at least same or bigger than largest element to avoid jolting-->
            <div class="h-48 relative">
                <TransitionGroupFade :prop-has-absolute="true">

                    <!--no event_rooms-->
                    <VDialogPlain
                        v-show="canShowEventRoomsEmptyMessage || canShowNoNewEventRoomsMessage"
                        :prop-has-border="false"
                        :prop-has-auto-spacing="false"
                        class="w-full"
                    >
                        <template #logo>
                            <i class="far fa-face-meh-blank" aria-hidden="true"></i>
                        </template>
                        <template #title>
                            <span v-show="canShowEventRoomsEmptyMessage">No events found.</span>
                            <span v-show="canShowNoNewEventRoomsMessage">You've reached the end.</span>
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
                        class="w-full"
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
                                    <span class="mx-auto">Load more recordings</span>
                                </VActionSpecial>
                            </div>
                        </template>
                    </VDialogPlain>
                </TransitionGroupFade>
            </div>
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
    import VAction from '@/components/small/VAction.vue';
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

                user_profile_username: "",  //only used at profile page

                is_sort_menu_open: false,

                is_fetching: false,
                can_observer_fetch: false,
                has_no_event_rooms_left_to_fetch: false,

                selected_event: null as EventsAndLikeDetailsTypes|null,
                playback_teleport_event_id: '',

                played_events_by_id: [] as number[],
                played_events_quantity_to_pause_scrolling: 50,
                can_pause_scrolling: false,
            };
        },
        props: {
            propIsUserProfilePage: {
                type: Boolean,
                default: false
            },
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
            canShowNoNewEventRoomsMessage() : boolean {

                return (
                    this.is_fetching === false &&
                    this.filtered_grouped_events_store.getEventRoomsForBrowsing.length > 0 &&
                    this.has_no_event_rooms_left_to_fetch === true
                );
            }
        },
        methods: {
            isSelectedEventRoleName(index:number) : boolean {

                return index === this.filtered_grouped_events_store.getCurrentEventRoleNameIndex;
            },
            isSelectedFilterType(index:number) : boolean {

                return index === this.filtered_grouped_events_store.getCurrentFilterTypeIndex;
            },
            async continueScrolling() : Promise<void> {

                const is_first_page = this.filtered_grouped_events_store.getEventRoomsForBrowsing.length === 0;

                this.can_pause_scrolling = false;

                await this.getEventRooms(
                    this.filtered_grouped_events_store.getSelectedEventTone,
                    this.filtered_grouped_events_store.getCurrentEventRoleNameIndex,
                    this.filtered_grouped_events_store.getCurrentFilterTypeIndex,
                    is_first_page,
                );
            },
            toggleSortMenu() : void {

                this.is_sort_menu_open = !this.is_sort_menu_open;
            },
            async updateCurrentEventRoleNameIndex(index:number) : Promise<void> {

                this.filtered_grouped_events_store.updateCurrentEventRoleNameIndex(index);

                await this.getEventRooms(
                    this.filtered_grouped_events_store.getSelectedEventTone,
                    index,
                    this.filtered_grouped_events_store.getCurrentFilterTypeIndex,
                    true,
                );
            },
            async updateCurrentFilterTypeIndex(index:number) : Promise<void> {

                this.filtered_grouped_events_store.updateCurrentFilterTypeIndex(index);
                
                await this.getEventRooms(
                    this.filtered_grouped_events_store.getSelectedEventTone,
                    this.filtered_grouped_events_store.getCurrentEventRoleNameIndex,
                    index,
                    true,
                );
            },
            async getEventRooms(
                event_tone:EventTonesTypes|null,
                current_event_role_name_index:number,
                current_filter_type_index:number,
                is_first_page:boolean
            ): Promise<void> {

                this.is_fetching = true;
                this.can_observer_fetch = false;
                this.has_no_event_rooms_left_to_fetch = false;

                //initialise to have all necessary keys available
                //will only do so when no data exists
                if(is_first_page === true){

                    this.filtered_grouped_events_store.initialiseDataOnFirstPageAfterFilterChange(event_tone);
                }

                //check if we already have data
                if(
                    is_first_page === true &&
                    this.filtered_grouped_events_store.hasDataOnFirstPageAfterFilterChange(
                        event_tone, current_event_role_name_index, current_filter_type_index,
                    ) === true
                ){

                    //do nothing else, as template uses getter, which auto-retrieves for us
                    this.is_fetching = false;
                    this.can_observer_fetch = true;
                    return;
                }

                //no existing data, proceed

                const full_url = await this.constructURL(event_tone, current_event_role_name_index, current_filter_type_index);

                await axios.get(full_url)
                .then((results: any) => {

                    this.filtered_grouped_events_store.insertEventRooms(event_tone, current_event_role_name_index, current_filter_type_index, results.data['data']);

                    if(results.data['data'].length === 0){

                        this.has_no_event_rooms_left_to_fetch = true;
                    }

                    this.can_observer_fetch = true;

                })
                .catch(() => {

                    notify({
                        title: "Error",
                        text: "Oops, something is not right. Try again later.",
                        type: "error"
                    }, 3000);

                }).finally(()=>{

                    this.is_fetching = false;
                });
            },
            async handleNewSelectedEventTone(event_tone:EventTonesTypes|null) : Promise<void> {

                this.filtered_grouped_events_store.updateSelectedEventTone(event_tone);

                await this.getEventRooms(
                    event_tone,
                    this.filtered_grouped_events_store.getCurrentEventRoleNameIndex,
                    this.filtered_grouped_events_store.getCurrentFilterTypeIndex,
                    true,
                );
            },
            async constructURL(
                event_tone:EventTonesTypes|null,
                current_event_role_name_index:number,
                current_filter_type_index:number,
            ) : Promise<string> {

                //construct URL
                let full_url = window.location.origin + "/api/event-rooms/list";

                if(this.propIsUserProfilePage === true){
                    full_url += "/user/" + this.user_profile_username;
                }else{
                    full_url += "/completed";
                }

                //latest/best
                full_url += "/" + this.filtered_grouped_events_store.getFilterTypes[current_filter_type_index].toLowerCase();

                //timeframe
                full_url += "/all";

                if(this.propIsUserProfilePage === true){
                    full_url += "/" + this.filtered_grouped_events_store.getEventRoleNames[current_event_role_name_index].toLowerCase();
                }else if(event_tone !== null){
                    full_url += "/" + event_tone.event_tone_slug;
                }

                //get next page
                if(event_tone === null){

                    full_url += "/" + (
                        this.filtered_grouped_events_store.getNoEventToneEventRooms[current_event_role_name_index][current_filter_type_index]['current_page'] + 1
                    ).toString();

                }else{

                    full_url += "/" + (
                        this.filtered_grouped_events_store.getSelectedEventToneEventRooms[event_tone.id][current_event_role_name_index][current_filter_type_index]['current_page'] + 1
                    ).toString();
                }

                console.log(full_url);

                return full_url;
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
            setUpObserver() : void {

                //set up observer for infinite scroll
                const observer_target = document.querySelector('#load-more-event-rooms-observer-target');

                const observer = new IntersectionObserver(()=>{

                    if(
                        this.can_observer_fetch === false ||
                        this.can_pause_scrolling === true ||
                        this.has_no_event_rooms_left_to_fetch === true
                    ){

                        return;
                    }

                    this.getEventRooms(
                        this.filtered_grouped_events_store.getSelectedEventTone,
                        this.filtered_grouped_events_store.getCurrentEventRoleNameIndex,
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
        },
        beforeMount(){

            //get username
            if(this.propIsUserProfilePage === true){

                const container = (document.getElementById('data-container-get-user-profile') as HTMLElement);

                this.user_profile_username = (container.getAttribute('data-user-profile-username') as string);
            }

            //listen to store
            this.currently_playing_event_store.$subscribe((mutation, state)=>{

                this.handleNewSelectedEvent(state.playing_event as EventsAndLikeDetailsTypes|null);
            });

            this.getEventRooms(
                this.filtered_grouped_events_store.getSelectedEventTone,
                this.filtered_grouped_events_store.getCurrentEventRoleNameIndex,
                this.filtered_grouped_events_store.getCurrentFilterTypeIndex,
                true,
            );
        },
        mounted(){

            this.setUpObserver();
        },
    });
</script>