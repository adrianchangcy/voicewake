//this store is the final step in creating audio clips
//calls for processing and manages state+notifications+retries
//this is managed more separately from the other steps during the upload
//to allow users to not wait too long, as this is the more time-consuming part

import { defineStore } from 'pinia';
import {
    timeFromNowMS,
    getPiniaDateObject,
    setPiniaDateObject,
    addSeconds,
} from '@/helper_functions';
import { notify } from 'notiwind';
import AudioClipTonesTypes from '@/types/AudioClipTones.interface';

const axios = require('axios');

interface EventsTypes{
    event_id:number,
    event_name: string,
}
interface RecordingsTypes{
    final_blob: Blob,
    blob_duration: number,
    blob_volume_peaks: number[],
}
interface ChecksTypes{
    last_checked: string,
    is_checking: boolean,
    check_attempts: number,
}

interface AudioClipProcessingDetailsTypes{
    is_originator: boolean,
    event: EventsTypes,
    audio_clip_tone: AudioClipTonesTypes,
    recording: RecordingsTypes|null,
    checks: ChecksTypes,
}

//use this when user has uploaded to backend and AWS
//and all there is left is the processing step
//if API has error due to deletion by cronjob, expect 404
interface AudioClipProcessingsTypes{
    [audio_clip_id:number]: AudioClipProcessingDetailsTypes
}



