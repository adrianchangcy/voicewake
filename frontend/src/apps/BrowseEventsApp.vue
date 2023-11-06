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
        
                        <!--main filters-->
                        <div class="w-fit flex flex-row items-center border rounded-lg border-theme-light-gray px-2">
                            <VActionTextOnly
                                v-for="(filter_type, index) in filtered_events_store.getMainFilters"
                                :key="index"
                                @click="filtered_events_store.updateCurrentMainFilterIndex(index)"
                                :disabled="filtered_events_store.isSameCurrentMainFilterIndex(index)"
                                prop-element="button"
                                prop-element-size="s"
                                prop-font-size="s"
                                :prop-is-icon-only="true"
                                class="p-2 relative"
                            >
                                <span>{{ filter_type }}</span>
                                <span
                                    v-show="filtered_events_store.isSameCurrentMainFilterIndex(index)"
                                    class="sr-only"
                                >
                                    selected
                                </span>
                                <TransitionFade>
                                    <div
                                        v-show="filtered_events_store.isSameCurrentMainFilterIndex(index)"
                                        class="absolute w-full h-0.5 bg-theme-black left-0 right-0 bottom-0"
                                    ></div>
                                </TransitionFade>
                            </VActionTextOnly>
                        </div>

                        <!--audio_clip_roles-->
                        <div class="w-fit flex flex-row items-center border rounded-lg border-theme-light-gray px-2">
                            <VActionTextOnly
                                v-for="(pretty_audio_clip_role_name, index) in filtered_events_store.getPrettyAudioClipRoleNames"
                                :key="index"
                                @click="filtered_events_store.updateCurrentAudioClipRoleNameIndex(index)"
                                :disabled="filtered_events_store.isSameCurrentAudioClipRoleNameIndex(index)"
                                prop-element="button"
                                prop-element-size="s"
                                prop-font-size="s"
                                :prop-is-icon-only="true"
                                class="p-2 relative"
                            >
                                <span>{{ pretty_audio_clip_role_name }}</span>
                                <span
                                    v-show="filtered_events_store.isSameCurrentAudioClipRoleNameIndex(index)"
                                    class="sr-only"
                                >
                                    selected
                                </span>
                                <TransitionFade>
                                    <div
                                        v-show="filtered_events_store.isSameCurrentAudioClipRoleNameIndex(index)"
                                        class="absolute w-full h-0.5 bg-theme-black left-0 right-0 bottom-0"
                                    ></div>
                                </TransitionFade>
                            </VActionTextOnly>
                        </div>
        
                        <!--audio_clip_tones-->
                        <VAudioClipToneMenu
                            :prop-is-open="true"
                            :prop-close-when-selected="false"
                            :prop-has-deselect-option="true"
                            :prop-must-track-selected-option="true"
                            :prop-initial-audio-clip-tone="filtered_events_store.getCurrentAudioClipTone"
                            :prop-filtered-grouped-audio-clips-store="filtered_events_store"
                            @audioClipToneSelected="filtered_events_store.updateCurrentAudioClipTone($event)"
                            class="border rounded-l-lg border-theme-light-gray"
                        />
                    </div>
                </div>
            </div>
        </div>

        <DynamicScroller
            v-show="filtered_events_store.getEventsForBrowsing.length > 0"
            @visible="restoreScrollY()"
            :items="filtered_events_store.getEventsForBrowsing"
            :min-item-size="2"
            :buffer="dynamic_scroller_buffer"
            :page-mode="true"
            key-field="event_id_as_scroller_index"
            class="scroller"
        >

            <template #default="{ item, index, active }">

                <!--events-->
                <!--DynamicScrollerItem has weird right side overflow clip-->
                <!--px-1 is used to fix it, so other outer elements will require px-1 too-->
                <DynamicScrollerItem
                    :item="item"
                    :index="index"
                    :active="active"
                >
                    <div class="px-1 pb-4">
                        <EventCard
                            :prop-show-title="true"
                            :prop-event="item"
                            :prop-has-border="true"
                            :prop-load-v-audio-clip-cards-only="true"
                        />
                    </div>
                </DynamicScrollerItem>
            </template>
        </DynamicScroller>

        <div class="px-1">
            <!--loading events-->
            <TransitionFade>
                <EventCardSkeleton
                    v-show="is_fetching"
                    :prop-has-border="true"
                    :prop-audio-clip-quantity="2"
                />
            </TransitionFade>

            <!--dialogs-->
            <div class="pt-8 relative">

                <TransitionGroupFade :prop-has-absolute="true">

                    <!--no events-->
                    <VDialogPlain
                        v-show="canShowEventsEmptyMessage || canShowNoNewEventsMessage"
                        :prop-has-border="false"
                        :prop-has-auto-spacing="false"
                        class="w-full"
                    >
                        <template #logo>
                            <i class="far fa-face-meh-blank" aria-hidden="true"></i>
                        </template>
                        <template #title>
                            <span v-show="canShowEventsEmptyMessage">No recordings found.</span>
                            <span v-show="canShowNoNewEventsMessage">You've reached the end.</span>
                        </template>
                        <template #content>
                            <span>The filters can be changed to explore other content!</span>
                        </template>
                    </VDialogPlain>

                    <!--reconsider loading more audio_clips -->
                    <VDialogPlain
                        v-show="canPauseScrolling"
                        :prop-has-auto-spacing="true"
                        :prop-has-border="true"
                        class="w-full"
                    >
                        <template #title>
                            <span>
                                {{ getPlayedAudioClipsLength }} recordings played.
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
        </div>

        <div id="load-more-events-observer-target"></div>

        <!--VAudioClipCard emits selection, which triggers :to, thus teleporting-->
        <!--presence of VAudioClipCard depends on VEventCard-->
        <!--we don't use :disabled because it will still attempt to teleport to :to-->
        <Teleport
            :to="getVPlaybackTeleportId"
        >
            <VPlayback
                v-show="selected_audio_clip !== null"
                :propAudioClip="selected_audio_clip"
                :propIsOpen="true"
                :propAudioVolumePeaks="getSelectedAudioClipAudioVolumePeaks"
                :propBucketQuantity="20"
                :propAutoPlayOnSourceChange="can_autoplay"
                :propPauseTrigger="filter_change_trigger"
            />
        </Teleport>
    </div>
