<template>
    <div>

        <!--user profile-->
        <VUserCard
            v-if="propIsUserProfilePage"
            :prop-username="user_profile_username"
            class="pt-8 pb-14"
        />

        <!--sorting options-->
        <div
            ref="sorting_options_container"
            :class="[
                propIsUserProfilePage ? 'pb-8' : 'pb-10',
                'flex flex-col'
            ]"
        >

            <!--filter-->
            <div ref="open_close_filter_menu_button">

                <!--open/close filter menu-->
                <VAction
                    @click="toggleFilterMenu()"
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
                            is_filter_menu_open ? '-rotate-180' : 'rotate-0',
                            'fas text-xs fa-chevron-down transition-transform'
                        ]"
                        aria-hidden="true"
                    ></i>
                </VAction>

                <!--filter menu-->
                <div class="h-0 relative">

                    <!--arrow-->
                    <div
                        v-show="is_filter_menu_open"
                        class="z-30 w-2 h-2 absolute top-3 left-0 right-0 m-auto bg-theme-light border-l-2 border-t-2 border-theme-black rotate-45"
                    ></div>

                    <!--menu-->
                    <div
                        v-show="is_filter_menu_open"
                        v-click-outside="{
                            var_name_for_element_bool_status: 'is_filter_menu_open',
                            refs_to_exclude: ['open_close_filter_menu_button']
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
                            :prop-initial-event-tone="filtered_grouped_events_store.getSelectedEventTone"
                            :prop-filtered-grouped-events-store="filtered_grouped_events_store"
                            @eventToneSelected="handleNewSelectedEventTone($event)"
                            class="border rounded-l-lg border-theme-light-gray"
                        />
                    </div>
                </div>
            </div>

            <!--event roles-->
            <div v-if="propIsUserProfilePage" class="w-full grid grid-cols-2 px-4">
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
                        <span v-show="isSelectedEventRoleName(0)" class="sr-only">selected</span>
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
                        <span v-show="isSelectedEventRoleName(1)" class="sr-only">selected</span>
                    </span>
                </VActionTextOnly>
            </div>
        </div>

        <!--item-size seems to work like gap size in px, not sure, but it's not needed for DynamicScroller-->
        <!--page-mode is needed here, else it behaves like flex, i.e. DynamicScroller doesn't know when to reuse components-->
        <!--arbitrarily large buffer value solves:
            -whitespace before render that is the same size as "previous elements' height combined" after going past 1st/2nd item
            -no item for keyboard focus, due to being unrendered
        -->
        <!--as long as data persists, backward and close-reopen navigations accurately continue to where the user had left off-->
        <DynamicScroller
            v-show="filtered_grouped_events_store.getEventRoomsForBrowsing.length > 0"
            :items="filtered_grouped_events_store.getEventRoomsForBrowsing"
            :min-item-size="2"
            :buffer="dynamic_scroller_buffer"
            :page-mode="true"
            key-field="event_room_id"
            class="scroller"
        >

            <template #default="{ item, index, active }">

                <!--event_rooms-->
                <DynamicScrollerItem
                    :item="item"
                    :index="index"
                    :active="active"
                >
                    <div class="pb-4">
                        <EventRoomCard
                            :prop-show-title="true"
                            :prop-event-room="item"
                            :prop-has-border="true"
                            :prop-load-v-event-cards-only="true"
                        />
                    </div>
                </DynamicScrollerItem>
            </template>
        </DynamicScroller>

        <!--loading event_rooms-->
        <TransitionFade>
            <EventRoomCardSkeleton
                v-show="is_fetching"
                :prop-has-border="true"
                :prop-event-quantity="2"
            />
        </TransitionFade>

        <!--dialogs-->
        <div class="pt-8 relative">

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
                            {{ getPlayedEventsLength }} recordings played.
                        </span>
                    </template>
                    <template #content>
                        <div class="flex flex-col gap-4">
                            <span>
                                Don't forget to take a break!
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

        <div id="load-more-event-rooms-observer-target"></div>

        <!--VEventCard emits selection, which triggers :to, thus teleporting-->
        <!--presence of VEventCard depends on VEventRoomCard-->
        <!--we don't use :disabled because it will still attempt to teleport to :to-->
        <Teleport
            :to="getVPlaybackTeleportId"
        >
            <VPlayback
                v-show="selected_event !== null"
                :propEvent="selected_event"
                :propIsOpen="true"
                :propAudioVolumePeaks="getSelectedEventAudioVolumePeaks"
                :propBucketQuantity="20"
                :propAutoPlayOnSourceChange="can_autoplay"
                :propPauseTrigger="filter_change_trigger"
            />
        </Teleport>
    </div>
