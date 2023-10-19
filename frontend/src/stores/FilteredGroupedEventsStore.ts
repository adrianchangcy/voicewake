import { defineStore } from 'pinia';
import EventTonesTypes from '@/types/EventTones.interface';
import GroupedEventsTypes from '@/types/GroupedEvents.interface';
import EventsAndLikeDetailsTypes from '@/types/EventsAndLikeDetails.interface';


//need this because RecycleScroller's keyField is not flexible for nested values
interface GroupedEventsAndScrollerIndexTypes extends GroupedEventsTypes{
    event_room_id: number
}

interface NoEventToneEventRoomsType{
    [event_role_name_index:number] : {
        [filter_type_index: number] : {
            event_rooms: GroupedEventsAndScrollerIndexTypes[],
            current_page: number,
            stop_searching: boolean,
            when_stopped_searching: Date|null,
            last_selected_event: EventsAndLikeDetailsTypes|null,
        }
    }
}

interface SelectedEventToneEventRoomsType{
    [event_tone_id: number]: NoEventToneEventRoomsType
}


export const useFilteredGroupedEventsStore = defineStore('filtered_grouped_events_store', {
    state: ()=>({
        current_event_role_name_index: 0,
        event_role_names: ["originator", "responder"],
        current_filter_type_index: 0,
        filter_types: ["Latest", "Best"],

        selected_event_tone: null as EventTonesTypes|null,
        no_event_tone_event_rooms: {} as NoEventToneEventRoomsType,
        selected_event_tone_event_rooms: {} as SelectedEventToneEventRoomsType,

        stop_searching_duration_s: 120,
    }),    
    getters: {
        getEventRoleNames: (state) => {

            return state.event_role_names;
        },
        getNoEventToneEventRooms: (state) => {

            return state.no_event_tone_event_rooms;
        },
        getSelectedEventToneEventRooms: (state) => {

            return state.selected_event_tone_event_rooms;
        },
        getCurrentEventRoleNameIndex: (state) => {

            return state.current_event_role_name_index;
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
        getSelectedEventTone: (state) => {

            return state.selected_event_tone;
        },
        getEventRoomsForBrowsing: (state):GroupedEventsTypes[] => {

            //only have to check first layer key to know whether everything else exists
            //we can do this because of the way we initialise

            if(state.selected_event_tone === null){

                if(Object.keys(state.no_event_tone_event_rooms).length === 0){

                    return [];

                }else{

                    return state.no_event_tone_event_rooms[state.current_event_role_name_index][state.current_filter_type_index]['event_rooms'];
                }

            }else{

                if(state.selected_event_tone.id in state.selected_event_tone_event_rooms === false){

                    return [];

                }else{

                    return state.selected_event_tone_event_rooms[state.selected_event_tone.id][state.current_event_role_name_index][state.current_filter_type_index]['event_rooms'];
                }
            }
        },
        getLastSelectedEvent: (state):EventsAndLikeDetailsTypes|null => {

            if(state.selected_event_tone === null){

                if(Object.keys(state.no_event_tone_event_rooms).length === 0){

                    return null;

                }else{

                    return state.no_event_tone_event_rooms[state.current_event_role_name_index][state.current_filter_type_index].last_selected_event;
                }

            }else{

                if(state.selected_event_tone.id in state.selected_event_tone_event_rooms === false){

                    return null;

                }else{

                    return state.selected_event_tone_event_rooms[state.selected_event_tone.id][state.current_event_role_name_index][state.current_filter_type_index].last_selected_event;
                }
            }
        },
    },
    actions: {
        updateSelectedEventTone(new_value:EventTonesTypes|null) : void {

            this.selected_event_tone = new_value;
        },
        updateCurrentEventRoleNameIndex(new_value:number) : void {

            if(new_value >= this.event_role_names.length){

                throw new Error('Invalid current_event_role_name_index value passed.');
            }

            this.current_event_role_name_index = new_value;
        },
        updateCurrentFilterTypeIndex(new_value:number) : void {

            if(new_value >= this.filter_types.length){

                throw new Error('Invalid current_filter_type_index value passed.');
            }

            this.current_filter_type_index = new_value;
        },
        updateLastSelectedEvent(event:EventsAndLikeDetailsTypes) : void {

            if(this.selected_event_tone === null){

                this.no_event_tone_event_rooms[this.current_event_role_name_index][this.current_filter_type_index].last_selected_event = event;

            }else{

                this.selected_event_tone_event_rooms[this.selected_event_tone.id][this.current_event_role_name_index][this.current_filter_type_index].last_selected_event = event;
            }
        },
        incrementPage(
            event_tone:EventTonesTypes|null,
            current_event_role_name_index:number,
            current_filter_type_index:number,
        ) : void {

            //a bit worried about race condition on API request, where we get duplicate same-page data
            //but perhaps this worry is unjustified
            //hence, this is placed back into insertEventRooms()

            if(event_tone === null){

                this.no_event_tone_event_rooms[current_event_role_name_index][current_filter_type_index]['current_page'] += 1;

            }else{

                this.selected_event_tone_event_rooms[event_tone.id][current_event_role_name_index][current_filter_type_index]['current_page'] += 1;
            }
        },
        checkCanFetch(
            event_tone:EventTonesTypes|null,
            current_event_role_name_index:number,
            current_filter_type_index:number,
        ) : boolean {

            //if never stopped searching, return true
            if(
                event_tone === null &&
                this.no_event_tone_event_rooms[current_event_role_name_index][current_filter_type_index]['stop_searching'] === false
            ){

                return true;

            }else if(
                event_tone !== null &&
                this.selected_event_tone_event_rooms[event_tone.id][current_event_role_name_index][current_filter_type_index]['stop_searching'] === false
            ){

                return true;
            }

            //has stopped searching before
            //if when_stopped_searching is too in the past, reset and return true
            const datetime_now = new Date();
            let when_stopped_searching_difference_s = 0;

            if(
                event_tone === null &&
                this.no_event_tone_event_rooms[current_event_role_name_index][current_filter_type_index]['stop_searching'] === true &&
                this.no_event_tone_event_rooms[current_event_role_name_index][current_filter_type_index]['when_stopped_searching'] !== null
            ){

                when_stopped_searching_difference_s = datetime_now.getTime() - this.no_event_tone_event_rooms[current_event_role_name_index][current_filter_type_index]['when_stopped_searching']!.getTime();

                when_stopped_searching_difference_s = when_stopped_searching_difference_s / 1000;

                if(when_stopped_searching_difference_s >= this.stop_searching_duration_s){
    
                    this.no_event_tone_event_rooms[current_event_role_name_index][current_filter_type_index]['stop_searching'] = false;
                    this.no_event_tone_event_rooms[current_event_role_name_index][current_filter_type_index]['when_stopped_searching'] = null;

                    return true;
                }

            }else if(
                event_tone !== null &&
                this.selected_event_tone_event_rooms[event_tone.id][current_event_role_name_index][current_filter_type_index]['stop_searching'] === true &&
                this.selected_event_tone_event_rooms[event_tone.id][current_event_role_name_index][current_filter_type_index]['when_stopped_searching'] !== null
            ){

                when_stopped_searching_difference_s = datetime_now.getTime() - this.selected_event_tone_event_rooms[event_tone.id][current_event_role_name_index][current_filter_type_index]['when_stopped_searching']!.getTime();

                when_stopped_searching_difference_s = when_stopped_searching_difference_s / 1000;

                if(when_stopped_searching_difference_s >= this.stop_searching_duration_s){
    
                    this.selected_event_tone_event_rooms[event_tone.id][current_event_role_name_index][current_filter_type_index]['stop_searching'] = false;
                    this.selected_event_tone_event_rooms[event_tone.id][current_event_role_name_index][current_filter_type_index]['when_stopped_searching'] = null;

                    return true;
                }
            }

            return false;
        },
        insertEventRooms(
            event_tone:EventTonesTypes|null,
            current_event_role_name_index:number,
            current_filter_type_index:number,
            data:GroupedEventsTypes[],
        ) : void {

            //need to use params to prevent inaccuracy from race condition
            //i.e. data from filter choices previously but new choices were selected

            //stop searching if received no event_rooms
            if(data.length === 0){

                const datetime_now = new Date();

                if(event_tone === null){

                    this.no_event_tone_event_rooms[current_event_role_name_index][current_filter_type_index]['stop_searching'] = true;
                    this.no_event_tone_event_rooms[current_event_role_name_index][current_filter_type_index]['when_stopped_searching'] = datetime_now;

                }else{

                    this.selected_event_tone_event_rooms[event_tone.id][current_event_role_name_index][current_filter_type_index]['stop_searching'] = true;
                    this.selected_event_tone_event_rooms[event_tone.id][current_event_role_name_index][current_filter_type_index]['when_stopped_searching'] = datetime_now;
                }

                return;
            }

            this.incrementPage(event_tone, current_event_role_name_index, current_filter_type_index);

            //insertion below adds 'event_room_id' for VirtualScroller's keyField indexing
            //it accepts only literal string, i.e. nested values in objects won't work

            if(event_tone === null){

                //handle event_rooms retrieved from query with no event_tone specified

                //add data
                for(let x=0; x < data.length; x++){

                    (data[x] as GroupedEventsAndScrollerIndexTypes)['event_room_id'] = data[x].event_room.id;

                    this.no_event_tone_event_rooms[current_event_role_name_index][current_filter_type_index]['event_rooms'].push(data[x] as GroupedEventsAndScrollerIndexTypes);
                }

            }else{

                //handle event_rooms retrieved from query with event_tone specified

                //add data
                for(let x=0; x < data.length; x++){

                    (data[x] as GroupedEventsAndScrollerIndexTypes)['event_room_id'] = data[x].event_room.id;

                    this.selected_event_tone_event_rooms[event_tone.id][current_event_role_name_index][current_filter_type_index]['event_rooms'].push(data[x] as GroupedEventsAndScrollerIndexTypes);
                }
            }
        },
        initialiseDataOnFirstPageAfterFilterChange(
            event_tone:EventTonesTypes|null,
        ) : void {

            if(event_tone === null && Object.keys(this.no_event_tone_event_rooms).length === 0){

                for(let x=0; x < this.event_role_names.length; x++){

                    this.no_event_tone_event_rooms[x] = {};

                    for(let xx=0; xx < this.filter_types.length; xx++){

                        this.no_event_tone_event_rooms[x][xx] = {
                            'event_rooms': [],
                            'current_page': 1,
                            'stop_searching': false,
                            'when_stopped_searching': null,
                            'last_selected_event': null,
                        };
                    }
                }

            }else if(event_tone !== null && event_tone.id in this.selected_event_tone_event_rooms === false){

                this.selected_event_tone_event_rooms[event_tone.id] = {};

                for(let x=0; x < this.event_role_names.length; x++){

                    this.selected_event_tone_event_rooms[event_tone.id][x] = {};

                    for(let xx=0; xx < this.filter_types.length; xx++){

                        this.selected_event_tone_event_rooms[event_tone.id][x][xx] = {
                            'event_rooms': [],
                            'current_page': 1,
                            'stop_searching': false,
                            'when_stopped_searching': null,
                            'last_selected_event': null,
                        };
                    }
                }
            }
        },
        hasDataOnFirstPageAfterFilterChange(
            event_tone:EventTonesTypes|null,
            current_event_role_name_index:number,
            current_filter_type_index:number,
        ) : boolean {

            //if is first page, check if we already have data
            //simply return, as our computed getEventRoomsForBrowsing handles retrieval for us
            return (
                (event_tone === null && this.no_event_tone_event_rooms[current_event_role_name_index][current_filter_type_index]['event_rooms'].length > 0) ||
                (event_tone !== null && this.selected_event_tone_event_rooms[event_tone.id][current_event_role_name_index][current_filter_type_index]['event_rooms'].length > 0)
            );
        },
    },
    persist: false,
    share: {
        //array of fields that the plugin will ignore
        omit: [],
        //override global config for this store
        enable: false,
        initialize: false,
    },
});