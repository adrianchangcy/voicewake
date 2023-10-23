import { defineStore } from 'pinia';
import GroupedAudioClipsTypes from '@/types/GroupedAudioClips.interface';
import StatusValues from '@/types/values/StatusValues';


export const useUnfinishedReplyStore = defineStore('unfinished_reply', {
    state: ()=>({
        event: null as GroupedAudioClipsTypes|null,
        status: "" as StatusValues,
    }),    
    getters: {
        getUnfinishedReply: (state)=>{

            return state.event;
        },
        getStatus: (state)=>{

            return state.status;
        },
    },
    actions: {
        async updateStatus(status:StatusValues) : Promise<void> {

            this.status = status;
        },
        async updateUnfinishedReply(event:GroupedAudioClipsTypes) : Promise<void> {

            this.event = event;
        },
        async removeUnfinishedReply() : Promise<void> {

            this.event = null;
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