</template>


<script setup lang="ts">
    import EventRoomCard from '@/components/main/EventRoomCard.vue';
    import EventRoomCardSkeleton from '@/components/skeleton/EventRoomCardSkeleton.vue';
    import VPlayback from '@/components/medium/VPlayback.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VEventToneMenu from '@/components/medium/VEventToneMenu.vue';
    import VAction from '@/components/small/VAction.vue';
    import VActionSpecial from '@/components/small/VActionSpecial.vue';
    import VActionTextOnly from '@/components/small/VActionTextOnly.vue';
    import VDialogPlain from '@/components/small/VDialogPlain.vue';
    import VUserCard from '@/components/medium/VUserCard.vue';
    import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller';
</script>


<script lang="ts">
    import { defineComponent, } from 'vue';
    import { notify } from 'notiwind';
    import EventsAndLikeDetailsTypes from '@/types/EventsAndLikeDetails.interface';
    import EventTonesTypes from '@/types/EventTones.interface';
    import { useCurrentlyPlayingEventStore } from '@/stores/CurrentlyPlayingEventStore';
    import { useFilteredGroupedEventsStore } from '@/stores/FilteredGroupedEventsStore';
    import { useCurrentLikesDislikesStore } from '@/stores/CurrentLikesDislikesStore';
    import { isPageAccessedByReload } from '@/helper_functions';
    const axios = require('axios');

    //TODO:
        //#1: clear FilteredGroupedEventsStore on least recent
            //follow through with CurrentLikesDislikesStore and CurrentlyPlayingEventStore


    export default defineComponent({
        name: 'BrowseEventRoomsApp',
        data(){
            return {
                currently_playing_event_store: useCurrentlyPlayingEventStore(),
                filtered_grouped_events_store: useFilteredGroupedEventsStore(this.propIsUserProfilePage),
                current_likes_dislikes_store: useCurrentLikesDislikesStore(this.propIsUserProfilePage),

                user_profile_username: "",  //only used at profile page

                is_filter_menu_open: false,
                can_filter_menu_teleport: false,

                dynamic_scroller_buffer: 1000, //px, larger means rendered earlier, needed for proper tabbing

                selected_event: null as EventsAndLikeDetailsTypes|null,
                filter_change_trigger: false,  //switch between true/false to trigger pause
                can_autoplay: true,

                played_events_by_id: [] as number[],
                played_events_quantity_to_pause_scrolling: 10,
                can_pause_scrolling: false,
                scrolling_timeout: window.setTimeout(()=>{}, 0),
                scrolling_checkpoint_px: 0,

                infinite_scroll_observer: new IntersectionObserver(this.getInfiniteScrollCallback(), {threshold: 1}),
                is_fetching: false,
                is_observer_on_cooldown: false,
                must_skip_observer_once: true,
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
                    this.is_observer_on_cooldown === true
                );
            },
            getVPlaybackTeleportId() : string {

                if(this.selected_event === null){

                    return '#temporary-teleport-target';
                }

                return '#playback-teleport-event-id-' + this.selected_event.id;
            },
            getSelectedEventAudioVolumePeaks() : number[] {

                if(this.selected_event === null){

                    return [];
                }

                return this.selected_event.audio_volume_peaks;
            },
        },
        methods: {
            switchTriggerOnFilterChange() : void {

                this.filter_change_trigger = !this.filter_change_trigger;
            },
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
            toggleFilterMenu() : void {

                this.is_filter_menu_open = !this.is_filter_menu_open;
            },
            async updateCurrentEventRoleNameIndex(index:number) : Promise<void> {

                await this.filtered_grouped_events_store.updateCurrentEventRoleNameIndex(index);

                this.getEventRooms(
                    this.filtered_grouped_events_store.getSelectedEventTone,
                    index,
                    this.filtered_grouped_events_store.getCurrentFilterTypeIndex,
                    true,
                );
            },
            async updateCurrentFilterTypeIndex(index:number) : Promise<void> {

                await this.filtered_grouped_events_store.updateCurrentFilterTypeIndex(index);
                
                this.getEventRooms(
                    this.filtered_grouped_events_store.getSelectedEventTone,
                    this.filtered_grouped_events_store.getCurrentEventRoleNameIndex,
                    index,
                    true,
                );
            },
            async handleNewSelectedEventTone(event_tone:EventTonesTypes|null) : Promise<void> {

                await this.filtered_grouped_events_store.updateSelectedEventTone(event_tone);

                this.getEventRooms(
                    event_tone,
                    this.filtered_grouped_events_store.getCurrentEventRoleNameIndex,
                    this.filtered_grouped_events_store.getCurrentFilterTypeIndex,
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

                //initialise to have all necessary keys available
                //will only do so when no data exists
                if(is_first_page === true){

                    await this.filtered_grouped_events_store.initialiseDataOnFirstPageAfterFilterChange(event_tone);
                }

                //check if we already have data
                if(
                    is_first_page === true &&
                    await this.filtered_grouped_events_store.hasDataOnFirstPageAfterFilterChange(
                        event_tone, current_event_role_name_index, current_filter_type_index,
                    ) === true
                ){

                    //do nothing else, as template uses getter, which auto-retrieves for us
                    this.is_fetching = false;
                    return;
                }

                const check_can_fetch = await this.filtered_grouped_events_store.checkCanFetch(event_tone, current_event_role_name_index, current_filter_type_index);

                if(check_can_fetch === false){

                    this.is_fetching = false;
                    return;
                }

                //no existing data, proceed

                const full_url = await this.constructURL(event_tone, current_event_role_name_index, current_filter_type_index);

                console.log(full_url);

                await axios.get(full_url)
                .then(async (results: any) => {

                    if(results.data['data'].length === 0){

                        this.is_observer_on_cooldown = true;
                    }

                    await this.filtered_grouped_events_store.insertEventRooms(event_tone, current_event_role_name_index, current_filter_type_index, results.data['data']);

                }).catch(() => {

                    notify({
                        title: "Error",
                        text: "Oops, something is not right. Try again later.",
                        type: "error"
                    }, 3000);

                }).finally(()=>{

                    this.is_fetching = false;
                });
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
                }

                //event_tone
                if(event_tone !== null){

                    full_url += "/" + event_tone.event_tone_slug;
                }

                //get next page
                if(event_tone === null){

                    full_url += "/" + (
                        this.filtered_grouped_events_store.getNoEventToneEventRooms[current_event_role_name_index][current_filter_type_index]['current_page']
                    ).toString();

                }else{

                    full_url += "/" + (
                        this.filtered_grouped_events_store.getSelectedEventToneEventRooms[event_tone.id][current_event_role_name_index][current_filter_type_index]['current_page']
                    ).toString();
                }

                return full_url;
            },
            async handleNewSelectedEvent(event:EventsAndLikeDetailsTypes|null, can_autoplay:boolean) : Promise<void> {

                this.can_autoplay = can_autoplay;
                this.selected_event = event;

                if(event === null){

                    return;
                }

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
            getInfiniteScrollCallback() : ()=>void {

                return async ()=>{
                    if(
                        this.is_fetching === true ||
                        this.can_pause_scrolling === true ||
                        this.filtered_grouped_events_store.getEventRoomsForBrowsing.length === 0
                    ){

                        return;
                    }

                    //prevents first run when DOM is still fresh
                    if(this.must_skip_observer_once === true){

                        this.must_skip_observer_once = false;
                        return;
                    }

                    const can_fetch = await this.filtered_grouped_events_store.checkCanFetch(
                        this.filtered_grouped_events_store.getSelectedEventTone,
                        this.filtered_grouped_events_store.getCurrentEventRoleNameIndex,
                        this.filtered_grouped_events_store.getCurrentFilterTypeIndex,
                    );

                    if(can_fetch === false){

                        return;
                    }

                    this.is_observer_on_cooldown = false;

                    //on filter change, we already run getEventRooms()
                    //upon reaching here, that first page fetch is already done
                    this.getEventRooms(
                        this.filtered_grouped_events_store.getSelectedEventTone,
                        this.filtered_grouped_events_store.getCurrentEventRoleNameIndex,
                        this.filtered_grouped_events_store.getCurrentFilterTypeIndex,
                        false,
                    );
                }
            },
            async canShowFilterOptionBelowNavBar() : Promise<void> {

                //currently not used
                //we want to improve accessibility first, e.g. ESC --> nav bar --> fixed filters --> ESC --> resume content

                window.clearTimeout(this.scrolling_timeout);

                //start evaluating past x distance downwards, and showing when user scrolls upwards a bit
                this.scrolling_timeout = window.setTimeout(async ()=>{

                    const target = (this.$refs.sorting_options_container as HTMLElement);

                    //get fixed distance of element relative to document
                    //+1000 for extra space
                    const minimum_scroll_distance_px = target.offsetTop + 400;

                    //compare with current scroll distance
                    if(window.scrollY < this.scrolling_checkpoint_px && window.scrollY > minimum_scroll_distance_px){

                        this.can_filter_menu_teleport = true;

                    }else{

                        this.can_filter_menu_teleport = false;
                    }

                    //set checkpoint for next comparison
                    this.scrolling_checkpoint_px = window.scrollY;

                }, 250);
            },
            async resetStores() : Promise<void> {

                if(
                    this.propIsUserProfilePage === false &&
                    (localStorage.getItem('reset_home_page_event_stores') !== null || isPageAccessedByReload() === true)
                ){

                    await this.filtered_grouped_events_store.partialResetStore();
                    this.current_likes_dislikes_store.$reset();
                    localStorage.removeItem('reset_home_page_event_stores');
                }
            },
        },
        beforeMount(){

            //get username
            if(this.propIsUserProfilePage === true){

                const container = (document.getElementById('data-container-get-user-profile') as HTMLElement);

                this.user_profile_username = (container.getAttribute('data-user-profile-username') as string);
            }

            //reset store if scheduled by home button click at NavBar
            (async ()=>{
                await this.resetStores();
            })();

            //listen from EventRoomCard
            this.currently_playing_event_store.$subscribe((mutation, state)=>{

                //if playing_event is identical to selected_event,
                //it means that this $patch is fired from filter change

                const playing_event = (state.playing_event as EventsAndLikeDetailsTypes|null);

                if(
                    playing_event !== null && this.selected_event !== null &&
                    playing_event.id === this.selected_event.id
                ){

                    return;
                }

                //selected_event from here is fired when user has just manually selected event

                this.handleNewSelectedEvent(playing_event, true);

                if(playing_event !== null){

                    this.filtered_grouped_events_store.updateLastSelectedEvent(playing_event);
                }
            });

            //handle things on filter change
            this.filtered_grouped_events_store.$onAction(({
                name,
                after,
            })=>{

                if(
                    name === 'updateSelectedEventTone' ||
                    name === 'updateCurrentEventRoleNameIndex' ||
                    name === 'updateCurrentFilterTypeIndex'
                ){
                    after(()=>{

                        //last selected event to be currently selected event

                        this.switchTriggerOnFilterChange();

                        const last_selected_event = this.filtered_grouped_events_store.getLastSelectedEvent;
                        this.handleNewSelectedEvent(last_selected_event, false);

                        this.currently_playing_event_store.$patch({
                            playing_event: last_selected_event
                        });

                        this.must_skip_observer_once = true;
                    });
                }
            });

            if(this.filtered_grouped_events_store.getEventRoomsForBrowsing.length === 0){

                (async ()=>{
                    await this.getEventRooms(
                        this.filtered_grouped_events_store.getSelectedEventTone,
                        this.filtered_grouped_events_store.getCurrentEventRoleNameIndex,
                        this.filtered_grouped_events_store.getCurrentFilterTypeIndex,
                        true,
                    ).then(()=>{

                        this.must_skip_observer_once = false;
                    });
                })();
            }
        },
        mounted(){

            //reassign buffer size in case screen height > 1000px
            //better bigger than smaller
            this.dynamic_scroller_buffer = window.innerHeight * 2;

            //set up observer for infinite scroll
            const observer_target = document.querySelector('#load-more-event-rooms-observer-target');

            if(observer_target !== null){

                this.infinite_scroll_observer.observe(observer_target);
            }
        },
        beforeUnmount(){

            this.infinite_scroll_observer.disconnect();
        }
    });
</script>