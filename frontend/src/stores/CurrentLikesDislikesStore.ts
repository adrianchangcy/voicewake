import { defineStore } from 'pinia';


//this is to keep VEventTool's is_liked up-to-date
//because we will be using FilteredGroupedEventsStore as pseudo-cache

interface CurrentLikesDislikesType{
    [event_id: number]: {
        current_value: boolean|null,
        old_value: boolean|null
    }
}


export function useCurrentLikesDislikesStore(is_user_page:boolean){

    const store_id = is_user_page === true ? 'user_page_current_likes_dislikes_store' : 'current_likes_dislikes_store';

    return defineStore(store_id, {
        state: ()=>({
            current_likes_dislikes: {} as CurrentLikesDislikesType,
        }),    
        getters: {
            getCurrentLikesDislikes: (state)=>{

                return state.current_likes_dislikes;
            },
        },
        actions: {
            async updateLikeDislike(event_id:number, is_liked:boolean|null) : Promise<void> {

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
            async revertLikeDislike(event_id:number) : Promise<boolean|null> {

                if(event_id in this.current_likes_dislikes === false){

                    return null;
                }

                //call this on API failure
                this.current_likes_dislikes[event_id].current_value = this.current_likes_dislikes[event_id].old_value;
                this.current_likes_dislikes[event_id].old_value = null;

                return this.current_likes_dislikes[event_id].current_value;
            },
        },
        persist: !is_user_page,
    })();
}