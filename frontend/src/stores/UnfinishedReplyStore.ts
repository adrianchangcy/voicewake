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
        async updateStatus(status:StatusValues) : Promise<void> {

            this.status = status;
        },
        async updateUnfinishedReply(event_room:GroupedEventsTypes) : Promise<void> {

            this.event_room = event_room;
        },
        async removeUnfinishedReply() : Promise<void> {

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