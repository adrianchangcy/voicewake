import { defineStore } from 'pinia';


//this store is used to track the last VPlayback instance that the user had interacted with
//and, at a page where VPlayback always has propEvent, to track where it had stopped when it switched to another event
    //useful for play #0 --> play #1 --> continue from last stopped when play #0

//if bugs occur, check if event_id and stopped_at_s are not in sync
    //also, <audio>.duration changes according to rate
    //currently always 1, so if we implement rate, remember to update the code here

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

            if(target_index === -1){

                //does not exist

                //if limit has been reached, remove oldest via shift() until are 1 item away from limit
                while(this.event_id.length >= event_limit){

                    this.event_id.shift();
                    this.stopped_at_s.shift();
                }

                //push() as newest
                this.event_id.push(event_id);
                this.stopped_at_s.push(stopped_at_s);

            }else if(target_index === (this.event_id.length - 1)){

                //exists and is already newest
                return;

            }else{

                //remove older record of itself and add to newest
                this.event_id.splice(target_index, 1);
                this.stopped_at_s.splice(target_index, 1);

                this.event_id.push(event_id);
                this.stopped_at_s.push(stopped_at_s);

                //longer event is id 2
                console.log('storing for' + event_id);
                console.log(this.event_id);
                console.log(this.stopped_at_s);
            }
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
    persist: {
        //persist these states
        paths: [
            'event_id', 'stopped_at_s',
        ],
        debug: true
    },

    //no need to share store across tabs, hence false values below
    share: {
        //array of fields that the plugin will ignore
        omit: [],
        //override global config for this store
        enable: false,
        initialize: false,
    },
});