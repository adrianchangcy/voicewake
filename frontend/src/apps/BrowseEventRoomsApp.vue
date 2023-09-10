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
                <VAction
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
                </VAction>

                <!--arrow-->
                <!--needs mt-4 to stay to prevent snapping-->
                <div class="mt-4 relative">
                    <div
                        v-show="is_sort_menu_open"
                        class="z-10 w-2 h-2 absolute -top-1 left-0 right-0 m-auto bg-theme-light border-l-2 border-t-2 border-theme-black rotate-45"
                    ></div>
                </div>
            </div>

            <div
                v-show="is_sort_menu_open"
            >

                <!--options-->
                <div class="w-full h-fit">

                    <!--use gap-3 because VEventToneMenu.vue has py-1-->
                    <div class="flex flex-col p-4 gap-3 rounded-lg border-2 border-theme-black bg-theme-light/60 backdrop-blur">

                        <!--filter type-->
                        <div class="flex flex-row items-center gap-2">
                            <VActionTextOnly
                                v-for="(filter_type, index) in filter_types" :key="index"
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
            <div
                v-for="event_room in getEventRoomsForBrowsing" :key="event_room.event_room.id"
            >
                <EventRoomCard
                    :prop-show-title="true"
                    :prop-event-room="event_room"
                    :prop-has-border="true"
                    @newSelectedEvent=handleNewSelectedEvent($event)
                />
            </div>
        </TransitionGroupFade>

        <VActionSpecial
            @click="getEventRooms(selected_event_tone, current_filter_type_index, false)"
            prop-element="button"
            type="button"
            prop-element-size="l"
            prop-font-size="l"
            :prop-is-icon-only="false"
            :prop-is-enabled="true"
            class="w-full mt-8"
        >
            <span class="mx-auto">Load more events</span>
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
    import VTitle from '@/components/small/VTitle.vue';
    import VPlayback from '@/components/medium/VPlayback.vue';
    import VBackdropAnime from '@/components/small/VBackdropAnime.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
    import VEventToneMenu from '@/components/medium/VEventToneMenu.vue';
    import VActionSpecial from '@/components/small/VActionSpecial.vue';
    import VActionTextOnly from '@/components/small/VActionTextOnly.vue';
    import VAction from '@/components/small/VAction.vue';
</script>


