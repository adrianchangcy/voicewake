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
                                v-for="(filter_type, index) in filtered_events_store.getFilterTypes" :key="index"
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
        
                        <!--audio_clip tones-->
                        <VAudioClipToneMenu
                            :prop-is-open="true"
                            :prop-close-when-selected="false"
                            :prop-has-deselect-option="true"
                            :prop-must-track-selected-option="true"
                            :prop-initial-audio-clip-tone="filtered_events_store.getSelectedAudioClipTone"
                            :prop-filtered-grouped-audio-clips-store="filtered_events_store"
                            @audio_clipToneSelected="handleNewSelectedAudioClipTone($event)"
                            class="border rounded-l-lg border-theme-light-gray"
                        />
                    </div>
                </div>
            </div>

            <!--audio_clip roles-->
            <div v-if="propIsUserProfilePage" class="w-full grid grid-cols-2 px-4">
                <VActionTextOnly
                    @click="updateCurrentAudioClipRoleNameIndex(0)"
                    prop-element="button"
                    prop-element-size="s"
                    prop-font-size="s"
                    :prop-is-icon-only="true"
                    :class="[
                        isSelectedAudioClipRoleName(0) ? 'border-b-theme-black' : 'border-b-theme-medium-gray',
                        'col-span-1 border-b-2 rounded-b-none p-2'
                    ]"
                >
                    <span class="mx-auto">
                        <i class="fas fa-comment"></i>
                        <span class="pl-2">Started</span>
                        <span v-show="isSelectedAudioClipRoleName(0)" class="sr-only">selected</span>
                    </span>
                </VActionTextOnly>
                <VActionTextOnly
                    @click="updateCurrentAudioClipRoleNameIndex(1)"
                    prop-element="button"
                    prop-element-size="s"
                    prop-font-size="s"
                    :prop-is-icon-only="true"
                    :class="[
                        isSelectedAudioClipRoleName(1) ? 'border-b-theme-black' : 'border-b-theme-medium-gray',
                        'col-span-1 border-b-2 rounded-b-none p-2'
                    ]"
                >
                    <span class="mx-auto">
                        <i class="fas fa-comments"></i>
                        <span class="pl-2">Replied</span>
                        <span v-show="isSelectedAudioClipRoleName(1)" class="sr-only">selected</span>
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
            v-show="filtered_events_store.getEventsForBrowsing.length > 0"
            :items="filtered_events_store.getEventsForBrowsing"
            :min-item-size="2"
            :buffer="dynamic_scroller_buffer"
            :page-mode="true"
            key-field="event_id"
            class="scroller"
        >

            <template #default="{ item, index, active }">

                <!--events-->
                <DynamicScrollerItem
                    :item="item"
                    :index="index"
                    :active="active"
                >
                    <div class="pb-4">
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
    import AudioClipTonesTypes from '@/types/AudioClipTones.interface';
    import { useCurrentlyPlayingAudioClipStore } from '@/stores/CurrentlyPlayingAudioClipStore';
    import { useFilteredEventsStore } from '@/stores/FilteredEventsStore';
    import { useCurrentLikesDislikesStore } from '@/stores/CurrentLikesDislikesStore';
    import { isPageAccessedByReload } from '@/helper_functions';
    const axios = require('axios');

    //TODO:
        //#1: clear FilteredEventsStore on least recent
            //follow through with CurrentLikesDislikesStore and CurrentlyPlayingAudioClipStore


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
            switchTriggerOnFilterChange() : void {

                this.filter_change_trigger = !this.filter_change_trigger;
            },
            isSelectedAudioClipRoleName(index:number) : boolean {

                return index === this.filtered_events_store.getCurrentAudioClipRoleNameIndex;
            },
            isSelectedFilterType(index:number) : boolean {

                return index === this.filtered_events_store.getCurrentFilterTypeIndex;
            },
            async continueScrolling() : Promise<void> {

                const is_first_page = this.filtered_events_store.getEventsForBrowsing.length === 0;

                this.can_pause_scrolling = false;

                await this.getEvents(
                    this.filtered_events_store.getSelectedAudioClipTone,
                    this.filtered_events_store.getCurrentAudioClipRoleNameIndex,
                    this.filtered_events_store.getCurrentFilterTypeIndex,
                    is_first_page,
                );
            },
            toggleFilterMenu() : void {

                this.is_filter_menu_open = !this.is_filter_menu_open;
            },
            async updateCurrentAudioClipRoleNameIndex(index:number) : Promise<void> {

                await this.filtered_events_store.updateCurrentAudioClipRoleNameIndex(index);

                this.getEvents(
                    this.filtered_events_store.getSelectedAudioClipTone,
                    index,
                    this.filtered_events_store.getCurrentFilterTypeIndex,
                    true,
                );
            },
            async updateCurrentFilterTypeIndex(index:number) : Promise<void> {

                await this.filtered_events_store.updateCurrentFilterTypeIndex(index);
                
                this.getEvents(
                    this.filtered_events_store.getSelectedAudioClipTone,
                    this.filtered_events_store.getCurrentAudioClipRoleNameIndex,
                    index,
                    true,
                );
            },
            async handleNewSelectedAudioClipTone(audio_clip_tone:AudioClipTonesTypes|null) : Promise<void> {

                await this.filtered_events_store.updateSelectedAudioClipTone(audio_clip_tone);

                this.getEvents(
                    audio_clip_tone,
                    this.filtered_events_store.getCurrentAudioClipRoleNameIndex,
                    this.filtered_events_store.getCurrentFilterTypeIndex,
                    true,
                );
            },
            async getEvents(
                audio_clip_tone:AudioClipTonesTypes|null,
                current_audio_clip_role_name_index:number,
                current_filter_type_index:number,
                is_first_page:boolean
            ): Promise<void> {

                this.is_fetching = true;

                //initialise to have all necessary keys available
                //will only do so when no data exists
                if(is_first_page === true){

                    await this.filtered_events_store.initialiseDataOnFirstPageAfterFilterChange(audio_clip_tone);
                }

                //check if we already have data
                if(
                    is_first_page === true &&
                    await this.filtered_events_store.hasDataOnFirstPageAfterFilterChange(
                        audio_clip_tone, current_audio_clip_role_name_index, current_filter_type_index,
                    ) === true
                ){

                    //do nothing else, as template uses getter, which auto-retrieves for us
                    this.is_fetching = false;
                    return;
                }

                const check_can_fetch = await this.filtered_events_store.checkCanFetch(audio_clip_tone, current_audio_clip_role_name_index, current_filter_type_index);

                if(check_can_fetch === false){

                    this.is_fetching = false;
                    return;
                }

                //no existing data, proceed

                const full_url = await this.constructURL(audio_clip_tone, current_audio_clip_role_name_index, current_filter_type_index);

                console.log(full_url);

                await axios.get(full_url)
                .then(async (results: any) => {

                    if(results.data['data'].length === 0){

                        this.is_observer_on_cooldown = true;
                    }

                    await this.filtered_events_store.insertEvents(audio_clip_tone, current_audio_clip_role_name_index, current_filter_type_index, results.data['data']);

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
                audio_clip_tone:AudioClipTonesTypes|null,
                current_audio_clip_role_name_index:number,
                current_filter_type_index:number,
            ) : Promise<string> {

                //construct URL
                let full_url = window.location.origin + "/api/events/list";

                if(this.propIsUserProfilePage === true){

                    full_url += "/user/" + this.user_profile_username;

                }else{

                    full_url += "/completed";
                }

                //latest/best
                full_url += "/" + this.filtered_events_store.getFilterTypes[current_filter_type_index].toLowerCase();

                //timeframe
                full_url += "/all";

                if(this.propIsUserProfilePage === true){

                    full_url += "/" + this.filtered_events_store.getAudioClipRoleNames[current_audio_clip_role_name_index].toLowerCase();
                }

                //audio_clip_tone
                if(audio_clip_tone !== null){

                    full_url += "/" + audio_clip_tone.audio_clip_tone_slug;
                }

                //get next page
                if(audio_clip_tone === null){

                    full_url += "/" + (
                        this.filtered_events_store.getNoAudioClipToneEvents[current_audio_clip_role_name_index][current_filter_type_index]['current_page']
                    ).toString();

                }else{

                    full_url += "/" + (
                        this.filtered_events_store.getSelectedAudioClipToneEvents[audio_clip_tone.id][current_audio_clip_role_name_index][current_filter_type_index]['current_page']
                    ).toString();
                }

                return full_url;
            },
            async handleNewSelectedAudioClip(audio_clip:AudioClipsAndLikeDetailsTypes|null, can_autoplay:boolean) : Promise<void> {

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
                        this.filtered_events_store.getSelectedAudioClipTone,
                        this.filtered_events_store.getCurrentAudioClipRoleNameIndex,
                        this.filtered_events_store.getCurrentFilterTypeIndex,
                    );

                    if(can_fetch === false){

                        return;
                    }

                    this.is_observer_on_cooldown = false;

                    //on filter change, we already run getEvents()
                    //upon reaching here, that first page fetch is already done
                    this.getEvents(
                        this.filtered_events_store.getSelectedAudioClipTone,
                        this.filtered_events_store.getCurrentAudioClipRoleNameIndex,
                        this.filtered_events_store.getCurrentFilterTypeIndex,
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
                    name === 'updateSelectedAudioClipTone' ||
                    name === 'updateCurrentAudioClipRoleNameIndex' ||
                    name === 'updateCurrentFilterTypeIndex'
                ){
                    after(()=>{

                        //last selected audio_clip to be currently selected audio_clip

                        this.switchTriggerOnFilterChange();

                        const last_selected_audio_clip = this.filtered_events_store.getLastSelectedAudioClip;
                        this.handleNewSelectedAudioClip(last_selected_audio_clip, false);

                        this.currently_playing_audio_clip_store.$patch({
                            playing_audio_clip: last_selected_audio_clip
                        });

                        this.must_skip_observer_once = true;
                    });
                }
            });

            if(this.filtered_events_store.getEventsForBrowsing.length === 0){

                (async ()=>{
                    await this.getEvents(
                        this.filtered_events_store.getSelectedAudioClipTone,
                        this.filtered_events_store.getCurrentAudioClipRoleNameIndex,
                        this.filtered_events_store.getCurrentFilterTypeIndex,
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
            const observer_target = document.querySelector('#load-more-events-observer-target');

            if(observer_target !== null){

                this.infinite_scroll_observer.observe(observer_target);
            }

            window.addEventListener('resize', this.handleWindowResize);
        },
        beforeUnmount(){

            this.infinite_scroll_observer.disconnect();

            window.removeEventListener('resize', this.handleWindowResize);
        }
    });
</script>