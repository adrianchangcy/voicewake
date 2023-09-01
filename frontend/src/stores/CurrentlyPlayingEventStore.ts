import { defineStore } from 'pinia';
import EventsAndLikeDetailsTypes from '@/types/EventsAndLikeDetails.interface';

export const useCurrentlyPlayingEventStore = defineStore('currently_playing_event', {
    state: ()=>({
        playing_event: null as EventsAndLikeDetailsTypes|null,
    }),    
    getters: {
        getEventId: (state)=>{

            return state.playing_event;
        },
    },
    actions: {
        updateEventId(playing_event:EventsAndLikeDetailsTypes): void {

            this.playing_event = playing_event;
        }
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