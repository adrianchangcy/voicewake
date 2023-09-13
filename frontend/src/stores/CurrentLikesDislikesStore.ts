import { defineStore } from 'pinia';


//this is to keep VEventTool's is_liked up-to-date
//because we will be using FilteredGroupedEventsStore as pseudo-cache

interface CurrentLikesDislikesType{
    [event_id: number]: boolean|null
}


export const useCurrentLikesDislikesStore = defineStore('current_likes_dislikes_store', {
    state: ()=>({
        current_likes_dislikes: {} as CurrentLikesDislikesType,
    }),    
    getters: {
        getCurrentLikesDislikes: (state)=>{

            return state.current_likes_dislikes;
        },
    },
    actions: {
        addLikeDislike(event_id:number, is_liked:boolean|null) : void {

            this.current_likes_dislikes[event_id] = is_liked;
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