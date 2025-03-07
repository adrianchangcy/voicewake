<template>
    <div>

        <!--user profile-->
        <!--px-1 to match scroller-->
        <VUserCard
            v-if="isUserProfilePage || isUserLikesDislikesPage"
            :prop-page-context="propPageContext"
            :prop-has-default-actions="isUserProfilePage"
            class="py-8 px-1"
        >
            <span v-if="isUserLikesDislikesPage">Likes &#38; Dislikes</span>
        </VUserCard>

        <!--sorting options-->
        <!--px-1 to match scroller-->
        <div
            ref="sorting_options_container"
            :class="[
                isUserProfilePage || isUserLikesDislikesPage ? 'pb-8' : 'pb-10',
                'flex flex-col px-1'
            ]"
        >

            <!--filter-->
            <div class="flex flex-col gap-2">

                <!--likes/dislikes-->
                <div
                    v-if="isUserLikesDislikesPage"
                    class="w-full flex flex-row items-center border-2 rounded-lg border-theme-gray-form-field dark:border-dark-theme-gray-form-field shade-border-when-hover transition-colors"
                >
                    <VActionText
                        v-for="(filter_type, index) in filtered_events_store.getLikeDislikeChoices"
                        :key="index"
                        @click="filtered_events_store.updateCurrentLikeDislikeChoiceIndex(index)"
                        :disabled="filtered_events_store.isSameCurrentLikeDislikeChoiceIndex(index)"
                        prop-element="button"
                        prop-element-size="s"
                        prop-font-size="s"
                        :prop-is-icon-only="true"
                        class="w-full relative focus-visible:-outline-offset-2"
                    >
                        <span class="w-fit mx-auto">{{ filter_type }}</span>
                        <span
                            v-show="filtered_events_store.isSameCurrentLikeDislikeChoiceIndex(index)"
                            class="sr-only"
                        >
                            selected
                        </span>
                        <TransitionFade>
                            <div
                                v-show="filtered_events_store.isSameCurrentLikeDislikeChoiceIndex(index)"
                                class="absolute h-0.5 bg-theme-black dark:bg-dark-theme-white-2 left-2 right-2 bottom-0"
                            ></div>
                        </TransitionFade>
                    </VActionText>
                </div>

                <div class="grid grid-cols-4 gap-2">
                    <!--audio_clip_roles-->
                    <div class="col-span-3 flex flex-row items-center border-2 rounded-lg border-theme-gray-form-field dark:border-dark-theme-gray-2 shade-border-when-hover transition-colors">
                        <VActionText
                            v-for="(pretty_audio_clip_role_name, index) in filtered_events_store.getPrettyAudioClipRoleNames"
                            :key="index"
                            @click="filtered_events_store.updateCurrentAudioClipRoleNameIndex(index)"
                            prop-element="button"
                            prop-element-size="s"
                            prop-font-size="s"
                            :prop-is-icon-only="true"
                            class="w-full relative focus-visible:-outline-offset-2"
                        >
                            <span class="w-fit mx-auto">{{ pretty_audio_clip_role_name }}</span>
                            <span
                                v-show="filtered_events_store.isSameCurrentAudioClipRoleNameIndex(index)"
                                class="sr-only"
                            >
                                selected
                            </span>
                            <TransitionFade>
                                <div
                                    v-show="filtered_events_store.isSameCurrentAudioClipRoleNameIndex(index)"
                                    class="absolute h-0.5 bg-theme-black dark:bg-dark-theme-white-2 left-2 right-2 bottom-0"
                                ></div>
                            </TransitionFade>
                        </VActionText>
                    </div>

                    <!--audio_clip_tones-->
                    <div
                        ref="open_close_audio_clip_tone_menu_button"
                        :class="[
                            is_audio_clip_tone_menu_open ? 'border-theme-black dark:border-dark-theme-white-2' : 'border-theme-gray-form-field dark:border-dark-theme-gray-form-field shade-border-when-hover',
                            'col-span-1 flex flex-row items-center border-2 rounded-lg transition-colors'
                        ]"
                    >
                        <VActionText
                            @click="toggleFilterMenu()"
                            prop-element="button"
                            prop-element-size="s"
                            prop-font-size="s"
                            :prop-is-icon-only="true"
                            class="w-full focus-visible:-outline-offset-2"
                        >
                            <span
                                v-if="filtered_events_store.getCurrentAudioClipTone === null"
                                class="mx-auto"
                            >
                                Any
                            </span>
                            <span
                                v-else
                                class="mx-auto text-2xl has-emoji"
                            >
                                <span class="sr-only">{{ filtered_events_store.getCurrentAudioClipTone.audio_clip_tone_name }}</span>
                                {{ filtered_events_store.getCurrentAudioClipTone.audio_clip_tone_symbol }}
                            </span>
                        </VActionText>
                    </div>
                </div>
            </div>

            <!--audio_clip_tone menu-->
            <div class="h-0 relative">

                <!--arrow-->
                <div class="w-full grid grid-cols-4">
                    <div class="col-start-4 col-span-1 relative">
                        <div
                            v-show="is_audio_clip_tone_menu_open"
                            class="z-30 w-2 h-2 absolute top-3 left-0 right-0 m-auto bg-theme-light dark:bg-theme-dark border-l-2 border-t-2 border-theme-black dark:border-dark-theme-white-2 rotate-45"
                        ></div>
                    </div>
                </div>

                <!--menu-->
                <div
                    v-show="is_audio_clip_tone_menu_open"
                    v-click-outside="{
                        bool_status_variable_or_callback: 'is_audio_clip_tone_menu_open',
                        refs_to_exclude: ['open_close_audio_clip_tone_menu_button']
                    }"
                    class="absolute w-full h-fit top-4 z-20 flex flex-col p-4 gap-4 rounded-lg border-2 border-theme-black dark:border-dark-theme-white-2 bg-theme-light dark:bg-theme-dark"
                >

                    <!--audio_clip_tones-->
                    <VAudioClipToneMenu
                        :prop-is-open="true"
                        :prop-close-when-selected="false"
                        :prop-has-deselect-option="true"
                        :prop-must-track-selected-option="true"
                        :prop-initial-audio-clip-tone="filtered_events_store.getCurrentAudioClipTone"
                        :prop-filtered-grouped-audio-clips-store="filtered_events_store"
                        @audioClipToneSelected="filtered_events_store.updateCurrentAudioClipTone($event)"
                    />
                </div>
            </div>
        </div>

        <div>
            <!--must specify a unique attribute as unique key for the scroller via "key-field"-->
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
                        <div class="px-1 pb-6">
                            <VEventCard
                                :prop-guaranteed-event-generic-status="isHomePage ? 'completed' : ''"
                                :prop-show-title="true"
                                :prop-event="item"
                                :prop-has-border="true"
                                :prop-load-v-audio-clip-cards-only="true"
                                :prop-has-virtual-scroll="true"
                                @new-is-liked="filtered_events_store.newAudioClipIsLiked($event)"
                                @new-v-playback-teleport-id="handleNewVPlaybackTeleportId($event)"
                            />
                        </div>
                    </DynamicScrollerItem>
                </template>
            </DynamicScroller>
        </div>

        <!--loading and dialogs-->
        <!--px-1 to match scroller-->
        <div class="px-1">

            <TransitionGroupFade>

                <!--fetching-->
                <VEventCardSkeleton
                    v-show="filtered_events_store.isFetching"
                    :prop-has-border="true"
                    :prop-audio-clip-quantity="2"
                    class="w-full"
                />

                <!--no events at all-->
                <VDialogPlain
                    v-show="canShowEventsEmptyMessage"
                    :prop-has-border="false"
                    :prop-has-auto-space-logo="false"
                    :prop-has-auto-space-title="false"
                    :prop-has-auto-space-content="false"
                    class="w-full"
                >
                    <template #logo>
                        <FontAwesomeIcon icon="far fa-face-meh-blank"/>
                    </template>
                    <template #title>
                        <span>No events found.</span>
                    </template>
                    <template #content>
                        <span>The filters can be changed to explore other content!</span>
                    </template>
                </VDialogPlain>

                <!--no events left to load-->
                <VDialogPlain
                    v-show="canShowNoNewEventsMessage"
                    :prop-has-border="false"
                    :prop-has-auto-space-logo="false"
                    :prop-has-auto-space-title="false"
                    :prop-has-auto-space-content="false"
                    class="w-full pt-8"
                >
                    <template #logo>
                        <FontAwesomeIcon icon="far fa-face-meh-blank"/>
                    </template>
                    <template #title>
                        <span>You've reached the end.</span>
                    </template>
                    <template #content>
                        <span>The filters can be changed to explore other content!</span>
                    </template>
                </VDialogPlain>

                <!--reconsider loading more events-->
                <VDialogPlain
                    v-show="canPauseScrolling"
                    :prop-has-border="true"
                    :prop-has-auto-space-logo="false"
                    :prop-has-auto-space-title="true"
                    :prop-has-auto-space-content="true"
                    class="w-full pt-8"
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
                                <span class="mx-auto">Load more events</span>
                            </VActionSpecial>
                        </div>
                    </template>
                </VDialogPlain>

                <!--retry-->
                <VDialogPlain
                    v-show="canShowManualFetchRetry"
                    :prop-has-border="true"
                    :prop-has-auto-space-logo="false"
                    :prop-has-auto-space-title="true"
                    :prop-has-auto-space-content="true"
                    class="w-full pt-8"
                >
                    <template #title>
                        <span>
                            Unable to load events.
                        </span>
                    </template>
                    <template #content>
                        <div class="flex flex-col gap-4">
                            <span>
                                An error had occurred.
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

        <div id="load-more-events-observer-target"></div>

        <Teleport
            v-if="teleport_id !== ''"
            :to="teleport_id"
        >
            <VPlayback
                :prop-audio-clip="vplayback_store.getPlayingAudioClip"
                :prop-is-open="canOpenVPlayback"
                :prop-audio-volume-peaks="getSelectedAudioClipAudioVolumePeaks"
                :prop-bucket-quantity="20"
            />
        </Teleport>
    </div>