</template>


<script setup lang="ts">
    import EventCard from '@/components/main/EventCard.vue';
    import EventCardSkeleton from '@/components/skeleton/EventCardSkeleton.vue';
    import VPlayback from '@/components/medium/VPlayback.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VAudioClipToneMenu from '@/components/medium/VAudioClipToneMenu.vue';
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
    import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';
    import { useCurrentlyPlayingAudioClipStore } from '@/stores/CurrentlyPlayingAudioClipStore';
    import { useFilteredEventsStore } from '@/stores/FilteredEventsStore';
    import { useCurrentLikesDislikesStore } from '@/stores/CurrentLikesDislikesStore';
    import { isPageAccessedByReload } from '@/helper_functions';
    const axios = require('axios');


    export default defineComponent({
        name: 'BrowseEventsApp',
        data(){
            return {
                currently_playing_audio_clip_store: useCurrentlyPlayingAudioClipStore(),
                filtered_events_store: useFilteredEventsStore(this.propIsUserProfilePage),
                current_likes_dislikes_store: useCurrentLikesDislikesStore(this.propIsUserProfilePage),

                user_profile_username: "",  //only used at profile page

                is_filter_menu_open: false,
                can_filter_menu_teleport: false,

                dynamic_scroller_buffer: 1000, //px, larger means rendered earlier, needed for proper tabbing
                window_resize_timeout: window.setTimeout(()=>{}, 0),

                selected_audio_clip: null as AudioClipsAndLikeDetailsTypes|null,
                filter_change_trigger: false,  //switch between true/false to trigger pause
                can_autoplay: true,

                played_audio_clips_by_id: [] as number[],
                played_audio_clips_quantity_to_pause_scrolling: 10,
                can_pause_scrolling: false,
                scrolling_timeout: window.setTimeout(()=>{}, 0),
                scrolling_checkpoint_px: 0,

                store_scroll_position_timeout: window.setTimeout(()=>{}, 0),
                has_restored_scroll_once: false,

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
            getPlayedAudioClipsLength() : number {

                return this.played_audio_clips_by_id.length;
            },
            canPauseScrolling() : boolean {

                return this.is_fetching === false && this.can_pause_scrolling === true;
            },
            canShowEventsEmptyMessage() : boolean {

                return this.is_fetching === false && this.filtered_events_store.getEventsForBrowsing.length === 0;
            },
            canShowNoNewEventsMessage() : boolean {

                return (
                    this.is_fetching === false &&
                    this.filtered_events_store.getEventsForBrowsing.length > 0 &&
                    this.is_observer_on_cooldown === true
                );
            },
            getVPlaybackTeleportId() : string {

                if(this.selected_audio_clip === null){

                    return '#temporary-teleport-target';
                }

                return '#playback-teleport-audio-clip-id-' + this.selected_audio_clip.id;
            },
            getSelectedAudioClipAudioVolumePeaks() : number[] {

                if(this.selected_audio_clip === null){

                    return [];
                }

                return this.selected_audio_clip.audio_volume_peaks;
            },
        },
        methods: {
            async getEvents(
                current_event_generic_status_name_index:number,
                current_main_filter_index:number,
                current_timeframe_index:number,
                current_audio_clip_role_name_index:number,
                current_audio_clip_tone_id:number,
                is_first_page:boolean,
                next_or_back:"next"|"back"="next",
            ): Promise<void> {

                this.is_fetching = true;

                //initialise to ensure object is ready
                if(is_first_page === true){

                    await this.filtered_events_store.initialiseFilteredEventsStructure(
                        current_event_generic_status_name_index,
                        current_main_filter_index,
                        current_timeframe_index,
                        current_audio_clip_role_name_index,
                        current_audio_clip_tone_id,
                    );
                }

                //for first page, i.e. after filter change, check if we already have data
                const can_skip_fetching = (
                    is_first_page === true &&
                    await this.filtered_events_store.hasExistingDataAfterFilterChange(
                        current_event_generic_status_name_index,
                        current_main_filter_index,
                        current_timeframe_index,
                        current_audio_clip_role_name_index,
                        current_audio_clip_tone_id,
                    ) === true
                );

                if(can_skip_fetching === true){

                    //do nothing else, as template uses getter, which auto-retrieves for us
                    this.is_fetching = false;
                    return;
                }

                //check if can fetch, e.g. if timed out from previous search that yielded no results
                const check_can_fetch = await this.filtered_events_store.checkCanFetch(
                    current_event_generic_status_name_index,
                    current_main_filter_index,
                    current_timeframe_index,
                    current_audio_clip_role_name_index,
                    current_audio_clip_tone_id,
                );

                if(check_can_fetch === false){

                    this.is_fetching = false;
                    return;
                }

                //determine URL
                let full_url = "";

                if(is_first_page === true){

                    //get first time URL
                    full_url = await this.constructFirstPageURL(
                        current_event_generic_status_name_index,
                        current_main_filter_index,
                        current_timeframe_index,
                        current_audio_clip_role_name_index,
                        current_audio_clip_tone_id,
                        next_or_back,
                    );

                }else{

                    const url_key = next_or_back === "next" ? "next_url" : "back_url";

                    full_url = this.filtered_events_store.getFilteredEventsStructure[
                        current_event_generic_status_name_index
                    ][
                        current_main_filter_index
                    ][
                        current_timeframe_index
                    ][
                        current_audio_clip_role_name_index
                    ][
                        current_audio_clip_tone_id
                    ][
                        url_key
                    ];
                }

                await axios.get(full_url)
                .then(async (results: any) => {

                    if(results.data['data'].length === 0){

                        this.is_observer_on_cooldown = true;
                    }

                    await this.filtered_events_store.insertEvents(
                        current_event_generic_status_name_index,
                        current_main_filter_index,
                        current_timeframe_index,
                        current_audio_clip_role_name_index,
                        current_audio_clip_tone_id,
                        next_or_back,
                        results.data['data'],
                        results.data['next_url'],
                        results.data['back_url'],
                    );

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
            async constructFirstPageURL(
                current_event_generic_status_name_index:number,
                current_main_filter_index:number,
                current_timeframe_index:number,
                current_audio_clip_role_name_index:number,
                current_audio_clip_tone_id:number,
                next_or_back:"next"|"back"="next",
            ) : Promise<string> {

                //this is only used for first page
                //API will send us next_url and back_url to directly use after that

                //construct URL
                let full_url = window.location.origin + "/api/events/list";

                //event.generic_status.generic_status_name
                full_url += "/" + this.filtered_events_store.getEventGenericStatusNames[current_event_generic_status_name_index];

                if(this.propIsUserProfilePage === true){

                    full_url += "/user/" + this.user_profile_username;

                }

                //latest/best
                full_url += "/" + this.filtered_events_store.getMainFilters[current_main_filter_index].toLowerCase();

                //timeframe
                full_url += "/" + this.filtered_events_store.getTimeframes[current_timeframe_index].toLowerCase();

                //audio_clip_role.audio_clip_role_name
                full_url += "/" + this.filtered_events_store.getAudioClipRoleNames[current_audio_clip_role_name_index];

                //audio_clip_tone
                if(current_audio_clip_tone_id > 0){

                    full_url += "/" + current_audio_clip_tone_id.toString();
                }

                //next or back
                full_url += "/" + next_or_back;

                return full_url;
            },
            async continueScrolling() : Promise<void> {

                const is_first_page = this.filtered_events_store.getEventsForBrowsing.length === 0;

                this.can_pause_scrolling = false;

                await this.getEvents(
                    this.filtered_events_store.getCurrentEventGenericStatusNameIndex,
                    this.filtered_events_store.getCurrentMainFilterIndex,
                    this.filtered_events_store.getCurrentTimeframeIndex,
                    this.filtered_events_store.getCurrentAudioClipRoleNameIndex,
                    this.filtered_events_store.getCurrentAudioClipToneId,
                    is_first_page,
                    "next",
                );
            },
            toggleFilterMenu() : void {

                this.is_filter_menu_open = !this.is_filter_menu_open;
            },
            switchTriggerOnFilterChange() : void {

                this.filter_change_trigger = !this.filter_change_trigger;
            },
            async handleNewSelectedAudioClip(
                audio_clip:AudioClipsAndLikeDetailsTypes|null,
                can_autoplay:boolean,
            ) : Promise<void> {

                this.can_autoplay = can_autoplay;
                this.selected_audio_clip = audio_clip;

                if(audio_clip === null){

                    return;
                }

                //record how many unique audio_clips have been played
                if(this.played_audio_clips_by_id.includes(audio_clip.id) === false){

                    this.played_audio_clips_by_id.push(audio_clip.id);
                }

                //check whether can stop scrolling
                if(
                    this.can_pause_scrolling === false &&
                    (this.played_audio_clips_by_id.length % this.played_audio_clips_quantity_to_pause_scrolling) === 0
                ){

                    this.can_pause_scrolling = true;
                }
            },
            getInfiniteScrollCallback() : ()=>void {

                return async ()=>{
                    if(
                        this.is_fetching === true ||
                        this.can_pause_scrolling === true ||
                        this.filtered_events_store.getEventsForBrowsing.length === 0
                    ){

                        return;
                    }

                    //prevents first run when DOM is still fresh
                    if(this.must_skip_observer_once === true){

                        this.must_skip_observer_once = false;
                        return;
                    }

                    const can_fetch = await this.filtered_events_store.checkCanFetch(
                        this.filtered_events_store.getCurrentEventGenericStatusNameIndex,
                        this.filtered_events_store.getCurrentMainFilterIndex,
                        this.filtered_events_store.getCurrentTimeframeIndex,
                        this.filtered_events_store.getCurrentAudioClipRoleNameIndex,
                        this.filtered_events_store.getCurrentAudioClipToneId,
                    );

                    if(can_fetch === false){

                        return;
                    }

                    this.is_observer_on_cooldown = false;

                    //on filter change, we already run getEvents()
                    //upon reaching here, that first page fetch is already done
                    this.getEvents(
                        this.filtered_events_store.getCurrentEventGenericStatusNameIndex,
                        this.filtered_events_store.getCurrentMainFilterIndex,
                        this.filtered_events_store.getCurrentTimeframeIndex,
                        this.filtered_events_store.getCurrentAudioClipRoleNameIndex,
                        this.filtered_events_store.getCurrentAudioClipToneId,
                        false,
                        "next",
                    );
                };
            },
            async resetStores() : Promise<void> {

                if(
                    this.propIsUserProfilePage === false &&
                    (localStorage.getItem('reset_home_page_audio_clip_stores') !== null || isPageAccessedByReload() === true)
                ){

                    await this.filtered_events_store.partialResetStore();
                    this.current_likes_dislikes_store.$reset();
                    localStorage.removeItem('reset_home_page_audio_clip_stores');
                }
            },
            async handleWindowResize() : Promise<void> {

                //we do our best to cater to user's viewport height to ensure sufficient buffer size
                //else elements are late to render, causing tab focus and whitespace issues

                this.window_resize_timeout !== null ? clearTimeout(this.window_resize_timeout) : null;

                //run this delayed one next, in case immediate call had fired before dimension is fixed
                this.window_resize_timeout = window.setTimeout(async ()=>{
                    this.dynamic_scroller_buffer = window.innerHeight * 2;
                }, 200);
            },
            async storeScrollY() : Promise<void> {

                window.clearTimeout(this.store_scroll_position_timeout);

                this.store_scroll_position_timeout = window.setTimeout(()=>{

                    this.filtered_events_store.setLastScrollY(window.scrollY);

                }, 250);
            },
            async restoreScrollY() : Promise<void> {

                if(this.has_restored_scroll_once === false){

                    //since stored scrollY is default 0, no need to check
                    window.scroll(0, this.filtered_events_store.getLastScrollY);
                    this.has_restored_scroll_once = true;
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
        },
        beforeMount(){

            //prevents auto-scroll
            //DynamicScroller handles "auto" well, provided that store data is the same
            //however, since store always changes/resets for latest content, "auto" is terrible
            history.scrollRestoration = 'manual';

            //get username
            if(this.propIsUserProfilePage === true){

                const container = (document.getElementById('data-container-get-user-profile') as HTMLElement);

                this.user_profile_username = (container.getAttribute('data-user-profile-username') as string);
            }

            //reset store if scheduled by home button click at NavBar
            this.resetStores();

            //listen from EventCard
            this.currently_playing_audio_clip_store.$subscribe((mutation, state)=>{

                //if playing_audio_clip is identical to selected_audio_clip,
                //it means that this $patch is fired from filter change

                const playing_audio_clip = (state.playing_audio_clip as AudioClipsAndLikeDetailsTypes|null);

                if(
                    playing_audio_clip !== null && this.selected_audio_clip !== null &&
                    playing_audio_clip.id === this.selected_audio_clip.id
                ){

                    return;
                }

                //selected_audio_clip from here is fired when user has just manually selected audio_clip

                this.handleNewSelectedAudioClip(playing_audio_clip, true);

                if(playing_audio_clip !== null){

                    this.filtered_events_store.updateLastSelectedAudioClip(playing_audio_clip);
                }
            });

            //handle things on filter change
            this.filtered_events_store.$onAction(({
                name,
                after,
            })=>{

                if(
                    name === 'updateCurrentEventGenericStatusNameIndex' ||
                    name === 'updateCurrentMainFilterIndex' ||
                    name === 'updateCurrentTimeframeIndex' ||
                    name === 'updateCurrentAudioClipRoleNameIndex' ||
                    name === 'updateCurrentAudioClipTone'
                ){
                    after(()=>{

                        this.switchTriggerOnFilterChange();
                        
                        //last selected audio_clip to be currently selected audio_clip
                        const last_selected_audio_clip = this.filtered_events_store.getLastSelectedAudioClip;
                        this.handleNewSelectedAudioClip(last_selected_audio_clip, false);

                        this.currently_playing_audio_clip_store.$patch({
                            playing_audio_clip: last_selected_audio_clip
                        });

                        this.must_skip_observer_once = true;

                        this.getEvents(
                            this.filtered_events_store.getCurrentEventGenericStatusNameIndex,
                            this.filtered_events_store.getCurrentMainFilterIndex,
                            this.filtered_events_store.getCurrentTimeframeIndex,
                            this.filtered_events_store.getCurrentAudioClipRoleNameIndex,
                            this.filtered_events_store.getCurrentAudioClipToneId,
                            true,
                            "next",
                        );
                    });
                }
            });

            if(this.filtered_events_store.getEventsForBrowsing.length === 0){

                (async ()=>{

                    await this.getEvents(
                        this.filtered_events_store.getCurrentEventGenericStatusNameIndex,
                        this.filtered_events_store.getCurrentMainFilterIndex,
                        this.filtered_events_store.getCurrentTimeframeIndex,
                        this.filtered_events_store.getCurrentAudioClipRoleNameIndex,
                        this.filtered_events_store.getCurrentAudioClipToneId,
                        true,
                        "next",
                    ).finally(()=>{

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
            const observer_target = document.querySelector('#load-more-events-observer-target');

            if(observer_target !== null){

                this.infinite_scroll_observer.observe(observer_target);
            }

            window.addEventListener('resize', this.handleWindowResize);
            window.addEventListener('scroll', this.storeScrollY);
        },
        beforeUnmount(){

            this.infinite_scroll_observer.disconnect();

            window.removeEventListener('resize', this.handleWindowResize);
            window.removeEventListener('scroll', this.storeScrollY);
        },
    });
</script>