<script lang="ts">
    import { defineComponent, } from 'vue';
    import { notify } from 'notiwind';
    import GroupedEventsTypes from '@/types/GroupedEvents.interface';
    import EventsAndLikeDetailsTypes from '@/types/EventsAndLikeDetails.interface';
    import EventTonesTypes from '@/types/EventTones.interface';
    import { useCurrentlyPlayingEventStore } from '@/stores/CurrentlyPlayingEventStore';
    const axios = require('axios');

    //these are for pseudo-cache to prevent repeated calls as user switches filters
    interface TrackedEventRoomsType{
        [filter_type_index: number] : {
            event_rooms: GroupedEventsTypes[],
            current_page: number,
        }
    }
    interface EventTonesEventRoomsType{
        [event_tone_id: number]: TrackedEventRoomsType
    }

    export default defineComponent({
        name: 'BrowseEventRoomsApp',
        data(){
            return {
                currently_playing_event_store: useCurrentlyPlayingEventStore(),

                is_sort_menu_open: false,

                current_filter_type_index: 0,
                filter_types: ["Best", "Latest"],

                selected_event_tone: null as EventTonesTypes|null,
                api_page_increment: 1,
                no_event_tone_event_rooms: {} as TrackedEventRoomsType,
                selected_event_tone_event_rooms: {} as EventTonesEventRoomsType,
                fetching_event_rooms_timeout: null as number|null,

                selected_event: null as EventsAndLikeDetailsTypes|null,
                playback_teleport_event_id: '',
            };
        },
        computed: {
            getEventRoomsForBrowsing() : GroupedEventsTypes[] {

                //only have to check first layer key to know whether everything else exists
                //we can do this because of the way we initialise

                if(this.selected_event_tone === null){

                    if(this.current_filter_type_index in this.no_event_tone_event_rooms === false){

                        return [];

                    }else{

                        return this.no_event_tone_event_rooms[this.current_filter_type_index]['event_rooms'];
                    }

                }else{

                    if(this.selected_event_tone.id in this.selected_event_tone_event_rooms === false){

                        return [];

                    }else{

                        return this.selected_event_tone_event_rooms[this.selected_event_tone.id][this.current_filter_type_index]['event_rooms'];
                    }
                }
            }
        },
        methods: {
            openSortMenu() : void {

                this.is_sort_menu_open = !this.is_sort_menu_open;
            },
            updateCurrentFilterTypeIndex(index:number) : void {

                this.current_filter_type_index = index;

                this.fetching_event_rooms_timeout = window.setTimeout(()=>{

                    this.getEventRooms(this.selected_event_tone, this.current_filter_type_index, true);

                }, 500);
            },
            isFilterTypeSelected(index:number) : boolean {

                return this.current_filter_type_index === index;
            },
            storeEventRooms(
                event_tone:EventTonesTypes|null,
                current_filter_type_index:number,
                data:GroupedEventsTypes[]
            ) : void {

                if(event_tone === null){

                    //handle event_rooms retrieved from query with no event_tone specified

                    //add data
                    for(let x=0; x < data.length; x++){

                        this.no_event_tone_event_rooms[current_filter_type_index]['event_rooms'].push(data[x]);
                    }

                    //store page
                    this.no_event_tone_event_rooms[current_filter_type_index]['current_page'] += 1;

                }else{

                    //handle event_rooms retrieved from query with event_tone specified

                    //add data
                    for(let x=0; x < data.length; x++){

                        this.selected_event_tone_event_rooms[event_tone.id][current_filter_type_index]['event_rooms'].push(data[x]);
                    }

                    //store page
                    this.selected_event_tone_event_rooms[event_tone.id][current_filter_type_index]['current_page'] += 1;
                }
            },
            async getEventRooms(
                event_tone:EventTonesTypes|null,
                current_filter_type_index:number,
                is_first_page:boolean
            ): Promise<void> {

                //cannot return on is_fetching===true here
                //else latest event_tones selected does not do the appropriate API call
                //we do it this way to allow non-blocking UX for selecting event_tones

                //initialise dict for first time
                //if first layer key doesn't exist, initialise all the way
                if(is_first_page === true){

                    if(event_tone === null && current_filter_type_index in this.no_event_tone_event_rooms === false){

                        this.no_event_tone_event_rooms[current_filter_type_index] = {
                            'event_rooms': [],
                            'current_page': 0,
                        };

                    }else if(event_tone !== null && event_tone.id in this.selected_event_tone_event_rooms === false){

                        this.selected_event_tone_event_rooms[event_tone.id] = {};

                        for(let x=0; x < this.filter_types.length; x++){

                            this.selected_event_tone_event_rooms[event_tone.id][x] = {
                                'event_rooms': [],
                                'current_page': 0
                            };
                        }
                    }
                }

                //if is first page, check if we already have data
                //simply return, as our computed getEventRoomsForBrowsing handles retrieval for us
                if(
                    is_first_page === true &&
                    (event_tone === null && this.no_event_tone_event_rooms[current_filter_type_index]['event_rooms'].length > 0) ||
                    (event_tone !== null && this.selected_event_tone_event_rooms[event_tone.id][current_filter_type_index]['event_rooms'].length > 0)
                ){

                    return;
                }

                //we initialise current_page here
                //only way, since only here do we know what our event_tone is

                let full_url = window.location.origin + "/api/event-rooms/list/completed/best/all/";

                if(event_tone === null){

                    //initialise current_page if it does not exist
                    if('current_page' in this.no_event_tone_event_rooms[current_filter_type_index] === false){

                        this.no_event_tone_event_rooms[current_filter_type_index]['current_page'] = 0;
                    }

                    //determine URL
                    full_url += (this.no_event_tone_event_rooms[current_filter_type_index]['current_page'] + 1).toString();

                }else{

                    //initialise current_page if it does not exist
                    if('current_page' in this.selected_event_tone_event_rooms[event_tone.id][current_filter_type_index] === false){

                        this.selected_event_tone_event_rooms[event_tone.id][current_filter_type_index]['current_page'] = 0;
                    }

                    //determine URL
                    full_url += event_tone.event_tone_slug + "/";
                    full_url += (
                        this.selected_event_tone_event_rooms[event_tone.id][current_filter_type_index]['current_page'] + 1
                    ).toString();
                }

                await axios.get(full_url)
                .then((results: any) => {

                    this.storeEventRooms(event_tone, current_filter_type_index, results.data['data']);
                })
                .catch((error: any) => {

                    notify({
                        title: "Could not get events",
                        text: error.response.data['message'],
                        type: "error"
                    }, 3000);
                });
            },
            async handleNewSelectedEventTone(event_tone:EventTonesTypes|null) : Promise<void> {

                this.selected_event_tone = event_tone;

                this.fetching_event_rooms_timeout !== null ? window.clearTimeout(this.fetching_event_rooms_timeout) : null;

                this.fetching_event_rooms_timeout = window.setTimeout(()=>{

                    this.getEventRooms(event_tone, this.current_filter_type_index, true);

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

                this.getEventRooms(null, this.current_filter_type_index, true);
            }, 0);

            //listen to store
            this.currently_playing_event_store.$subscribe((mutation, state)=>{

                this.handleNewSelectedEvent(state.playing_event);
            });
        }
    });
</script>