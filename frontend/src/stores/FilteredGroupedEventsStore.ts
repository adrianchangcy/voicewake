import { defineStore } from 'pinia';
import EventTonesTypes from '@/types/EventTones.interface';
import GroupedEventsTypes from '@/types/GroupedEvents.interface';


//this store is essentially a pseudo-cache to prevent repeated calls as user switches filters
//need this whole thing abstracted as this store
//due to complex indexing, and necessity to update nested values
interface NoEventToneEventRoomsType{
    [filter_type_index: number] : {
        event_rooms: GroupedEventsTypes[],
        current_page: number,
    }
}
interface SelectedEventToneEventRoomsType{
    [event_tone_id: number]: NoEventToneEventRoomsType
}


export const useFilteredGroupedEventsStore = defineStore('filtered_grouped_events_store', {
    state: ()=>({
        current_filter_type_index: 0,
        filter_types: ["Best", "Latest"],

        selected_event_tone: null as EventTonesTypes|null,
        no_event_tone_event_rooms: {} as NoEventToneEventRoomsType,
        selected_event_tone_event_rooms: {} as SelectedEventToneEventRoomsType,
    }),    
    getters: {
        getNoEventToneEventRooms: (state) => {

            return state.no_event_tone_event_rooms;
        },
        getSelectedEventToneEventRooms: (state) => {

            return state.selected_event_tone_event_rooms;
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

                if(state.current_filter_type_index in state.no_event_tone_event_rooms === false){

                    return [];

                }else{

                    return state.no_event_tone_event_rooms[state.current_filter_type_index]['event_rooms'];
                }

            }else{

                if(state.selected_event_tone.id in state.selected_event_tone_event_rooms === false){

                    return [];

                }else{

                    return state.selected_event_tone_event_rooms[state.selected_event_tone.id][state.current_filter_type_index]['event_rooms'];
                }
            }
        },
    },
    actions: {
        updateSelectedEventTone(new_value:EventTonesTypes|null) : void {

            this.selected_event_tone = new_value;
        },
        updateCurrentFilterTypeIndex(new_value:number) : void {

            if(new_value >= this.filter_types.length){

                throw new Error('Invalid current_filter_type_index value passed.');
            }

            this.current_filter_type_index = new_value;
        },
        insertEventRooms(event_tone:EventTonesTypes|null, current_filter_type_index:number, data:GroupedEventsTypes[]) : void {

            //need to use params to prevent inaccuracy from race condition
            //i.e. data from filter choices previously but new choices were selected

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
        initialiseDataOnFirstPageAfterFilterChange(
            event_tone:EventTonesTypes|null,
            current_filter_type_index:number,
        ) : void {

            //initialise dict for first time
            //if first layer key doesn't exist, initialise all the way

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
        },
        hasDataOnFirstPageAfterFilterChange(
            event_tone:EventTonesTypes|null,
            current_filter_type_index:number,
        ) : boolean {

            //if is first page, check if we already have data
            //simply return, as our computed getEventRoomsForBrowsing handles retrieval for us
            return (
                (event_tone === null && this.no_event_tone_event_rooms[current_filter_type_index]['event_rooms'].length > 0) ||
                (event_tone !== null && this.selected_event_tone_event_rooms[event_tone.id][current_filter_type_index]['event_rooms'].length > 0)
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