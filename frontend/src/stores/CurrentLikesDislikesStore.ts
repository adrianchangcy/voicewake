import { defineStore } from 'pinia';


//this is to keep VAudioClipTool's is_liked up-to-date
//because we will be using FilteredEventsStore as pseudo-cache

interface CurrentLikesDislikesType{
    [audio_clip_id: number]: {
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
            async updateLikeDislike(audio_clip_id:number, is_liked:boolean|null) : Promise<void> {

                let old_is_liked = null;

                if(Object.hasOwn(this.current_likes_dislikes, audio_clip_id) === true){

                    old_is_liked = this.current_likes_dislikes[audio_clip_id]['current_value'];
                }

                //call this before API
                //this prevents race condition in UI during "same data, different component"
                //since syncing opportunity is only when prop is changed, which can happen before API is done
                this.current_likes_dislikes[audio_clip_id] = {
                    current_value: is_liked,
                    old_value: old_is_liked
                };
            },
            async revertLikeDislike(audio_clip_id:number) : Promise<boolean|null> {

                if(Object.hasOwn(this.current_likes_dislikes, audio_clip_id) === false){

                    return null;
                }

                //call this on API failure
                this.current_likes_dislikes[audio_clip_id].current_value = this.current_likes_dislikes[audio_clip_id].old_value;
                this.current_likes_dislikes[audio_clip_id].old_value = null;

                return this.current_likes_dislikes[audio_clip_id].current_value;
            },
        },
        persist: !is_user_page,
    })();
}