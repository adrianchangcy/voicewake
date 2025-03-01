import { defineStore } from 'pinia';
import { notify } from '@/wrappers/notify_wrapper';
import axios from 'axios';

//persist only to have reliable initial data
//do not try to do cross-tab syncing, that level of complication is unnecessary



//let components/apps manage their own queue of POSTs
//failed ideas
    //let GET apply changes made by POSTs when done
        //better to just do basic checks before applying changes on every POST
        //avoids "POST done after GET, no changes applied", etc.
    //have is_get_processing to reduce GET calls
        //if persist=false, then it's exactly the same as default efficiency
        //if persist=true, then tab closing prematurely let it stay is_get_processing=true
export const useUserBlocksStore = defineStore('user_blocks_store', {
    state: ()=>({
        //on unblock, simply remove from blocked_usernames
        //on components that use this, be sure to only use .copy() and not to directly rely on this
        blocked_usernames: [] as string[],
        //only obtainable from GET
        cache_sync_when_last_action_s: 0,
    }),
    getters: {
        getBlockedUsernames: (state) => {
            return state.blocked_usernames;
        }
    },
    actions: {
        //always run this on page load for pages: user, block list
        //due to cache storing when_last_action_s, efficiency from constant API calls is reasonable
        async getUserBlocksAPI() : Promise<void> {

            let url = window.location.origin + '/api/users/blocks';

            if(this.cache_sync_when_last_action_s !== 0){

                url += '?when_last_action_s=' + this.cache_sync_when_last_action_s.toString();
            }

            await axios.get(url)
            .then((result:any)=>{

                //is up-to-date
                if(Object.hasOwn(result.data, 'is_up_to_date') && result.data['is_up_to_date'] === true){

                    return;
                }

                if(Object.hasOwn(result.data, 'data') === false){

                    throw new Error("'data' is unexpectedly missing.");
                }

                if(Object.hasOwn(result.data, 'when_last_action_s') === false){

                    throw new Error("'when_last_action_s' is unexpectedly missing.");
                }

                this.blocked_usernames = result.data['data'];
                this.cache_sync_when_last_action_s = result.data['when_last_action_s'];
            }).catch(()=>{

                notify({
                    type: 'error',
                    title: 'Error',
                    text: "Unable to get the list of users you've blocked.",
                }, 4000);
            });
        },
        //use queue system to do this, wherever this store is used
        async postUserBlocksAPI(target_username:string, to_block:boolean) : Promise<void> {

            if(target_username.length === 0){

                throw new Error('target_username must not be empty');
            }

            const url = window.location.origin + '/api/users/blocks';

            const data = new FormData();
            data.append('username', target_username);
            data.append('to_block', JSON.stringify(to_block));

            await axios.post(url, data)
            .then(()=>{

                let success_title = "";
                let success_text = "";

                if(to_block === true){

                    this.blocked_usernames.unshift(target_username);

                    success_title = "Blocked";
                    success_text = "You have blocked " + target_username + ".";

                }else{

                    this.blocked_usernames.indexOf('target_username');

                    const target_index = this.blocked_usernames.findIndex((username)=>{username === target_username});

                    if(target_index !== -1){

                        this.blocked_usernames.splice(target_index, 1);
                    }

                    success_title = "Unblocked";
                    success_text = "You have unblocked " + target_username + ".";
                }

                notify({
                    type: 'ok',
                    title: success_title,
                    text: success_text,
                }, 4000);

            }).catch((error:any)=>{

                notify({
                    type: 'error',
                    title: 'Error',
                    text: error.response.data['message'],
                }, 4000);
            });

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