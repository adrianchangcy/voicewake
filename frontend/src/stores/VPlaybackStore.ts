import { defineStore } from 'pinia';


//this store is used to track the last VPlayback instance that the user had interacted with
//and, at a page where VPlayback always has propEvent, to track where it had stopped when it switched to another event
    //useful for play #0 --> play #1 --> continue from last stopped when play #0

const event_limit = 10;

//make sure to sync the order of event_id with stopped_at_s
//we separate them instead of storing as dict, because array.includes() makes checking easier
export const useVPlaybackStore = defineStore('vplayback', {
    state: ()=>({
        last_interacted_uuid: "",
        event_id: [] as number[],   //left to right, oldest to newest
        stopped_at_s: [] as number[],   //left to right, oldest to newest
    }),
    getters: {
        getLastInteractedUUID: (state)=>{

            return state.last_interacted_uuid;
        },
    },
    actions: {
        updateLastInteractedUUID(uuid:string) : void {

            this.last_interacted_uuid = uuid;
        },
        addEventPlaybackLastStopped(event_id:number, stopped_at_s:number) : void {

            const target_index = this.event_id.indexOf(event_id);

            if(target_index !== -1){

                //event already exists, remove old
                this.event_id.splice(target_index, 1);
                this.stopped_at_s.splice(target_index, 1);
            }

            //if arrays have reached limit, remove oldest
            if(this.event_id.length === event_limit && this.stopped_at_s.length === event_limit){

                this.event_id.shift();
                this.stopped_at_s.shift();
            }

            this.event_id.push(event_id);
            this.stopped_at_s.push(stopped_at_s);
        },
        getEventPlaybackLastStoppedS(event_id:number) : number|null {

            const target_index = this.event_id.indexOf(event_id);

            if(target_index === -1){

                return null;
            }

            return this.stopped_at_s[target_index];
        }
    },
    //all things considered, we get overall better usability with persistence than without
    persist: true,

    //no need to share store across tabs, hence false values below
    share: {
        //array of fields that the plugin will ignore
        omit: [],
        //override global config for this store
        enable: false,
        initialize: false,
    },
});