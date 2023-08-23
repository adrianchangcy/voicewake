import { defineStore } from 'pinia';
import GroupedEventsTypes from '@/types/GroupedEvents.interface';
import StatusValues from '@/types/values/StatusValues';


export const useUnfinishedReplyStore = defineStore('unfinished_reply', {
    state: ()=>({
        event_room: null as GroupedEventsTypes|null,
        status: "" as StatusValues,
    }),    
    getters: {
        getUnfinishedReply: (state)=>{

            return state.event_room;
        },
        getStatus: (state)=>{

            return state.status;
        },
    },
    actions: {
        updateStatus(status:StatusValues) : void {

            this.status = status;
        },
        updateUnfinishedReply(event_room:GroupedEventsTypes) : void {

            this.event_room = event_room;
        },
        removeUnfinishedReply() : void {

            this.event_room = null;
        },
    },
    persist: true,
    share: {
        //array of fields that the plugin will ignore
        omit: [],
        //override global config for this store
        enable: true,
        initialize: false,
    },
});