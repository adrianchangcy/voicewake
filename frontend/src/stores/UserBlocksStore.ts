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
        //only update on GET
        //GET is performed on every page open
        //improves efficiency by not relying on db if GET is done with no changes made
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

                //we use setTimeout() to prevent blocking main thread, in case the array is too large to be instantaneous

                if(to_block === true){

                    setTimeout(()=>{

                        notify({
                            type: 'ok',
                            title: "User blocked",
                            text: "You have blocked " + target_username + ".",
                        }, 4000);

                    }, 0);

                }else{

                    setTimeout(()=>{

                        notify({
                            type: 'ok',
                            title: "User unblocked",
                            text: "You have unblocked " + target_username + ".",
                        }, 4000);

                    }, 0);
                }

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