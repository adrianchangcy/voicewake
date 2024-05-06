//this store is the final step in creating audio clips
//calls for processing and manages state+notifications+retries
//this is managed more separately from the other steps during the upload
//to allow users to not wait too long, as this is the more time-consuming part

import { defineStore } from 'pinia';
import { getShortenedString, setPiniaDateObject } from '@/helper_functions';
import AudioClipTonesTypes from '@/types/AudioClipTones.interface';
import AudioClipProcessingStatusesTypes from '@/types/values/AudioClipProcessingStatuses';
import { AudioClipProcessingDetailsTypes, EventsTypes } from '@/types/AudioClipProcessingDetails.interface';

const axios = require('axios');

//use this when user has uploaded to backend and AWS
//and all there is left is the processing step
//if API has error due to deletion by cronjob, expect 404
interface AudioClipProcessingsTypes{
    [audio_clip_id:number]: AudioClipProcessingDetailsTypes,
}

interface EventIdKeyAudioClipIdValue{
    [event_id:number]: number,
}



export function useAudioClipProcessingsStore(){

    return defineStore('audio_clip_processings_store', {
        state: ()=>({
            audio_clip_processings: {} as AudioClipProcessingsTypes,

            //allows cancel/expire reply to also remove records from this store
            event_id_key_audio_clip_id_value: {} as EventIdKeyAudioClipIdValue,

            //allows watcher to remove reply choice once processed
            last_processed_audio_clip_id: null as number|null,

            polling_processings_timeout: null as number|null,
            polling_processings_timeout_delay_ms: 1000,

            audio_clip_unprocessed_expiry_s: 0,
        }),
        getters: {
            getAudioClipProcessings: (state)=>{

                return state.audio_clip_processings;
            },
        },
        actions: {
            getStaticValuesFromTemplate(data_container_element:HTMLElement) : void {

                //get essential data first, where we don't proceed if they don't exist
                const audio_clip_unprocessed_expiry_seconds = data_container_element.getAttribute('data-audio-clip-unprocessed-expiry-seconds') as string;
    
                if(audio_clip_unprocessed_expiry_seconds === null){
    
                    //don't proceed because we lack essential data
                    throw new Error('Essential data was not passed into template.');
                }
    
                //get data from SSR template
                this.audio_clip_unprocessed_expiry_s = parseInt(audio_clip_unprocessed_expiry_seconds) * 1000;
            },
            getAudioClipIdByEventId(event_id:number) : number|null {

                if(Object.hasOwn(this.event_id_key_audio_clip_id_value, event_id) === false){

                    return null;
                }

                return this.event_id_key_audio_clip_id_value[event_id];
            },
            getAudioClipProcessing(audio_clip_id:number) : AudioClipProcessingDetailsTypes|null {

                if(Object.hasOwn(this.audio_clip_processings, audio_clip_id) === false){

                    return null;
                }

                return this.audio_clip_processings[audio_clip_id];
            },
            deleteAudioClipProcessing(audio_clip_id:number) : void {

                delete this.audio_clip_processings[audio_clip_id];

                const event_ids = Object.keys(this.event_id_key_audio_clip_id_value);
                const audio_clip_ids = Object.values(this.event_id_key_audio_clip_id_value);

                const event_id_index = audio_clip_ids.indexOf(audio_clip_id);

                if(event_id_index === -1){

                    return;
                }

                delete this.event_id_key_audio_clip_id_value[Number(event_ids[event_id_index])];
            },
            storeAudioClipProcessing(
                passed_audio_clip_role_name:'originator'|'responder',
                passed_audio_clip_id:number,
                passed_event:EventsTypes,
                passed_audio_clip_tone:AudioClipTonesTypes,
            ) : void {

                //have to add "passed_" to params to avoid setting them as keys

                if(Object.hasOwn(this.audio_clip_processings, passed_audio_clip_id) === true){

                    return;
                }

                const main_text = (
                    'Event: "' +
                    getShortenedString(
                        passed_event.event_name,
                        8
                    ) +
                    '"'
                );

                this.audio_clip_processings[passed_audio_clip_id] = {
                    audio_clip_role_name: passed_audio_clip_role_name,
                    event: passed_event,
                    audio_clip_tone: passed_audio_clip_tone,
                    status: 'processing',
                    title: 'Processing recording',
                    main_text: main_text,
                    last_lambda_attempt: '',
                    lambda_attempts_left: null,
                    can_close: false,
                };
            },
            determineReuploadURL(audio_clip_id:number) : string {

                let final_url = window.location.origin;
                
                const target_object = this.audio_clip_processings[audio_clip_id];

                final_url += '/event/' + target_object.event.id.toString();
                final_url += '?reupload=' + audio_clip_id.toString();

                return final_url;
            },
            updateLastProcessedAudioClipId(audio_clip_id:number) : void {

                this.last_processed_audio_clip_id = audio_clip_id;
            },
            async processAudioClipAPI(audio_clip_id:number) : Promise<void> {

                //notification_details is only null when there has been no important errors
                //if there were important errors, they cannot turn back into null

                if(Object.hasOwn(this.audio_clip_processings, audio_clip_id) === false){

                    throw new Error('audio clip does not exist in store');
                }

                //prepare URL
                let post_url = window.location.origin + '/api/events';

                if(this.audio_clip_processings[audio_clip_id].audio_clip_role_name === 'originator'){

                    post_url += '/create';

                }else if(this.audio_clip_processings[audio_clip_id].audio_clip_role_name === 'responder'){

                    post_url += '/replies/create';

                }else{

                    throw new Error('Unrecognised audio_clip_role_name');
                }

                post_url += '/process';

                //prepare data
                const data = new FormData();
                data.append('audio_clip_id', JSON.stringify(audio_clip_id));

                //make call
                await axios.post(post_url, data).then((result:any)=>{

                    if(result.request.status !== 200){

                        throw new Error('Unhandled success request.');
                    }

                    if(
                        Object.hasOwn(result.data, 'is_processed') === true &&
                        result.data['is_processed'] === true
                    ){

                        //processed, ok

                        this.updateLastProcessedAudioClipId(audio_clip_id);
                        this.updateProcessing(audio_clip_id, 'processed');
                        return;
                    }

                    if(Object.hasOwn(result.data, 'attempts_left') === true){

                        //ok, added to task queue

                        this.updateProcessing(audio_clip_id, 'processing', result.data['attempts_left']);
                        return;
                    }

                    throw new Error('Unhandled success request.');

                }).catch((error:any)=>{

                    if(Object.hasOwn(error, "request") === false){

                        throw new Error('Unhandled success request.');
                    }

                    switch(error.request.status){

                        case 400: {

                            //simple generic error
                            //delete from store, as next API call will re-create

                            delete this.audio_clip_processings[audio_clip_id];
                            throw error;
                        }

                        case 404: {

                            //no longer available

                            this.updateProcessing(audio_clip_id, 'not_found');
                            break;
                        }

                        case 409:

                            if(
                                Object.hasOwn(error.response.data, 'is_processing') === true &&
                                Object.hasOwn(error.response.data, 'attempts_left') === true &&
                                error.response.data['is_processing'] === true
                            ){

                                //still processing

                                this.updateProcessing(audio_clip_id, 'processing', error.response.data['attempts_left']);
                                return;
                            }

                            throw new Error('Unhandled error request.');

                        default:

                            //delete and recreate later

                            delete this.audio_clip_processings[audio_clip_id];
                            break;
                    }
                });
            },
            async checkProcessingStatusAPI(audio_clip_id:number) : Promise<void> {

                if(Object.hasOwn(this.audio_clip_processings, audio_clip_id) === false){

                    throw new Error('audio clip does not exist in store');
                }

                //prepare URL
                let post_url = window.location.origin + '/api/events';

                if(this.audio_clip_processings[audio_clip_id].audio_clip_role_name === 'originator'){

                    post_url += '/create';

                }else if(this.audio_clip_processings[audio_clip_id].audio_clip_role_name === 'responder'){

                    post_url += '/replies/create';

                }else{

                    throw new Error('Unrecognised audio_clip_role_name');
                }

                post_url += '/process/status';

                //prepare data
                const data = new FormData();
                data.append('audio_clip_id', JSON.stringify(audio_clip_id));

                //make call
                await axios.post(post_url, data).then((result:any)=>{

                    if(result.request.status !== 200){

                        throw new Error('Unhandled success request.');
                    }

                    if(
                        Object.hasOwn(result.data, 'is_processed') === true &&
                        result.data['is_processed'] === true
                    ){

                        //already processed

                        this.updateProcessing(audio_clip_id, 'processed');
                        return;

                    }else if(
                        Object.hasOwn(result.data, 'is_processing') === true &&
                        Object.hasOwn(result.data, 'attempts_left') === true &&
                        result.data['is_processing'] === false
                    ){

                        this.updateProcessing(audio_clip_id, 'lambda_error', result.data['attempts_left']);
                        return;
                    }

                    throw new Error('Unhandled success request.');

                }).catch((error:any)=>{

                    if(Object.hasOwn(error, "request") === false){

                        throw new Error('Unhandled success request.');
                    }

                    switch(error.request.status){

                        //don't handle 400 here, since there are no permanent 400 errors
                        //just silently retry

                        case 404:

                            //no longer available

                            this.updateProcessing(audio_clip_id, 'not_found');
                            break;

                        case 409:

                            if(
                                Object.hasOwn(error.response.data, 'is_processing') === true &&
                                Object.hasOwn(error.response.data, 'attempts_left') === true &&
                                error.response.data['is_processing'] === true
                            ){

                                //still processing

                                this.updateProcessing(
                                    audio_clip_id,
                                    'processing',
                                    error.response.data['attempts_left']
                                );
                                return;
                            }

                            throw new Error('Unhandled error request.');

                        default:

                            //do nothing
                            break;
                    }
                });
            },
            startPollingProcessings() : void {

                //for processing, we do 1 by 1 so we don't overwhelm server
                //even though Promise.allSettled() is most elegant

                this.polling_processings_timeout = window.setTimeout(()=>{

                    const audio_clip_ids = Object.keys(this.audio_clip_processings);

                    for(let x=0; x < audio_clip_ids.length; x++){

                        const audio_clip_id = Number(audio_clip_ids[x]);

                        if(
                            this.audio_clip_processings[audio_clip_id].status !== 'processing'
                        ){

                            continue;
                        }

                        this.checkProcessingStatusAPI(audio_clip_id).finally(()=>{

                            //loop again when done
                            this.startPollingProcessings();
                        });

                        break;
                    }

                }, this.polling_processings_timeout_delay_ms);
            },
            stopPollingProcessings() : void {

                if(this.polling_processings_timeout === null){

                    return;
                }

                window.clearTimeout(this.polling_processings_timeout);
                this.polling_processings_timeout = null;
            },
            updateProcessing(
                audio_clip_id:number,
                status:AudioClipProcessingStatusesTypes,
                lambda_attempts_left:number|null=null,
            ) : void {

                if(Object.hasOwn(this.audio_clip_processings, audio_clip_id) === false){

                    throw new Error('audio clip does not exist in store');
                }

                switch(status){

                    case 'processing': {

                        const main_text = (
                            'Event: "' +
                            getShortenedString(
                                this.audio_clip_processings[audio_clip_id].event.event_name,
                                8
                            ) +
                            '"'
                        );

                        this.audio_clip_processings[audio_clip_id].status = 'processing';
                        this.audio_clip_processings[audio_clip_id].title = 'Processing recording';
                        this.audio_clip_processings[audio_clip_id].main_text = main_text;
                        this.audio_clip_processings[audio_clip_id].lambda_attempts_left = lambda_attempts_left;
                        this.audio_clip_processings[audio_clip_id].can_close = false;

                        break;
                    }

                    case 'processed': {

                        const event_url = (
                            window.location.origin + '/event/' +
                            this.audio_clip_processings[audio_clip_id].event.id.toString()
                        );

                        const main_text = (
                            'Event: "' +
                            getShortenedString(
                                this.audio_clip_processings[audio_clip_id].event.event_name,
                                8
                            ) +
                            '"'
                        );

                        this.audio_clip_processings[audio_clip_id].status = 'processed';
                        this.audio_clip_processings[audio_clip_id].title = 'Recording processed';
                        this.audio_clip_processings[audio_clip_id].main_text = main_text;
                        this.audio_clip_processings[audio_clip_id].last_lambda_attempt = '';
                        this.audio_clip_processings[audio_clip_id].lambda_attempts_left = null;
                        this.audio_clip_processings[audio_clip_id].actions = [
                            {
                                type: 'url',
                                text: 'Open',
                                url: event_url,
                            },
                        ];
                        this.audio_clip_processings[audio_clip_id].can_close = true;

                        break;
                    }

                    case 'not_found' : {

                        const main_text = (
                            'Your recording for event "' +
                            getShortenedString(
                                this.audio_clip_processings[audio_clip_id].event.event_name,
                                8
                            ) +
                            '" could not be fixed.'
                        );

                        this.audio_clip_processings[audio_clip_id].status = 'not_found';
                        this.audio_clip_processings[audio_clip_id].title = 'Recording removed';
                        this.audio_clip_processings[audio_clip_id].main_text = main_text;
                        this.audio_clip_processings[audio_clip_id].last_lambda_attempt = '';
                        this.audio_clip_processings[audio_clip_id].lambda_attempts_left = null;
                        this.audio_clip_processings[audio_clip_id].actions = [];
                        this.audio_clip_processings[audio_clip_id].can_close = true;

                        break;
                    }

                    case 'lambda_error': {

                        const main_text = (
                            'Your recording for event "' +
                            getShortenedString(
                                this.audio_clip_processings[audio_clip_id].event.event_name,
                                8
                            ) +
                            '" has issues.'
                        );

                        this.audio_clip_processings[audio_clip_id].status = 'lambda_error';
                        this.audio_clip_processings[audio_clip_id].title = 'Recording error';
                        this.audio_clip_processings[audio_clip_id].main_text = main_text;
                        this.audio_clip_processings[audio_clip_id].last_lambda_attempt = setPiniaDateObject(new Date());
                        this.audio_clip_processings[audio_clip_id].lambda_attempts_left = lambda_attempts_left;
                        this.audio_clip_processings[audio_clip_id].actions = [
                            {
                                type: 'url',
                                text: 'Reupload',
                                url: this.determineReuploadURL(audio_clip_id),
                            },
                        ];
                        this.audio_clip_processings[audio_clip_id].can_close = true;

                        break;
                    }

                    default:

                        throw new Error('Invalid status for updateProcessing().');
                }
            },
            getReuploadAudioClipId() : number|null {

                //this is only used to verify that reupload is allowed, when user wants to reupload
                //only used at GetEventsApp, when user is at reupload-specific URL

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
            getActionButtonCallback(audio_clip_id:number, action_index:number) : (()=>void)|void {

                //not yet needed
                //just a proof of concept for action callbacks
                //since Pinia will remove callbacks on persist

                if(
                    Object.hasOwn(this.audio_clip_processings, audio_clip_id) === false ||
                    Object.hasOwn(this.audio_clip_processings[audio_clip_id], "actions") === false ||
                    this.audio_clip_processings[audio_clip_id].actions!.length < (action_index + 1) ||
                    Object.hasOwn(this.audio_clip_processings[audio_clip_id].actions![action_index], "callback_context") === false
                ){

                    return;
                }

                return ()=>{

                    if(this.audio_clip_processings[audio_clip_id].actions![action_index].callback_context === ''){
                        
                        return;
                    }

                    return;
                };
            },
            getPrettyLambdaAttemptsLeft(audio_clip_id:number) : string {

                if(Object.hasOwn(this.audio_clip_processings, audio_clip_id) === false){

                    return '';
                }

                const attempts_left = this.audio_clip_processings[audio_clip_id].lambda_attempts_left;

                if(attempts_left === null){

                    return '0 attempts left.';
                }

                if(attempts_left === 1){

                    return '1 attempt left.';
                }

                return attempts_left.toString() + ' attempts left.';
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