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
    id:number,
    event_name: string,
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
            api_cooldown_ms: 30000,
            api_call_interval_ms: 10000,
            min_check_attempts_for_reupload: 4,
        }),
        getters: {
            getAudioClipProcessings: (state)=>{

                return state.audio_clip_processings;
            },
        },
        actions: {
            hasAudioClipId(audio_clip_id:number) : boolean {

                return Object.hasOwn(this.audio_clip_processings, audio_clip_id);
            },
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
            ) : void {

                //have to add "passed_" to params to avoid setting them as keys

                if(Object.hasOwn(this.audio_clip_processings, passed_audio_clip_id) === true){

                    return;
                }

                this.audio_clip_processings[passed_audio_clip_id] = {
                    is_originator: passed_is_originator,
                    event: passed_event,
                    audio_clip_tone: passed_audio_clip_tone,
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

                final_url += '/event/' + target_object.event.id.toString();
                final_url += '?reupload=' + audio_clip_id.toString();

                return final_url;
            },
            processAudioClipAPI(audio_clip_id:number) : Promise<void>|null {

                if(Object.hasOwn(this.audio_clip_processings, audio_clip_id) === false){

                    return null;
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
                        Object.hasOwn(result.data, 'is_processed') === true &&
                        result.data['is_processed'] === true
                    ){

                        //create URL
                        const event_url = (
                            window.location.origin + '/event/' +
                            this.audio_clip_processings[audio_clip_id].event.id.toString()
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

                    if(
                        error.request.status === 409 &&
                        Object.hasOwn(error.response.data, 'is_processing') === true &&
                        error.response.data['is_processing'] === true
                    ){

                        //if processing, simply return and call later to check
                        throw error;
                    }

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
                            text: this.audio_clip_processings[audio_clip_id].event.event_name,
                            url: this.determineReuploadURL(audio_clip_id),
                            audio_clip_tone_name: this.audio_clip_processings[audio_clip_id].audio_clip_tone.audio_clip_tone_name,
                            audio_clip_tone_symbol: this.audio_clip_processings[audio_clip_id].audio_clip_tone.audio_clip_tone_symbol,
                        }, -1);

                        delete this.audio_clip_processings[audio_clip_id];
                    }

                    //this allows redirect handling
                    throw error;

                }).finally(()=>{

                    if(Object.hasOwn(this.audio_clip_processings, audio_clip_id) === true){

                        this.audio_clip_processings[audio_clip_id].checks.is_checking = false;
                    }
                });

                return api_call;
            },
            getReuploadAudioClipId() : number|null {

                //check if URL has get param

                const current_url = new URL(window.location.href);
                const reupload_audio_clip_id_from_url = current_url.searchParams.get('reupload');

                if(reupload_audio_clip_id_from_url === null){

                    return null;
                }

                //check if id is passed in template

                const container = (document.getElementById('data-container-get-events') as HTMLElement);

                if(container === null){

                    return null;
                }

                const reupload_audio_clip_id = container.getAttribute('data-reupload-audio-clip-id');

                if(reupload_audio_clip_id === null){

                    return null;
                }

                return Number(reupload_audio_clip_id_from_url);
            },
            processUntilNoneLeft() : void {

                //processAudioClipAPI() will delete when notified
                //we prefer worst case of "user missed it" over 1 processing spammed many times

                if(Object.keys(this.audio_clip_processings).length === 0){

                    return;
                }

                //don't run this at reupload page
                if(this.getReuploadAudioClipId() !== null){

                    return;
                }

                console.log('we starting');

                const current_interval = window.setInterval(async ()=>{

                    const audio_clip_ids = Object.keys(this.audio_clip_processings);
                    const target_audio_clip_id = Number(audio_clip_ids[0]);

                    if(audio_clip_ids.length === 0){

                        window.clearInterval(current_interval);
                    }

                    const api_call = this.processAudioClipAPI(
                        target_audio_clip_id
                    );

                    if(api_call === null){

                        return;
                    }

                    //if audio_clip_id no longer exists, it means we have notified
                    //stop interval, otherwise we'd overwhelm the UI
                    api_call.catch(()=>{
                        return;
                    }).finally(()=>{

                        if(Object.hasOwn(this.audio_clip_processings, target_audio_clip_id) === false){

                            window.clearInterval(current_interval);
                        }
                    });

                }, this.api_call_interval_ms);
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