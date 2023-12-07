import { defineStore } from 'pinia';


//we want to see what happens 

export const useVPlaybackStore = defineStore('test', {
    state: ()=>({
        last_interacted_vplayback_uuid: "",
        audio_clip_id: [] as number[],   //left to right, oldest to newest
        stopped_at_s: [] as number[],   //left to right, oldest to newest
    }),
    getters: {
        getLastInteractedVPlaybackUUID: (state)=>{

            return state.last_interacted_vplayback_uuid;
        },
    },
    actions: {

    },
    //all things considered, we get overall better usability with persistence than without
    persist: {
        //persist these states
        paths: [
            'audio_clip_id', 'stopped_at_s',
        ],
        debug: true
    },
    share: {
        //array of fields that the plugin will ignore
        omit: [],
        //override global config for this store
        enable: true,
        initialize: false,
    },
});