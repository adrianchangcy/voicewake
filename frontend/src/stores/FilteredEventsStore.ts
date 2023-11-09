import { defineStore } from 'pinia';
import AudioClipTonesTypes from '@/types/AudioClipTones.interface';
import EventsAndAudioClipsTypes from '@/types/EventsAndAudioClips.interface';
import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';


//reminder, Pinia does not rehydrate Date() as Date(), but string

interface DefaultPageTypes {
    events: EventsAndAudioClipsTypes[],
    stop_searching: boolean,
    when_stopped_searching: string|null,
    last_selected_audio_clip: AudioClipsAndLikeDetailsTypes|null,
    next_url: string,
    back_url: string,
}

interface FilteredEventsStructure {
    [current_event_generic_status_name_index:number]: {
        [current_main_filter_index:number]: {
            [current_timeframe_index:number]: {
                [current_audio_clip_role_name_index:number]: {
                    [audio_clip_tone_id:number]: DefaultPageTypes
                }
            }
        }
    }
}


export function useFilteredEventsStore(is_user_page:boolean){

    const store_id = is_user_page === true ? 'user_page_filtered_events_store' : 'filtered_events_store';

    return defineStore(store_id, {
        state: ()=>({
            filtered_events_structure: {} as FilteredEventsStructure,

            current_event_generic_status_name_index: 0,
            event_generic_status_names: ["completed"],

            current_main_filter_index: 0,
            // main_filters: ["Latest", "Best"],
            main_filters: ["Latest"],

            current_timeframe_index: 0,
            // timeframes: ["All", "Year", "Month", "Day"],
            timeframes: ["All"],

            current_audio_clip_role_name_index: 0,
            audio_clip_role_names: ["originator", "responder"],
            pretty_audio_clip_role_names: ["Started", "Replied"],

            //when null, i.e. "any", our index is 0, which is fine, since audio_clip_tones.id in db starts from 1
            current_audio_clip_tone_id: 0,
            current_audio_clip_tone: null as AudioClipTonesTypes|null,

            stop_searching_duration_s: 10,
            last_scroll_y: 0,
        }),
        getters: {
            getFilteredEventsStructure: (state):FilteredEventsStructure => {

                return state.filtered_events_structure;
            },
            getEventsForBrowsing: (state):EventsAndAudioClipsTypes[] => {

                const args_list = [
                    state.current_event_generic_status_name_index,
                    state.current_main_filter_index,
                    state.current_timeframe_index,
                    state.current_audio_clip_role_name_index,
                    state.current_audio_clip_tone_id,
                ];

                //tried checking using the proper way, i.e. manual 'if' checks going deeper and deeper
                //that seemed to ruin reactivity
                //beware that this solution here may hide errors
                try{

                    return state.filtered_events_structure[args_list[0]][args_list[1]][args_list[2]][args_list[3]][args_list[4]].events;

                }catch(error){

                    return [];
                }
            },
            getLastSelectedAudioClip: (state):AudioClipsAndLikeDetailsTypes|null => {

                try{

                    return state.filtered_events_structure[state.current_event_generic_status_name_index][state.current_main_filter_index][state.current_timeframe_index][state.current_audio_clip_role_name_index][state.current_audio_clip_tone_id].last_selected_audio_clip;

                }catch(error){

                    return null;
                }
            },
            getLastScrollY: (state):number => {

                return state.last_scroll_y;
            },
            getCurrentEventGenericStatusNameIndex: (state):number => {

                return state.current_event_generic_status_name_index;
            },
            getEventGenericStatusNames: (state):string[] => {

                return state.event_generic_status_names;
            },
            getCurrentMainFilterIndex: (state):number => {

                return state.current_main_filter_index;
            },
            getMainFilters: (state):string[] => {

                return state.main_filters;
            },
            getCurrentTimeframeIndex: (state):number => {

                return state.current_timeframe_index;
            },
            getTimeframes: (state):string[] => {

                return state.timeframes;
            },
            getCurrentAudioClipRoleNameIndex: (state):number => {

                return state.current_audio_clip_role_name_index;
            },
            getAudioClipRoleNames: (state):string[] => {

                return state.audio_clip_role_names;
            },
            getPrettyAudioClipRoleNames: (state):string[] => {

                return state.pretty_audio_clip_role_names;
            },
            getCurrentAudioClipToneId: (state):number => {

                return state.current_audio_clip_tone_id;
            },
            getCurrentAudioClipTone: (state):AudioClipTonesTypes|null => {

                return state.current_audio_clip_tone;
            },
        },
        actions: {
            async updateCurrentEventGenericStatusNameIndex(new_index:number) : Promise<void> {

                if(new_index >= this.event_generic_status_names.length){

                    throw new Error('Index out of range.');
                }

                this.current_event_generic_status_name_index = new_index;
            },
            isSameCurrentEventGenericStatusNameIndex(index:number) : boolean {

                return this.current_event_generic_status_name_index === index;
            },
            async updateCurrentMainFilterIndex(new_index:number) : Promise<void> {

                if(new_index >= this.main_filters.length){

                    throw new Error('Index out of range.');
                }

                this.current_main_filter_index = new_index;
            },
            isSameCurrentMainFilterIndex(index:number) : boolean {

                return this.current_main_filter_index === index;
            },
            async updateCurrentTimeframeIndex(new_index:number) : Promise<void> {

                if(new_index >= this.timeframes.length){

                    throw new Error('Index out of range.');
                }

                this.current_timeframe_index = new_index;
            },
            isSameCurrentTimeframeIndex(index:number) : boolean {

                return this.current_timeframe_index === index;
            },
            async updateCurrentAudioClipRoleNameIndex(new_index:number) : Promise<void> {

                if(new_index >= this.audio_clip_role_names.length){

                    throw new Error('Index out of range.');
                }

                this.current_audio_clip_role_name_index = new_index;
            },
            isSameCurrentAudioClipRoleNameIndex(index:number) : boolean {

                return this.current_audio_clip_role_name_index === index;
            },
            async updateCurrentAudioClipTone(audio_clip_tone:AudioClipTonesTypes|null) : Promise<void> {

                this.current_audio_clip_tone = audio_clip_tone;
                this.current_audio_clip_tone_id = audio_clip_tone === null ? 0 : audio_clip_tone.id;
            },
            isSameCurrentAudioClipTone(audio_clip_tone:AudioClipTonesTypes|null) : boolean {

                if(audio_clip_tone === null){

                    return this.current_audio_clip_tone_id === 0;

                }else{

                    return this.current_audio_clip_tone_id === audio_clip_tone.id;
                }
            },
            async updateLastSelectedAudioClip(audio_clip:AudioClipsAndLikeDetailsTypes) : Promise<void> {

                this.filtered_events_structure[
                    this.current_event_generic_status_name_index
                ][
                    this.current_main_filter_index
                ][
                    this.current_timeframe_index
                ][
                    this.current_audio_clip_role_name_index
                ][
                    this.current_audio_clip_tone_id
                ][
                    'last_selected_audio_clip'
                ] = audio_clip;
            },
            async checkCanFetch(
                current_event_generic_status_name_index:number,
                current_main_filter_index:number,
                current_timeframe_index:number,
                current_audio_clip_role_name_index:number,
                current_audio_clip_tone_id:number,
            ) : Promise<boolean> {

                const args_list = [
                    current_event_generic_status_name_index,
                    current_main_filter_index,
                    current_timeframe_index,
                    current_audio_clip_role_name_index,
                    current_audio_clip_tone_id,
                ];

                await this.initialiseFilteredEventsStructure(
                    current_event_generic_status_name_index,
                    current_main_filter_index,
                    current_timeframe_index,
                    current_audio_clip_role_name_index,
                    current_audio_clip_tone_id,
                );

                const target_level = this.filtered_events_structure[args_list[0]][args_list[1]][args_list[2]][args_list[3]][args_list[4]];

                if(target_level.stop_searching === false){

                    //can search
                    return true;
                }

                //has stopped searching before
                //if when_stopped_searching is too far in the past, reset and return true

                const datetime_object = new Date();
                let when_stopped_searching_difference_s = 0;

                const datetime_now = new Date(target_level.when_stopped_searching!);

                when_stopped_searching_difference_s = datetime_object.getTime() - datetime_now.getTime();

                when_stopped_searching_difference_s = when_stopped_searching_difference_s / 1000;

                if(when_stopped_searching_difference_s >= this.stop_searching_duration_s){

                    //time has passed, can search
                    this.filtered_events_structure[args_list[0]][args_list[1]][args_list[2]][args_list[3]][args_list[4]]['stop_searching'] = false;
                    this.filtered_events_structure[args_list[0]][args_list[1]][args_list[2]][args_list[3]][args_list[4]]['when_stopped_searching'] = null;

                    return true;
                }

                //time has not yet passed
                return false;
            },
            async insertEvents(
                current_event_generic_status_name_index:number,
                current_main_filter_index:number,
                current_timeframe_index:number,
                current_audio_clip_role_name_index:number,
                current_audio_clip_tone_id:number,
                next_or_back:"next"|"back"="next",
                new_events:EventsAndAudioClipsTypes[]=[],
                next_url:string='',
                back_url:string='',
            ) : Promise<void> {

                //need to use params to prevent inaccuracy from race condition
                //i.e. data from filter choices previously but new choices were selected

                //stop searching if received no events
                if(new_events.length === 0){

                    const datetime_now = new Date().toISOString();

                    //update "stop_searching", "when_stopped_searching"
                    this.filtered_events_structure[current_event_generic_status_name_index][current_main_filter_index][current_timeframe_index][current_audio_clip_role_name_index][current_audio_clip_tone_id]['stop_searching'] = true;
                    this.filtered_events_structure[current_event_generic_status_name_index][current_main_filter_index][current_timeframe_index][current_audio_clip_role_name_index][current_audio_clip_tone_id]['when_stopped_searching'] = datetime_now;

                    return;
                }

                //add extra needed data for all events and audio_clips

                for(let x = 0; x < new_events.length; x++){

                    //add "event_id_as_scroller_index" to every event for Vue Virtual Scroller, then store

                    new_events[x].event_id_as_scroller_index = new_events[x].event.id;

                    //add previous_is_liked_by_user, useful for revert on API failure

                    if(new_events[x].originator !== null){

                        new_events[x].originator!.previous_is_liked_by_user = null;
                    }

                    for(let xx = 0; xx < new_events[x].responder.length; xx++){

                        new_events[x].responder[xx].previous_is_liked_by_user = null;
                    }
                }

                if(next_or_back === "next"){

                    new_events.forEach((event:EventsAndAudioClipsTypes)=>{

                        this.filtered_events_structure[current_event_generic_status_name_index][current_main_filter_index][current_timeframe_index][current_audio_clip_role_name_index][current_audio_clip_tone_id]['events'].push(event);
                    });
                
                }else if(next_or_back === "back"){

                    //backwards
                    for(let x = (new_events.length - 1); x >= 0; x--){

                        this.filtered_events_structure[current_event_generic_status_name_index][current_main_filter_index][current_timeframe_index][current_audio_clip_role_name_index][current_audio_clip_tone_id]['events'].splice(0, 0, new_events[x]);
                    }
                }

                //update URLs

                if(next_url !== ''){

                    this.filtered_events_structure[current_event_generic_status_name_index][current_main_filter_index][current_timeframe_index][current_audio_clip_role_name_index][current_audio_clip_tone_id]['next_url'] = next_url;
                }

                if(back_url !== ''){

                    this.filtered_events_structure[current_event_generic_status_name_index][current_main_filter_index][current_timeframe_index][current_audio_clip_role_name_index][current_audio_clip_tone_id]['back_url'] = back_url;
                }
            },
            async initialiseFilteredEventsStructure(
                current_event_generic_status_name_index:number,
                current_main_filter_index:number,
                current_timeframe_index:number,
                current_audio_clip_role_name_index:number,
                current_audio_clip_tone_id:number,
            ) : Promise<void> {

                //on-demand initialisation
                //does nothing if there is already our desired structure

                const args_list = [
                    current_event_generic_status_name_index,
                    current_main_filter_index,
                    current_timeframe_index,
                    current_audio_clip_role_name_index,
                    current_audio_clip_tone_id,
                ];

                //start initialising
                Object.hasOwn(this.filtered_events_structure, args_list[0]) === false ? this.filtered_events_structure[args_list[0]] = {} : null;
                Object.hasOwn(this.filtered_events_structure[args_list[0]], args_list[1]) === false ? this.filtered_events_structure[args_list[0]][args_list[1]] = {} : null;
                Object.hasOwn(this.filtered_events_structure[args_list[0]][args_list[1]], args_list[2]) === false ? this.filtered_events_structure[args_list[0]][args_list[1]][args_list[2]] = {} : null;
                Object.hasOwn(this.filtered_events_structure[args_list[0]][args_list[1]][args_list[2]], args_list[3]) === false ? this.filtered_events_structure[args_list[0]][args_list[1]][args_list[2]][args_list[3]] = {} : null;

                //final initialisation
                if(Object.hasOwn(this.filtered_events_structure[args_list[0]][args_list[1]][args_list[2]][args_list[3]], args_list[4]) === false){

                    this.filtered_events_structure[args_list[0]][args_list[1]][args_list[2]][args_list[3]][args_list[4]] = {
                        'events': [],
                        'stop_searching': false,
                        'when_stopped_searching': null,
                        'last_selected_audio_clip': null,
                        'next_url': '',
                        'back_url': '',
                    };
                }
            },
            async hasExistingDataAfterFilterChange(
                current_event_generic_status_name_index:number,
                current_main_filter_index:number,
                current_timeframe_index:number,
                current_audio_clip_role_name_index:number,
                current_audio_clip_tone_id:number,
            ) : Promise<boolean> {

                const args_list = [
                    current_event_generic_status_name_index,
                    current_main_filter_index,
                    current_timeframe_index,
                    current_audio_clip_role_name_index,
                    current_audio_clip_tone_id,
                ];

                return this.filtered_events_structure[args_list[0]][args_list[1]][args_list[2]][args_list[3]][args_list[4]]['events'].length > 0;
            },
            async partialResetStore() : Promise<void> {

                this.filtered_events_structure = {};
                this.last_scroll_y = 0;
            },
            async setLastScrollY(scrollY_value:number) : Promise<void> {

                this.last_scroll_y = scrollY_value;
            },
            async newAudioClipIsLiked(
                new_value:{audio_clip:AudioClipsAndLikeDetailsTypes, new_is_liked:boolean|null}
            ) : Promise<void> {

                //since objects are passed by reference, just pass the audio_clip here

                //only call this on API success, instead of following user's spam clicks
                //because on failure, this will be the source of truth, while server is the ultimate source
                //if you'd like to ensure 100% accuracy, maybe a log-and-retry-request at storage can do

                switch(new_value.new_is_liked){

                    case true:
            
                        if(new_value.audio_clip.is_liked_by_user === false){
            
                            new_value.audio_clip.dislike_count -= 1;
                        }
            
                        if(new_value.audio_clip.is_liked_by_user !== true){
            
                            new_value.audio_clip.like_count += 1;
                        }
            
                        break;
            
                    case null:
            
                        switch(new_value.audio_clip.is_liked_by_user){
                            case true:
                                new_value.audio_clip.like_count -= 1;
                                break;
                            case false:
                                new_value.audio_clip.dislike_count -= 1;
                                break;
                            default:
                                break;
                        }
            
                        break;
            
                    case false:
            
                        if(new_value.audio_clip.is_liked_by_user === true){
            
                            new_value.audio_clip.like_count -= 1;
                        }
            
                        if(new_value.audio_clip.is_liked_by_user !== false){
            
                            new_value.audio_clip.dislike_count += 1;
                        }
            
                        break;
            
                    default:
            
                        break;
                }
            
                new_value.audio_clip.previous_is_liked_by_user = new_value.audio_clip.is_liked_by_user;
                new_value.audio_clip.is_liked_by_user = new_value.new_is_liked;
            },
        },
        persist: !is_user_page,
    })();
}