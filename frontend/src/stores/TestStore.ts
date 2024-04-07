import { defineStore } from 'pinia';
// import { notify } from '@/wrappers/notify_wrapper';



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
    persist: false,
    share: {
        //array of fields that the plugin will ignore
        omit: [],
        //override global config for this store
        enable: true,
        initialize: false,
    },
});