</template>


<script setup lang="ts">
    import VEventCard from '../components/main/VEventCard.vue';
    import VEventCardSkeleton from '../components/skeleton/VEventCardSkeleton.vue';
    import VPlayback from '../components/medium/VPlayback.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
    import VAudioClipToneMenu from '../components/medium/VAudioClipToneMenu.vue';
    import VActionSpecial from '../components/small/VActionSpecial.vue';
    import VActionText from '../components/small/VActionText.vue';
    import VDialogPlain from '../components/small/VDialogPlain.vue';
    import VUserCard from '../components/medium/VUserCard.vue';
    import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faFaceMehBlank } from '@fortawesome/free-regular-svg-icons/faFaceMehBlank';
    import { faChevronDown } from '@fortawesome/free-solid-svg-icons/faChevronDown';

    library.add(faFaceMehBlank, faChevronDown);
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';
    import AudioClipsTypes from '@/types/AudioClips.interface';
    import { useVPlaybackStore } from '@/stores/VPlaybackStore';
    import { useFilteredEventsStore } from '@/stores/FilteredEventsStore';
    import { isPageAccessedByBackForward } from '@/helper_functions';
    import axios from 'axios';


    export default defineComponent({
        name: 'BrowseEventsApp',
        data(){
            return {
                vplayback_store: useVPlaybackStore(),
                filtered_events_store: useFilteredEventsStore(this.propPageContext),

                //data-container
                username: "",
                is_own_page: false,
                is_blocked: false,

                is_audio_clip_tone_menu_open: false,
                can_audio_clip_tone_menu_teleport: false,

                dynamic_scroller_buffer: 1000, //px, larger means rendered earlier, needed for proper tabbing
                window_resize_timeout: window.setTimeout(()=>{}, 0),

                played_audio_clips_by_id: [] as number[],
                played_audio_clips_quantity_to_pause_scrolling: 40,
                can_pause_scrolling: false,
                scrolling_timeout: window.setTimeout(()=>{}, 0),
                scrolling_checkpoint_px: 0,

                store_scroll_position_timeout: window.setTimeout(()=>{}, 0),
                has_restored_scroll_once: false,

                infinite_scroll_observer: new IntersectionObserver(this.getInfiniteScrollCallback(), {threshold: 1}),
                can_observer_fetch: false,
                is_error_on_previous_fetch: false,

                teleport_id: '',
            };
        },
        props: {
            propPageContext: {
                type: String as PropType<"home"|"user_profile"|"user_likes_dislikes">,
                default: "home"
            },
        },
        computed: {
            isHomePage() : boolean {

                return this.propPageContext === 'home';
            },
            isUserProfilePage() : boolean {

                return this.propPageContext === 'user_profile';
            },
            isUserLikesDislikesPage() : boolean {

                return this.propPageContext === 'user_likes_dislikes';
            },
            getPlayedAudioClipsLength() : number {

                return this.played_audio_clips_by_id.length;
            },
            canPauseScrolling() : boolean {

                return (
                    this.filtered_events_store.isFetching === false &&
                    this.can_pause_scrolling === true &&
                    this.filtered_events_store.canStopFetching === false
                );
            },
            canShowEventsEmptyMessage() : boolean {

                return (
                    this.filtered_events_store.getEventsForBrowsing.length === 0 &&
                    this.filtered_events_store.isFetching === false &&
                    this.filtered_events_store.canStopFetching === true &&
                    this.is_error_on_previous_fetch === false
                );
            },
            canShowNoNewEventsMessage() : boolean {

                return (
                    this.filtered_events_store.getEventsForBrowsing.length > 0 &&
                    this.filtered_events_store.isFetching === false &&
                    this.filtered_events_store.canStopFetching === true &&
                    this.is_error_on_previous_fetch === false
                );
            },
            canShowManualFetchRetry() : boolean {
                return (
                    this.filtered_events_store.getEventsForBrowsing.length > 0 &&
                    this.filtered_events_store.isFetching === false &&
                    this.filtered_events_store.canStopFetching === false &&
                    this.is_error_on_previous_fetch === true
                );
            },
            getSelectedAudioClipAudioVolumePeaks() : number[] {

                if(this.vplayback_store.getPlayingAudioClip === null){

                    return [];
                }

                return this.vplayback_store.getPlayingAudioClip.audio_volume_peaks;
            },
            canOpenVPlayback() : boolean {

                return this.filtered_events_store.getLastSelectedAudioClip !== null;
            },
        },
        methods: {
            async getEvents(
                current_like_dislike_choice_index:number,
                current_event_generic_status_name_index:number,
                current_main_filter_index:number,
                current_timeframe_index:number,
                current_audio_clip_role_name_index:number,
                current_audio_clip_tone_id:number,
                is_first_page:boolean,
                next_or_back:"next"|"back"="next",
            ): Promise<void> {

                //initialise to ensure object is ready
                if(is_first_page === true){

                    this.filtered_events_store.initialiseFilteredEventsStructure(
                        current_like_dislike_choice_index,
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
                    this.filtered_events_store.hasExistingDataAfterFilterChange(
                        current_like_dislike_choice_index,
                        current_event_generic_status_name_index,
                        current_main_filter_index,
                        current_timeframe_index,
                        current_audio_clip_role_name_index,
                        current_audio_clip_tone_id,
                    ) === true
                );

                if(can_skip_fetching === true){

                    //do nothing else, as template uses getter, which auto-retrieves for us
                    return;
                }

                //check if can fetch, e.g. if timed out from previous search that yielded no results
                const check_can_fetch = this.filtered_events_store.checkCanFetch(
                    current_like_dislike_choice_index,
                    current_event_generic_status_name_index,
                    current_main_filter_index,
                    current_timeframe_index,
                    current_audio_clip_role_name_index,
                    current_audio_clip_tone_id,
                );

                if(check_can_fetch === false){

                    return;
                }

                //get base URL
                //for first page, it is "/next" or "/back"
                //for subsequent pages, it is "/next/tokenhere" or "/back/tokenhere"
                //request will return next_token and back_token, so just append it to base_url
                const base_url = this.constructBaseURL(
                    current_like_dislike_choice_index,
                    current_event_generic_status_name_index,
                    current_main_filter_index,
                    current_timeframe_index,
                    current_audio_clip_role_name_index,
                    current_audio_clip_tone_id,
                );

                //determine URL
                let target_url = "";

                if(is_first_page === true){

                    //construct target URL if first page

                    target_url = base_url + "/" + next_or_back;

                }else{

                    //get target URL from store if not first page, as it has been constructed and saved by previous request

                    const url_key = next_or_back === "next" ? "next_url" : "back_url";

                    target_url = this.filtered_events_store.getFilteredEventsStructure[
                        current_like_dislike_choice_index
                    ][
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

                //is fetching
                this.filtered_events_store.updateIsFetching(
                    true,
                    current_like_dislike_choice_index,
                    current_event_generic_status_name_index,
                    current_main_filter_index,
                    current_timeframe_index,
                    current_audio_clip_role_name_index,
                    current_audio_clip_tone_id,
                );

                await axios.get(target_url)
                .then((result:any)=>{

                    if(
                        Object.hasOwn(result.data, 'next_token') === false ||
                        Object.hasOwn(result.data, 'back_token') === false
                    ){

                        throw new Error('Expected API keys were not found.');
                    }

                    let next_url = base_url + "/" + "next";
                    let back_url = base_url + "/" + "back";

                    if(result.data['next_token'] !== "" && result.data['back_token'] !== ""){

                        next_url += "/" + result.data['next_token'];
                        back_url += "/" + result.data['back_token'];
                    }

                    this.filtered_events_store.insertEvents(
                        current_like_dislike_choice_index,
                        current_event_generic_status_name_index,
                        current_main_filter_index,
                        current_timeframe_index,
                        current_audio_clip_role_name_index,
                        current_audio_clip_tone_id,
                        next_or_back,
                        result.data['data'],
                        next_url,
                        back_url,
                    );

                    //put this after insertEvents(), for potential are_all_rows_fetched=true
                    this.is_error_on_previous_fetch = false;

                }).catch(async()=>{

                    this.is_error_on_previous_fetch = true;

                    //no need to notify

                }).finally(()=>{

                    //no longer fetching
                    this.filtered_events_store.updateIsFetching(
                        false,
                        current_like_dislike_choice_index,
                        current_event_generic_status_name_index,
                        current_main_filter_index,
                        current_timeframe_index,
                        current_audio_clip_role_name_index,
                        current_audio_clip_tone_id,
                    );
                });
            },
            constructBaseURL(
                current_like_dislike_choice_index:number,
                current_event_generic_status_name_index:number,
                current_main_filter_index:number,
                current_timeframe_index:number,
                current_audio_clip_role_name_index:number,
                current_audio_clip_tone_id:number,
            ) : string {

                //add "/next/tokenhere" or "/back/tokenhere" after calling this function
                //API will send us next_token and back_token to directly use after that

                //start of URL
                let full_url = window.location.origin + "/api/events/list";

                if(this.isUserProfilePage === true){

                    //signature URL
                    full_url += "/user" + "/" + this.username;

                }else if(this.isUserLikesDislikesPage === true){

                    //signature URL
                    full_url += "/user-likes-dislikes" + "/" + this.username;

                    //likes/dislikes
                    full_url += "/" + this.filtered_events_store.like_dislike_choices[current_like_dislike_choice_index].toLowerCase();

                }else if(this.isHomePage === true){

                    //no signature URL

                    //event.generic_status.generic_status_name
                    if(this.filtered_events_store.getEventGenericStatusNames[current_event_generic_status_name_index] !== null){

                        full_url += "/" + this.filtered_events_store.getEventGenericStatusNames[current_event_generic_status_name_index]!.toLowerCase();
                    }
                }

                //latest/best
                full_url += "/" + this.filtered_events_store.getMainFilters[current_main_filter_index].toLowerCase();

                //timeframe
                full_url += "/" + this.filtered_events_store.getTimeframes[current_timeframe_index].toLowerCase();

                //audio_clip_role.audio_clip_role_name
                full_url += "/" + this.filtered_events_store.getAudioClipRoleNames[current_audio_clip_role_name_index];

                //audio_clip_tone
                if(current_audio_clip_tone_id > this.filtered_events_store.default_audio_clip_tone_id_when_null){

                    full_url += "/" + current_audio_clip_tone_id.toString();
                }

                return full_url;
            },
            async continueScrolling() : Promise<void> {

                const is_first_page = this.filtered_events_store.getEventsForBrowsing.length === 0;

                this.can_pause_scrolling = false;

                await this.getEvents(
                    this.filtered_events_store.getCurrentLikeDislikeChoiceIndex,
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

                this.is_audio_clip_tone_menu_open = !this.is_audio_clip_tone_menu_open;
            },
            async handleNewSelectedAudioClip(audio_clip:AudioClipsTypes|AudioClipsAndLikeDetailsTypes|null) : Promise<void> {

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

                return ()=>{
                    if(
                        this.filtered_events_store.isFetching === true ||
                        this.can_observer_fetch === false ||
                        this.can_pause_scrolling === true ||
                        this.is_error_on_previous_fetch === true ||
                        this.filtered_events_store.getEventsForBrowsing.length === 0
                    ){

                        return;
                    }

                    const can_fetch = this.filtered_events_store.checkCanFetch(
                        this.filtered_events_store.getCurrentLikeDislikeChoiceIndex,
                        this.filtered_events_store.getCurrentEventGenericStatusNameIndex,
                        this.filtered_events_store.getCurrentMainFilterIndex,
                        this.filtered_events_store.getCurrentTimeframeIndex,
                        this.filtered_events_store.getCurrentAudioClipRoleNameIndex,
                        this.filtered_events_store.getCurrentAudioClipToneId,
                    );

                    if(can_fetch === false){

                        return;
                    }

                    //on filter change, we already run getEvents()
                    //upon reaching here, that first page fetch is already done
                    this.getEvents(
                        this.filtered_events_store.getCurrentLikeDislikeChoiceIndex,
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
                    this.isHomePage === true &&
                    isPageAccessedByBackForward() === false
                ){

                    await this.filtered_events_store.partialResetStore();
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
            async canShowFilterOptionBelowVNavBar() : Promise<void> {

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

                        this.can_audio_clip_tone_menu_teleport = true;

                    }else{

                        this.can_audio_clip_tone_menu_teleport = false;
                    }

                    //set checkpoint for next comparison
                    this.scrolling_checkpoint_px = window.scrollY;

                }, 250);
            },
            handleNewVPlaybackTeleportId(teleport_id:string) : void {

                this.teleport_id = teleport_id;
            },
            handleNewUsername(new_value:string) : void {

                this.username = new_value;
            },

        },
        beforeMount(){

            //prevents auto-scroll
            //DynamicScroller handles "auto" well, provided that store data is the same
            //however, since store always changes/resets for latest content, "auto" is terrible
            history.scrollRestoration = 'manual';

            //reset store if not navigated from back/forward
            this.resetStores();

            //we have to get username here, cannot wait for VUserCard
            if(this.propPageContext === 'user_profile'){

                const container = (document.getElementById('data-container-get-user-profile') as HTMLElement);
                this.username = (container.getAttribute('data-username') as string);

            }else if(this.propPageContext === 'user_likes_dislikes'){

                const container = (document.getElementById('data-container-list-user-likes-dislikes') as HTMLElement);
                this.username = (container.getAttribute('data-username') as string);
            }

            //sync vplayback_store if filtered_events_store has persisted
            if(this.filtered_events_store.getLastSelectedAudioClip !== null){

                this.vplayback_store.updatePlayingAudioClip(
                    this.filtered_events_store.getLastSelectedAudioClip
                );
            }

            //listen from VEventCardAlwaysCompleted
            this.vplayback_store.$onAction(({
                name,
                after,
            })=>{

                after(()=>{

                    //decide on autoplay

                    if(name === 'updatePlayingAudioClip'){

                        //if playing_audio_clip is identical to selected_audio_clip,
                        //it means that this $patch is fired from filter change
                        if(
                            this.filtered_events_store.getLastSelectedAudioClip !== null &&
                            this.vplayback_store.getPlayingAudioClip !== null &&
                            this.filtered_events_store.getLastSelectedAudioClip.id === this.vplayback_store.getPlayingAudioClip.id
                        ){

                            //don't autoplay on filter change
                            this.vplayback_store.autoplayOnChange(false);
                            this.handleNewSelectedAudioClip(this.vplayback_store.getPlayingAudioClip);

                        }else{

                            //not from filter change, can autoplay
                            this.vplayback_store.autoplayOnChange(true);
                            this.handleNewSelectedAudioClip(this.vplayback_store.getPlayingAudioClip);

                            this.filtered_events_store.updateLastSelectedAudioClip(
                                this.vplayback_store.getPlayingAudioClip
                            );
                        }
                    }
                });

            });

            //handle things on filter change
            this.filtered_events_store.$onAction(({
                name,
                after,
            })=>{

                if(
                    name === 'updateCurrentLikeDislikeChoiceIndex' ||
                    name === 'updateCurrentEventGenericStatusNameIndex' ||
                    name === 'updateCurrentMainFilterIndex' ||
                    name === 'updateCurrentTimeframeIndex' ||
                    name === 'updateCurrentAudioClipRoleNameIndex' ||
                    name === 'updateCurrentAudioClipTone'
                ){

                    after(async ()=>{

                        this.can_observer_fetch = false;

                        //always pause on filter change
                        this.vplayback_store.triggerPause();

                        //restore last played audio clip from filter, if any
                        if(this.filtered_events_store.getLastSelectedAudioClip !== null){

                            this.vplayback_store.updatePlayingAudioClip(
                                this.filtered_events_store.getLastSelectedAudioClip
                            );
                        }

                        //get events on first page of filter change, if no events exist
                        await this.getEvents(
                            this.filtered_events_store.getCurrentLikeDislikeChoiceIndex,
                            this.filtered_events_store.getCurrentEventGenericStatusNameIndex,
                            this.filtered_events_store.getCurrentMainFilterIndex,
                            this.filtered_events_store.getCurrentTimeframeIndex,
                            this.filtered_events_store.getCurrentAudioClipRoleNameIndex,
                            this.filtered_events_store.getCurrentAudioClipToneId,
                            true,
                            "next",
                        ).finally(()=>{

                            this.can_observer_fetch = true;
                        });
                    });
                }
            });

            if(this.filtered_events_store.getEventsForBrowsing.length === 0){

                (async ()=>{
                    await this.getEvents(
                        this.filtered_events_store.getCurrentLikeDislikeChoiceIndex,
                        this.filtered_events_store.getCurrentEventGenericStatusNameIndex,
                        this.filtered_events_store.getCurrentMainFilterIndex,
                        this.filtered_events_store.getCurrentTimeframeIndex,
                        this.filtered_events_store.getCurrentAudioClipRoleNameIndex,
                        this.filtered_events_store.getCurrentAudioClipToneId,
                        true,
                        "next",
                    ).finally(()=>{
                        this.can_observer_fetch = true;
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