import { defineStore } from 'pinia';


//this is to keep VEventTool's is_liked up-to-date
//because we will be using FilteredGroupedEventsStore as pseudo-cache

interface CurrentLikesDislikesType{
    [event_id: number]: {
        current_value: boolean|null,
        old_value: boolean|null
    }
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
        updateLikeDislike(event_id:number, is_liked:boolean|null) : void {

            let old_is_liked = null;

            if(event_id in this.current_likes_dislikes){

                old_is_liked = this.current_likes_dislikes[event_id]['current_value'];
            }

            //call this before API
            //this prevents race condition in UI during "same data, different component"
            //since syncing opportunity is only when prop is changed, which can happen before API is done
            this.current_likes_dislikes[event_id] = {
                current_value: is_liked,
                old_value: old_is_liked
            };
        },
        revertLikeDislike(event_id:number) : boolean|null {

            if(event_id in this.current_likes_dislikes === false){

                return null;
            }

            //call this on API failure
            this.current_likes_dislikes[event_id].current_value = this.current_likes_dislikes[event_id].old_value;
            this.current_likes_dislikes[event_id].old_value = null;

            return this.current_likes_dislikes[event_id].current_value;
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