export function useAudioClipProcessingsStore(){

    return defineStore('audio_clip_processings_store', {
        state: ()=>({
            audio_clip_processings: {} as AudioClipProcessingsTypes,
            api_cooldown_ms: 10000,
            min_check_attempts_for_reupload: 4,
        }),
        getters: {
            getAudioClipProcessings: (state)=>{

                return state.audio_clip_processings;
            },
        },
        actions: {
            getAudioClipProcessing(audio_clip_id:number) : AudioClipProcessingDetailsTypes|null {

                if(Object.hasOwn(this.audio_clip_processings, audio_clip_id) === false){

                    return null;
                }

                return this.audio_clip_processings[audio_clip_id];
            },
            deleteAudioClipProcessing(audio_clip_id:number) : void {

                if(Object.hasOwn(this.audio_clip_processings, audio_clip_id) === false){

                    delete this.audio_clip_processings[audio_clip_id];
                }
            },
            storeAudioClipProcessing(
                passed_is_originator:boolean,
                passed_audio_clip_id:number,
                passed_event:EventsTypes,
                passed_audio_clip_tone:AudioClipTonesTypes,
                passed_recording:RecordingsTypes|null,
            ) : void {

                //have to add "passed_" to params to avoid setting them as keys

                if(Object.hasOwn(this.audio_clip_processings, passed_audio_clip_id) === true){

                    return;
                }

                this.audio_clip_processings[passed_audio_clip_id] = {
                    is_originator: passed_is_originator,
                    event: passed_event,
                    audio_clip_tone: passed_audio_clip_tone,
                    recording: passed_recording,
                    checks: {
                        last_checked: setPiniaDateObject(new Date()),
                        is_checking: false,
                        check_attempts: 0,
                    },
                };
            },
            determineReuploadURL(audio_clip_id:number) : string {

                let final_url = window.location.origin;
                
                const target_object = this.audio_clip_processings[audio_clip_id];

                final_url += '/event/' + target_object.event.event_id.toString();
                final_url += '?reupload=' + audio_clip_id.toString();

                return final_url;
            },
            processAudioClipAPI(audio_clip_id:number) : Promise<void>|null {

                if(Object.hasOwn(this.audio_clip_processings, audio_clip_id) === false){

                    throw new Error('audio_clip_id does not exist.');
                }

                //check cooldown
                //can be is_checking=true but user closed app, so it had stayed that way
                //hence, last_checked is the most important

                //this can be -ve, i.e. future, if we receive cooldown_s from API and we update last_checked with it
                const last_checked_ms:number = timeFromNowMS(
                    getPiniaDateObject(this.audio_clip_processings[audio_clip_id].checks.last_checked)
                );

                if(
                    this.audio_clip_processings[audio_clip_id].checks.is_checking === true &&
                    last_checked_ms >= 0 &&
                    last_checked_ms < this.api_cooldown_ms
                ){

                    //don't call yet
                    return null;
                }

                this.audio_clip_processings[audio_clip_id].checks.is_checking = true;

                //prepare URL
                let post_url = window.location.origin + '/api/events';

                if(this.audio_clip_processings[audio_clip_id].is_originator === true){

                    post_url += '/create';

                }else{

                    post_url += '/replies/create';
                }

                post_url += '/process';

                //prepare data
                const data = new FormData();
                data.append('audio_clip_id', JSON.stringify(audio_clip_id));

                //make call
                const api_call = axios.post(post_url, data).then((result:any)=>{

                    //check if already processed before call was made
                    //['is_processed'] === true, 200
                    //['is_processing'] === true, 200
                    //['is_processing'] === false, ['cooldown_s'] > 0, 200

                    if(result.status !== 200){

                        throw new Error('Unhandled status code: ' + result.status.toString());
                    }

                    if(
                        Object.hasOwn(result.data, 'is_processing') === true &&
                        result.data['is_processing'] === true
                    ){

                        //if processing, simply return and call later to check
                        return;
                    }

                    if(
                        Object.hasOwn(result.data, 'is_processed') === true &&
                        result.data['is_processed'] === true
                    ){

                        //create URL
                        const event_url = (
                            window.location.origin + '/event/' +
                            this.audio_clip_processings[audio_clip_id].event.event_id.toString()
                        );

                        //notify
                        notify({
                            type: "audio_clip_process_ok",
                            title: "Recording processed",
                            text: this.audio_clip_processings[audio_clip_id].event.event_name,
                            url: event_url,
                            audio_clip_tone_name: this.audio_clip_processings[audio_clip_id].audio_clip_tone.audio_clip_tone_name,
                            audio_clip_tone_symbol: this.audio_clip_processings[audio_clip_id].audio_clip_tone.audio_clip_tone_symbol,
                        }, -1);

                        //safe to immediately delete
                        delete this.audio_clip_processings[audio_clip_id];

                        return;
                    }

                    //should not reach here
                    throw new Error('Unhandled success request.');

                }).catch((error:any)=>{

                    //determine last_checked
                    let new_last_checked = new Date();

                    if(Object.hasOwn(error.response.data, 'cooldown_s') === true){

                        //not processing, and has cooldown
                        //we do not reset check_attempts
                        new_last_checked = addSeconds(
                            new_last_checked,
                            error.response.data['cooldown_s'] as number
                        );
                    }

                    //update last_checked
                    this.audio_clip_processings[audio_clip_id].checks.last_checked = (
                        setPiniaDateObject(new_last_checked)
                    );

                    //update check
                    this.audio_clip_processings[audio_clip_id].checks.check_attempts += 1;

                    //handle status

                    if(error.request.status === 404){

                        //can either mean no longer available, or dev called the wrong URL

                        delete this.audio_clip_processings[audio_clip_id];

                    }else if(
                        error.request.status === 400 &&
                        this.audio_clip_processings[audio_clip_id].checks.check_attempts > this.min_check_attempts_for_reupload
                    ){

                        //too many processing errors

                        //notify
                        //will only notify at tab where function was called
                        //will not notify at other tabs when this same store is shared
                        notify({
                            type: "audio_clip_process_error",
                            title: "Recording error",
                            text: "Full silence can cause issues. Record again?",
                            url: this.determineReuploadURL(audio_clip_id),
                            audio_clip_tone_name: this.audio_clip_processings[audio_clip_id].audio_clip_tone.audio_clip_tone_name,
                            audio_clip_tone_symbol: this.audio_clip_processings[audio_clip_id].audio_clip_tone.audio_clip_tone_symbol,
                            close_callback: ():void=>{
                                delete this.audio_clip_processings[audio_clip_id];
                            },
                        }, -1);
                    }

                }).finally(()=>{

                    this.audio_clip_processings[audio_clip_id].checks.is_checking = false;
                });

                return api_call;
            },
            async doAllAudioClipProcessings() : Promise<void> {

                //if there are strange bugs, be aware that this function can cause race condition
                //e.g. at "for" loop, when one tab deletes key:value pair while another tab is still looping

                if(Object.keys(this.audio_clip_processings).length === 0){

                    return;
                }

                //prepare bulk Promises

                const api_calls:Promise<void>[] = [];

                for(const audio_clip_id in this.audio_clip_processings){

                    const api_call = this.processAudioClipAPI(Number(audio_clip_id));

                    if(api_call === null){

                        continue;
                    }

                    //add API call to array
                    api_calls.push(api_call);
                }

                //call
                await Promise.allSettled(
                    api_calls
                ).catch(()=>{
                    return;
                });
            },
        },
        persist: true,

        //for shared state
        share: {
            //array of fields that the plugin will ignore
            omit: [],
            //override global config for this store
            enable: true,
            initialize: false,
        },
    })();
}