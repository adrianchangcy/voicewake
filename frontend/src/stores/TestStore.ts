import { defineStore } from 'pinia';
// import { notify } from '@/wrappers/notify_wrapper';


//we want to see what happens 

export const useTestStore = defineStore('test_store', {
    state: ()=>({
        add_count: 0,
    }),
    getters: {
        getCount: (state) => {
            return state.add_count;
        },
    },
    actions: {
        addCount() : void {
            this.add_count += 1;
            console.log('new count is: ' + this.add_count.toString());
        },
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