//this store is the final step in creating audio clips
//calls for processing and manages state+notifications+retries
//this is managed more separately from the other steps during the upload
//to allow users to not wait too long, as this is the more time-consuming part

import { defineStore } from 'pinia';
import {
    timeFromNowMS,
    getPiniaDateObject,
    setPiniaDateObject,
    getShortenedString,
} from '@/helper_functions';
import { notify } from '@/wrappers/notify_wrapper';
import AudioClipTonesTypes from '@/types/AudioClipTones.interface';
import NotificationsTypes from '@/types/Notifications.interface';

const axios = require('axios');

interface EventsTypes{
    id:number,
    event_name: string,
}
interface ChecksTypes{
    check_again: boolean,
    last_checked: string,
    is_checking: boolean,
}
//use this for easier state management at parent components
//otherwise, we'd have to throw the request error, and rewrite the same code at parent components
type ProcessingStatusesTypes = ''|'error'|'processed'|'processing'|'not_found'|'lambda_error'

interface AudioClipProcessingDetailsTypes{
    is_originator: boolean,
    event: EventsTypes,
    audio_clip_tone: AudioClipTonesTypes,
    checks: ChecksTypes,
    notification_details: {
        args: NotificationsTypes,
        duration_ms: number
    }|null,
    can_auto_process: boolean,
    status: ProcessingStatusesTypes,
    lambda_attempts_left: number|null,
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
            api_cooldown_ms: 20000,
            api_call_interval_ms: 10000,
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
            ) : void {

                //have to add "passed_" to params to avoid setting them as keys

                if(Object.hasOwn(this.audio_clip_processings, passed_audio_clip_id) === true){

                    return;
                }

                const pinia_date_now = setPiniaDateObject(new Date());

                this.audio_clip_processings[passed_audio_clip_id] = {
                    is_originator: passed_is_originator,
                    event: passed_event,
                    audio_clip_tone: passed_audio_clip_tone,
                    checks: {
                        check_again: true,
                        last_checked: pinia_date_now,
                        is_checking: false,
                    },
                    notification_details: null,
                    can_auto_process: true,
                    status: '',
                    lambda_attempts_left: null,
                };
            },
            determineReuploadURL(audio_clip_id:number) : string {

                let final_url = window.location.origin;
                
                const target_object = this.audio_clip_processings[audio_clip_id];

                final_url += '/event/' + target_object.event.id.toString();
                final_url += '?reupload=' + audio_clip_id.toString();

                return final_url;
            },
            async processAudioClipAPI(
                current_context:'user_submit'|'auto_evaluation',
                audio_clip_id:number,
            ) : Promise<void> {

                //notification_details is only null when there has been no important errors
                //if there were important errors, they cannot turn back into null

                if(Object.hasOwn(this.audio_clip_processings, audio_clip_id) === false){

                    throw new Error('no recording');
                }

                if(this.audio_clip_processings[audio_clip_id].checks.check_again === false){

                    return;
                }

                //check cooldown
                //can be is_checking=true but user closed app, so it had stayed that way
                //hence, last_checked is the most important

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

                //reset
                this.audio_clip_processings[audio_clip_id].status = '';
                this.audio_clip_processings[audio_clip_id].notification_details = null;

                //make call
                await axios.post(post_url, data).then((result:any)=>{

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

                        const notify_text = (
                            'Event: "' +
                            getShortenedString(
                                this.audio_clip_processings[audio_clip_id].event.event_name,
                                8
                            ) +
                            '"'
                        );

                        this.audio_clip_processings[audio_clip_id].notification_details = {
                            args: {
                                type: 'ok',
                                title: 'Recording processed',
                                text: notify_text,
                                icon: {'audio_clip_tone': {
                                    audio_clip_tone_name: this.audio_clip_processings[audio_clip_id].audio_clip_tone.audio_clip_tone_name,
                                    audio_clip_tone_symbol: this.audio_clip_processings[audio_clip_id].audio_clip_tone.audio_clip_tone_symbol,
                                }},
                                actions: [
                                    {
                                        type: 'url',
                                        style: 'primary',
                                        text: 'Open',
                                        url: event_url,
                                    },
                                ],
                                has_close_button: true,
                                close_callback: ()=>{
                                    delete this.audio_clip_processings[audio_clip_id];
                                },
                            },
                            duration_ms: -1
                        };

                        this.audio_clip_processings[audio_clip_id].status = 'processed';

                        //no need any further checks
                        this.audio_clip_processings[audio_clip_id].checks.check_again = false;

                        return;
                    }

                    //should not reach here
                    throw new Error('Unhandled success request.');

                }).catch((error:any)=>{

                    //defaults, only relevant on error
                    this.audio_clip_processings[audio_clip_id].status = 'error';
                    this.audio_clip_processings[audio_clip_id].can_auto_process = true;

                    switch(error.request.status){

                        case 400:

                            if(
                                Object.hasOwn(error.response.data, 'attempts_left') === true
                            ){

                                //when attempts_left is 0, next call will permanently remove recording from db

                                //create URL
                                const event_url = (
                                    window.location.origin + '/event/' +
                                    this.audio_clip_processings[audio_clip_id].event.id.toString() +
                                    '?reupload=' +
                                    audio_clip_id.toString()
                                );

                                const notify_text = (
                                    'Event: "' +
                                    getShortenedString(
                                        this.audio_clip_processings[audio_clip_id].event.event_name,
                                        8
                                    ) +
                                    '"'
                                );

                                this.audio_clip_processings[audio_clip_id].notification_details = {
                                    args: {
                                        type: 'error',
                                        title: 'Recording error',
                                        text: notify_text,
                                        icon: {'audio_clip_tone': {
                                            audio_clip_tone_name: this.audio_clip_processings[audio_clip_id].audio_clip_tone.audio_clip_tone_name,
                                            audio_clip_tone_symbol: this.audio_clip_processings[audio_clip_id].audio_clip_tone.audio_clip_tone_symbol,
                                        }},
                                        actions: [
                                            {
                                                type: 'url',
                                                style: 'primary',
                                                text: 'Reupload',
                                                url: event_url,
                                            },
                                        ],
                                        has_close_button: true,
                                        close_callback: ()=>{
                                            delete this.audio_clip_processings[audio_clip_id];
                                        },
                                    },
                                    duration_ms: -1
                                };

                                this.audio_clip_processings[audio_clip_id].status = 'lambda_error';
                                this.audio_clip_processings[audio_clip_id].lambda_attempts_left = error.response.data['attempts_left'];

                                //only user submit can perform processing from now on
                                this.audio_clip_processings[audio_clip_id].can_auto_process = false;
                            }

                            break;

                        case 404: {

                            //no longer available
                            //can be caused by:
                                //dev called the wrong URL, or too many attempts, or cronjob auto-expire
                            const notify_text = (
                                'Sorry, your recording for event "' +
                                getShortenedString(
                                    this.audio_clip_processings[audio_clip_id].event.event_name,
                                    8
                                ) +
                                '" is no longer available.'
                            );

                            this.audio_clip_processings[audio_clip_id].notification_details = {
                                args: {
                                    type: 'error',
                                    title: 'Recording removed',
                                    text: notify_text,
                                    icon: {'audio_clip_tone': {
                                        audio_clip_tone_name: this.audio_clip_processings[audio_clip_id].audio_clip_tone.audio_clip_tone_name,
                                        audio_clip_tone_symbol: this.audio_clip_processings[audio_clip_id].audio_clip_tone.audio_clip_tone_symbol,
                                    }},
                                    has_close_button: true,
                                    close_callback: ()=>{
                                        delete this.audio_clip_processings[audio_clip_id];
                                    },
                                },
                                duration_ms: -1
                            };

                            this.audio_clip_processings[audio_clip_id].status = 'not_found';
                            this.audio_clip_processings[audio_clip_id].checks.check_again = false;
                            break;
                        }

                        case 409:

                            if(
                                Object.hasOwn(error.response.data, 'is_processing') === true &&
                                error.response.data['is_processing'] === true
                            ){

                                //still processing
                                this.audio_clip_processings[audio_clip_id].status = 'processing';
                            }

                            break;

                        default:

                            break;
                    }

                    //notify

                    if(
                        current_context === 'auto_evaluation' &&
                        this.audio_clip_processings[audio_clip_id].notification_details !== null
                    ){

                        //notify
                        notify(
                            this.audio_clip_processings[audio_clip_id].notification_details!.args,
                            this.audio_clip_processings[audio_clip_id].notification_details!.duration_ms
                        );

                        return;
                    }

                }).finally(()=>{

                    if(Object.hasOwn(this.audio_clip_processings, audio_clip_id) === false){

                        return;
                    }

                    //update check details

                    this.audio_clip_processings[audio_clip_id].checks.is_checking = false;

                    this.audio_clip_processings[audio_clip_id].checks.last_checked = (
                        setPiniaDateObject(new Date())
                    );
                });
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
            autoEvaluateAllAudioClipProcessings() : void {

                interface hasNotifiedTypes {
                    [audio_clip_id:number]: boolean,
                }

                //this will set up an interval on a per-processing basis
                //i.e. slow and timely
                //should only use at NavBar

                //if user is at reupload page, do nothing
                if(this.getReuploadAudioClipId() !== null){

                    return;
                }

                //all notifications shall only be displayed once
                const notify_tracker = {} as hasNotifiedTypes

                //do -1 so we can increment early, instead of at the end
                //this helps us to avoid being stuck at one index on error
                let index_tracker = -1;
                let is_calling_api = false;

                //every 10s, check entire store
                window.setInterval(async()=>{

                    const audio_clip_ids = Object.keys(this.audio_clip_processings);

                    if(audio_clip_ids.length === 0 || is_calling_api === true){

                        return;
                    }

                    index_tracker += 1;

                    if(index_tracker >= audio_clip_ids.length){

                        //some processings were removed in-between intervals by external actions
                        //readjust
                        index_tracker = 0;
                    }

                    const target_audio_clip_processing = this.getAudioClipProcessing(
                        Number(audio_clip_ids[index_tracker])
                    );

                    if(target_audio_clip_processing === null){

                        return;
                    }

                    //add to notify_tracker first
                    if(
                        Object.hasOwn(notify_tracker, audio_clip_ids[index_tracker]) === false
                    ){

                        notify_tracker[Number(audio_clip_ids[index_tracker])] = false;
                    }

                    //if already notified, don't continue
                    if(notify_tracker[Number(audio_clip_ids[index_tracker])] === true){

                        return;
                    }

                    const last_checked_ms:number = timeFromNowMS(
                        getPiniaDateObject(target_audio_clip_processing.checks.last_checked)
                    );

                    //if is already checking since not too long ago, skip
                    if(
                        target_audio_clip_processing.checks.is_checking === true &&
                        last_checked_ms >= 0 &&
                        last_checked_ms < this.api_cooldown_ms
                    ){
        
                        return;
                    }

                    //for processings that cannot be evaluated here, we just notify
                    //since the reason they still exist is because user has not acnkwowledged/closed them

                    if(
                        target_audio_clip_processing.can_auto_process === false ||
                        target_audio_clip_processing.checks.check_again === false
                    ){

                        //notification_details is only null when there has been no important errors
                        //if there were important errors, they cannot turn back into null
                        if(
                            target_audio_clip_processing.notification_details !== null
                        ){

                            notify_tracker[Number(audio_clip_ids[index_tracker])] = true;

                            notify(
                                target_audio_clip_processing.notification_details.args,
                                target_audio_clip_processing.notification_details.duration_ms,
                            )
                        }

                        return;
                    }

                    //current audio_clip_processing can be auto-evaluated
                    //we evaluate only one for every interval

                    is_calling_api = true;

                    await this.processAudioClipAPI(
                        'auto_evaluation',
                        Number(audio_clip_ids[index_tracker])
                    ).catch(()=>{
                        return;
                    }).finally(()=>{
                        is_calling_api = false;
                    });

                    if(

                        (target_audio_clip_processing.can_auto_process as boolean) === false ||
                        (target_audio_clip_processing.checks.check_again as boolean) === false
                    ){

                        //notification_details is only null when there has been no important errors
                        //if there were important errors, they cannot turn back into null
                        if(
                            target_audio_clip_processing.notification_details !== null
                        ){

                            notify_tracker[Number(audio_clip_ids[index_tracker])] = true;

                            notify(
                                target_audio_clip_processing.notification_details.args,
                                target_audio_clip_processing.notification_details.duration_ms,
                            )
                        }

                        return;
                    }

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