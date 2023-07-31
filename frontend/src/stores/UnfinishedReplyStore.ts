import { defineStore } from 'pinia';
import EventRoomTypes from '@/types/EventRooms.interface';
import Statuses from '@/types/values/Statuses';
import { watch } from 'vue';


export const useUnfinishedReplyStore = defineStore('unfinished_reply', {
    state: ()=>({
        event_room: null as EventRoomTypes|null,
        status: "" as Statuses,
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
        updateStatus(status:Statuses) : void {

            this.status = status;
        },
        updateUnfinishedReply(event_room:EventRoomTypes) : void {

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