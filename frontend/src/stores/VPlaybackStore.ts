import { defineStore } from 'pinia';
import AudioClipsTypes from '@/types/AudioClips.interface';
import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';

//this store is used to track the last VPlayback instance that the user had interacted with
//and, at a page where VPlayback always has propAudioClip, to track where it had stopped when it switched to another audio_clip
    //useful for play #0 --> play #1 --> continue from last stopped when play #0

//if bugs occur, check if audio_clip_id and stopped_at_s are not in sync
    //also, <audio>.duration changes according to rate
    //currently always 1, so if we implement rate, remember to update the code here

//make sure to sync the order of audio_clip_id with stopped_at_s
//we separate them instead of storing as dict, because array.includes() makes checking easier
export const useVPlaybackStore = defineStore('vplayback', {
    state: ()=>({
        active_vplayback_uuids: [] as string[],
        last_interacted_vplayback_uuid: "",

        playing_audio_clip: null as AudioClipsTypes|AudioClipsAndLikeDetailsTypes|null,
        can_autoplay: false,
        
        //change this value to trigger pause at VPlayback
        pause_trigger: false,
        //this is needed when we have multiple VPlayback instances
        can_pause_trigger_affect_last_interacted_vplayback: true,

        audio_clip_id: [] as number[],   //left to right, oldest to newest
        stopped_at_s: [] as number[],   //left to right, oldest to newest
        max_stopped_at_quantity: 10,
    }),
    getters: {
        getLastInteractedVPlaybackUUID: (state)=>{

            return state.last_interacted_vplayback_uuid;
        },
        getPlayingAudioClip: (state)=>{

            return state.playing_audio_clip;
        },
        getCanAutoplay: (state)=>{

            return state.can_autoplay;
        },
        getPauseTrigger: (state)=>{

            return state.pause_trigger;
        },
    },
    actions: {
        triggerPause(affect_last_interacted_vplayback:boolean=true) : void {

            this.pause_trigger = !this.pause_trigger;
            this.can_pause_trigger_affect_last_interacted_vplayback = affect_last_interacted_vplayback;
        },
        updateCanAutoplay(can_autoplay:boolean) : void {

            this.can_autoplay = can_autoplay;
        },
        updatePlayingAudioClip(audio_clip:AudioClipsTypes|AudioClipsAndLikeDetailsTypes|null) : void {

            this.playing_audio_clip = audio_clip;
        },
        updateLastInteractedVPlaybackUUID(vplayback_uuid:string) : void {

            this.last_interacted_vplayback_uuid = vplayback_uuid;
        },
        async addAudioClipLastStoppedS(audio_clip_id:number, stopped_at_s:number) : Promise<void> {

            const target_index = this.audio_clip_id.indexOf(audio_clip_id);

            if(target_index === -1){

                //does not exist

                //if limit has been reached, remove oldest via shift() until 1 item away from limit
                while(this.audio_clip_id.length >= this.max_stopped_at_quantity){

                    this.audio_clip_id.shift();
                    this.stopped_at_s.shift();
                }

                //push() as newest
                this.audio_clip_id.push(audio_clip_id);
                this.stopped_at_s.push(stopped_at_s);
                return;
            }

            //simply update existing record
            this.stopped_at_s[target_index] = stopped_at_s;
        },
        async getAudioClipLastStoppedS(audio_clip_id:number) : Promise<number|null> {

            const target_index = this.audio_clip_id.indexOf(audio_clip_id);

            if(target_index === -1){

                return null;
            }

            return this.stopped_at_s[target_index];
        },
        async addActiveVPlaybackUUID(uuid:string) : Promise<void> {

            if(this.active_vplayback_uuids.indexOf(uuid) === -1){

                this.active_vplayback_uuids.push(uuid);
            }
        },
        async focusFirstVPlaybackUUID() : Promise<void> {

            if(this.active_vplayback_uuids.length > 0){

                this.last_interacted_vplayback_uuid = this.active_vplayback_uuids[0];
            }
        },
    },
    //all things considered, we get overall better usability with persistence than without
    persist: {
        //persist these states
        paths: [
            'audio_clip_id', 'stopped_at_s',
        ],
    },
});