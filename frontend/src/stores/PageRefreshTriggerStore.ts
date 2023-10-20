import { defineStore } from 'pinia';


//this is helpful when applying changes on one browser tab requires refresh on all tabs
//e.g. user signs in when there are other tabs open, those tabs get refreshed by listening to $patch and $subscribe
//right before refresh, reset via resetRefreshContext()
export const usePageRefreshTriggerStore = defineStore('page_refresh_trigger', {
    state: ()=>({
        refresh_context: "" as "logging_in"|"logging_out"|"new_username"|"",
    }),    
    getters: {
        getRefreshContext: (state)=>{

            return state.refresh_context;
        },
    },
    actions: {
        async resetRefreshContext() : Promise<void> {

            this.refresh_context = "";
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