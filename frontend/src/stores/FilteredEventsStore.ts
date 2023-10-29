import { defineStore } from 'pinia';
import AudioClipTonesTypes from '@/types/AudioClipTones.interface';
import GroupedAudioClipsTypes from '@/types/GroupedAudioClips.interface';
import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';


//need this because RecycleScroller's keyField is not flexible for nested values
interface GroupedAudioClipsWithScrollerIndexTypes extends GroupedAudioClipsTypes{
    event_id: number
}

//stated edge case, Pinia does not rehydrate Date() as Date(), but string
interface NoAudioClipToneEventsType{
    [audio_clip_role_name_index:number] : {
        [filter_type_index: number] : {
            events: GroupedAudioClipsWithScrollerIndexTypes[],
            current_page: number,
            stop_searching: boolean,
            when_stopped_searching: string|null,
            last_selected_audio_clip: AudioClipsAndLikeDetailsTypes|null,
        }
    }
}

interface SelectedAudioClipToneEventsType{
    [audio_clip_tone_id: number]: NoAudioClipToneEventsType
}

export function useFilteredEventsStore(is_user_page:boolean){

    const store_id = is_user_page === true ? 'user_page_filtered_events_store' : 'filtered_events_store';

    return defineStore(store_id, {
        state: ()=>({
            current_audio_clip_role_name_index: 0,
            audio_clip_role_names: ["originator", "responder"],
            current_filter_type_index: 0,
            filter_types: ["Latest", "Best"],

            selected_audio_clip_tone: null as AudioClipTonesTypes|null,
            no_audio_clip_tone_events: {} as NoAudioClipToneEventsType,
            selected_audio_clip_tone_events: {} as SelectedAudioClipToneEventsType,

            stop_searching_duration_s: 10,
            last_scroll_y: 0,
        }),    
        getters: {
            getAudioClipRoleNames: (state) => {

                return state.audio_clip_role_names;
            },
            getNoAudioClipToneEvents: (state) => {

                return state.no_audio_clip_tone_events;
            },
            getSelectedAudioClipToneEvents: (state) => {

                return state.selected_audio_clip_tone_events;
            },
            getCurrentAudioClipRoleNameIndex: (state) => {

                return state.current_audio_clip_role_name_index;
            },
            getCurrentFilterTypeIndex: (state) => {

                return state.current_filter_type_index;
            },
            getFilterTypes: (state) => {

                return state.filter_types;
            },
            getSelectedFilterType: (state) => {

                return state.filter_types[state.current_filter_type_index];
            },
            getSelectedAudioClipTone: (state) => {

                return state.selected_audio_clip_tone;
            },
            getEventsForBrowsing: (state):GroupedAudioClipsTypes[] => {

                //only have to check first layer key to know whether everything else exists
                //we can do this because of the way we initialise

                if(state.selected_audio_clip_tone === null){

                    if(Object.keys(state.no_audio_clip_tone_events).length === 0){

                        return [];

                    }else{

                        return state.no_audio_clip_tone_events[state.current_audio_clip_role_name_index][state.current_filter_type_index]['events'];
                    }

                }else{

                    if(state.selected_audio_clip_tone.id in state.selected_audio_clip_tone_events === false){

                        return [];

                    }else{

                        return state.selected_audio_clip_tone_events[state.selected_audio_clip_tone.id][state.current_audio_clip_role_name_index][state.current_filter_type_index]['events'];
                    }
                }
            },
            getLastSelectedAudioClip: (state):AudioClipsAndLikeDetailsTypes|null => {

                if(state.selected_audio_clip_tone === null){

                    if(Object.keys(state.no_audio_clip_tone_events).length === 0){

                        return null;

                    }else{

                        return state.no_audio_clip_tone_events[state.current_audio_clip_role_name_index][state.current_filter_type_index].last_selected_audio_clip;
                    }

                }else{

                    if(state.selected_audio_clip_tone.id in state.selected_audio_clip_tone_events === false){

                        return null;

                    }else{

                        return state.selected_audio_clip_tone_events[state.selected_audio_clip_tone.id][state.current_audio_clip_role_name_index][state.current_filter_type_index].last_selected_audio_clip;
                    }
                }
            },
            getLastScrollY: (state) => {

                return state.last_scroll_y;
            },
        },
        actions: {
            async setLastScrollY(scrollY_value:number) : Promise<void> {

                this.last_scroll_y = scrollY_value;
            },
            async partialResetStore() : Promise<void> {

                //resetting only these allows us to maintain user's filter preferences
                this.no_audio_clip_tone_events = {};
                this.selected_audio_clip_tone_events = {};
                this.last_scroll_y = 0;
            },
            async destroySelectedAudioClipToneData(new_value:AudioClipTonesTypes) : Promise<void> {

                if(new_value.id in this.selected_audio_clip_tone_events === false){

                    return;
                }

                delete this.selected_audio_clip_tone_events[new_value.id];
            },
            async updateSelectedAudioClipTone(new_value:AudioClipTonesTypes|null) : Promise<void> {

                this.selected_audio_clip_tone = new_value;
            },
            async updateCurrentAudioClipRoleNameIndex(new_value:number) : Promise<void> {

                if(new_value >= this.audio_clip_role_names.length){

                    throw new Error('Invalid current_audio_clip_role_name_index value passed.');
                }

                this.current_audio_clip_role_name_index = new_value;
            },
            async updateCurrentFilterTypeIndex(new_value:number) : Promise<void> {

                if(new_value >= this.filter_types.length){

                    throw new Error('Invalid current_filter_type_index value passed.');
                }

                this.current_filter_type_index = new_value;
            },
            async updateLastSelectedAudioClip(audio_clip:AudioClipsAndLikeDetailsTypes) : Promise<void> {

                if(this.selected_audio_clip_tone === null){

                    this.no_audio_clip_tone_events[this.current_audio_clip_role_name_index][this.current_filter_type_index].last_selected_audio_clip = audio_clip;

                }else{

                    this.selected_audio_clip_tone_events[this.selected_audio_clip_tone.id][this.current_audio_clip_role_name_index][this.current_filter_type_index].last_selected_audio_clip = audio_clip;
                }
            },
            async incrementPage(
                audio_clip_tone:AudioClipTonesTypes|null,
                current_audio_clip_role_name_index:number,
                current_filter_type_index:number,
            ) : Promise<void> {

                //a bit worried about race condition on API request, where we get duplicate same-page data
                //but perhaps this worry is unjustified
                //hence, this is placed back into insertEvents()

                if(audio_clip_tone === null){

                    this.no_audio_clip_tone_events[current_audio_clip_role_name_index][current_filter_type_index]['current_page'] += 1;

                }else{

                    this.selected_audio_clip_tone_events[audio_clip_tone.id][current_audio_clip_role_name_index][current_filter_type_index]['current_page'] += 1;
                }
            },
            async checkCanFetch(
                audio_clip_tone:AudioClipTonesTypes|null,
                current_audio_clip_role_name_index:number,
                current_filter_type_index:number,
            ) : Promise<boolean> {

                //if never stopped searching, return true
                if(
                    audio_clip_tone === null &&
                    this.no_audio_clip_tone_events[current_audio_clip_role_name_index][current_filter_type_index]['stop_searching'] === false
                ){

                    return true;

                }else if(
                    audio_clip_tone !== null &&
                    this.selected_audio_clip_tone_events[audio_clip_tone.id][current_audio_clip_role_name_index][current_filter_type_index]['stop_searching'] === false
                ){

                    return true;
                }

                //has stopped searching before
                //if when_stopped_searching is too in the past, reset and return true
                const datetime_object = new Date();
                let when_stopped_searching_difference_s = 0;

                if(
                    audio_clip_tone === null &&
                    this.no_audio_clip_tone_events[current_audio_clip_role_name_index][current_filter_type_index]['stop_searching'] === true &&
                    this.no_audio_clip_tone_events[current_audio_clip_role_name_index][current_filter_type_index]['when_stopped_searching'] !== null
                ){

                    const datetime_now = new Date(this.no_audio_clip_tone_events[current_audio_clip_role_name_index][current_filter_type_index]['when_stopped_searching']!);

                    when_stopped_searching_difference_s = datetime_object.getTime() - datetime_now.getTime();

                    when_stopped_searching_difference_s = when_stopped_searching_difference_s / 1000;

                    if(when_stopped_searching_difference_s >= this.stop_searching_duration_s){
        
                        this.no_audio_clip_tone_events[current_audio_clip_role_name_index][current_filter_type_index]['stop_searching'] = false;
                        this.no_audio_clip_tone_events[current_audio_clip_role_name_index][current_filter_type_index]['when_stopped_searching'] = null;

                        return true;
                    }

                }else if(
                    audio_clip_tone !== null &&
                    this.selected_audio_clip_tone_events[audio_clip_tone.id][current_audio_clip_role_name_index][current_filter_type_index]['stop_searching'] === true &&
                    this.selected_audio_clip_tone_events[audio_clip_tone.id][current_audio_clip_role_name_index][current_filter_type_index]['when_stopped_searching'] !== null
                ){

                    const datetime_now = new Date(this.selected_audio_clip_tone_events[audio_clip_tone.id][current_audio_clip_role_name_index][current_filter_type_index]['when_stopped_searching']!);

                    when_stopped_searching_difference_s = datetime_object.getTime() - datetime_now.getTime();

                    when_stopped_searching_difference_s = when_stopped_searching_difference_s / 1000;

                    if(when_stopped_searching_difference_s >= this.stop_searching_duration_s){
        
                        this.selected_audio_clip_tone_events[audio_clip_tone.id][current_audio_clip_role_name_index][current_filter_type_index]['stop_searching'] = false;
                        this.selected_audio_clip_tone_events[audio_clip_tone.id][current_audio_clip_role_name_index][current_filter_type_index]['when_stopped_searching'] = null;

                        return true;
                    }
                }

                return false;
            },
            async insertEvents(
                audio_clip_tone:AudioClipTonesTypes|null,
                current_audio_clip_role_name_index:number,
                current_filter_type_index:number,
                data:GroupedAudioClipsTypes[],
            ) : Promise<void> {

                //need to use params to prevent inaccuracy from race condition
                //i.e. data from filter choices previously but new choices were selected

                //stop searching if received no events
                if(data.length === 0){

                    const datetime_now = new Date().toISOString();

                    if(audio_clip_tone === null){

                        this.no_audio_clip_tone_events[current_audio_clip_role_name_index][current_filter_type_index]['stop_searching'] = true;
                        this.no_audio_clip_tone_events[current_audio_clip_role_name_index][current_filter_type_index]['when_stopped_searching'] = datetime_now;

                    }else{

                        this.selected_audio_clip_tone_events[audio_clip_tone.id][current_audio_clip_role_name_index][current_filter_type_index]['stop_searching'] = true;
                        this.selected_audio_clip_tone_events[audio_clip_tone.id][current_audio_clip_role_name_index][current_filter_type_index]['when_stopped_searching'] = datetime_now;
                    }

                    return;
                }

                //handle edge case where data is fetched but audio_clip_tone no longer exists
                //i.e. removed by VAudioClipToneMenu
                if(audio_clip_tone !== null && audio_clip_tone.id in this.selected_audio_clip_tone_events === false){

                    return;
                }

                await this.incrementPage(audio_clip_tone, current_audio_clip_role_name_index, current_filter_type_index);

                //insertion below adds 'event_id' for VirtualScroller's keyField indexing
                //it accepts only literal string, i.e. nested values in objects won't work

                if(audio_clip_tone === null){

                    //handle events retrieved from query with no audio_clip_tone specified

                    //add data
                    for(let x=0; x < data.length; x++){

                        (data[x] as GroupedAudioClipsWithScrollerIndexTypes)['event_id'] = data[x].event.id;

                        this.no_audio_clip_tone_events[current_audio_clip_role_name_index][current_filter_type_index]['events'].push(data[x] as GroupedAudioClipsWithScrollerIndexTypes);
                    }

                }else{

                    //handle events retrieved from query with audio_clip_tone specified

                    //add data
                    for(let x=0; x < data.length; x++){

                        (data[x] as GroupedAudioClipsWithScrollerIndexTypes)['event_id'] = data[x].event.id;

                        this.selected_audio_clip_tone_events[audio_clip_tone.id][current_audio_clip_role_name_index][current_filter_type_index]['events'].push(data[x] as GroupedAudioClipsWithScrollerIndexTypes);
                    }
                }
            },
            async initialiseDataOnFirstPageAfterFilterChange(
                audio_clip_tone:AudioClipTonesTypes|null,
            ) : Promise<void> {

                if(audio_clip_tone === null && Object.keys(this.no_audio_clip_tone_events).length === 0){

                    for(let x=0; x < this.audio_clip_role_names.length; x++){

                        this.no_audio_clip_tone_events[x] = {};

                        for(let xx=0; xx < this.filter_types.length; xx++){

                            this.no_audio_clip_tone_events[x][xx] = {
                                'events': [],
                                'current_page': 1,
                                'stop_searching': false,
                                'when_stopped_searching': null,
                                'last_selected_audio_clip': null,
                            };
                        }
                    }

                }else if(audio_clip_tone !== null && audio_clip_tone.id in this.selected_audio_clip_tone_events === false){

                    this.selected_audio_clip_tone_events[audio_clip_tone.id] = {};

                    for(let x=0; x < this.audio_clip_role_names.length; x++){

                        this.selected_audio_clip_tone_events[audio_clip_tone.id][x] = {};

                        for(let xx=0; xx < this.filter_types.length; xx++){

                            this.selected_audio_clip_tone_events[audio_clip_tone.id][x][xx] = {
                                'events': [],
                                'current_page': 1,
                                'stop_searching': false,
                                'when_stopped_searching': null,
                                'last_selected_audio_clip': null,
                            };
                        }
                    }
                }
            },
            async hasDataOnFirstPageAfterFilterChange(
                audio_clip_tone:AudioClipTonesTypes|null,
                current_audio_clip_role_name_index:number,
                current_filter_type_index:number,
            ) : Promise<boolean> {

                //if is first page, check if we already have data
                //simply return, as our computed getEventsForBrowsing handles retrieval for us
                return (
                    (audio_clip_tone === null && this.no_audio_clip_tone_events[current_audio_clip_role_name_index][current_filter_type_index]['events'].length > 0) ||
                    (audio_clip_tone !== null && this.selected_audio_clip_tone_events[audio_clip_tone.id][current_audio_clip_role_name_index][current_filter_type_index]['events'].length > 0)
                );
            },
        },
        persist: !is_user_page,
    })();
}