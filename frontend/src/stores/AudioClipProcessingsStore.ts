//this store is the final step in creating audio clips
//calls for processing and manages state+notifications+retries
//this is managed more separately from the other steps during the upload
//to allow users to not wait too long, as this is the more time-consuming part

import { defineStore } from 'pinia';
import { getShortenedString, setPiniaDateObject } from '@/helper_functions';
import AudioClipTonesTypes from '@/types/AudioClipTones.interface';
import {
    BackendAudioClipProcessingGenericStatusNames,
    FrontendAudioClipProcessingStates,
    AudioClipProcessingDetailsTypes,
    ProcessingCacheTypes,
    EventsTypes,
} from '@/types/AudioClipProcessingDetails.interface';
import { notify } from '@/wrappers/notify_wrapper';

import axios from 'axios';

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

            //allows watcher to remove reply choice
            last_removable_audio_clip_id: null as number|null,

            polling_processings_timeout: null as number|null,
            polling_processings_timeout_delay_ms: 2000,

            audio_clip_unprocessed_expiry_ms: 0,

            //this is needed to show a more serious dialog at EventReplyChoicesApp
            //only one should exist at any given time
            responder_processing_audio_clip_id: null as number|null,
        }),
        getters: {
            getAudioClipProcessings: (state)=>{

                return state.audio_clip_processings;
            },
            getResponderProcessing: (state)=>{

                if(
                    state.responder_processing_audio_clip_id === null ||
                    Object.hasOwn(state.audio_clip_processings, state.responder_processing_audio_clip_id) === false
                ){

                    return null;
                }

                return state.audio_clip_processings[state.responder_processing_audio_clip_id];
            },
        },
        actions: {
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

                    const current_processing = this.getAudioClipProcessing(audio_clip_id);

                    if(current_processing === null){

                        throw new Error('Processing no longer exists.');
                    }

                    if(result.request.status !== 200){

                        throw new Error('Unhandled success request.');
                    }

                    if(
                        Object.hasOwn(result.data, 'is_processed') === true &&
                        result.data['is_processed'] === true
                    ){

                        //processed, ok

                        const new_processing = this.updateProcessing(
                            audio_clip_id,
                            current_processing,
                            'ok',
                        );

                        this.audio_clip_processings[audio_clip_id] = new_processing;
                        this.updateLastRemovableAudioClipId(audio_clip_id);

                        return;
                    }

                    if(Object.hasOwn(result.data, 'attempts_left') === true){

                        //can proceed, added to task queue

                        const new_processing = this.updateProcessing(
                            audio_clip_id,
                            current_processing,
                            'processing',
                            result.data['attempts_left']
                        );

                        this.audio_clip_processings[audio_clip_id] = new_processing;

                        return;
                    }

                    throw new Error('Unhandled success request.');

                }).catch((error:any)=>{

                    const current_processing = this.getAudioClipProcessing(audio_clip_id);

                    if(current_processing === null){

                        throw new Error('Processing no longer exists.');
                    }

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

                            const new_processing = this.updateProcessing(
                                audio_clip_id,
                                current_processing,
                                'not_found',
                            );
    
                            this.audio_clip_processings[audio_clip_id] = new_processing;

                            break;
                        }

                        case 409:

                            if(
                                Object.hasOwn(error.response.data, 'is_processing') === true &&
                                Object.hasOwn(error.response.data, 'attempts_left') === true &&
                                error.response.data['is_processing'] === true
                            ){

                                //still processing

                                const new_processing = this.updateProcessing(
                                    audio_clip_id,
                                    current_processing,
                                    'processing',
                                    error.response.data['attempts_left']
                                );
        
                                this.audio_clip_processings[audio_clip_id] = new_processing;
                                break;
                            }

                            throw new Error('Unhandled error request.');

                        default:

                            //do not delete processing at store by default, to prevent unexpected disappearance
                            //let user delete it
                            break;
                    }
                });
            },
            async syncProcessingsAPI() : Promise<void> {

                //cache only stores processing/processing_failed
                //which means if we have existing processed/not_found in this store, we do nothing to them

                //prepare URL
                const target_url = window.location.origin + '/api/audio-clips/processings/list';

                await axios.get(target_url).then((result:any)=>{

                    if(Object.hasOwn(result.data, 'data') === false){

                        throw new Error('Missing data.');
                    }

                    const processing_cache = result.data['data'] as ProcessingCacheTypes;

                    const audio_clip_ids = Object.keys(processing_cache['processings']);

                    for(let x=0; x < audio_clip_ids.length; x++){

                        const audio_clip_id = Number(audio_clip_ids[x]);

                        const processing = processing_cache['processings'][audio_clip_id];

                        const default_processing = {
                            audio_clip_role_name: processing['audio_clip_role_name'],
                            event: processing['event'],
                            audio_clip_tone: processing['audio_clip_tone'],
                            frontend_processing_state: processing['frontend_processing_state'] as BackendAudioClipProcessingGenericStatusNames,
                            last_attempt: '',
                            attempts_left: processing['attempts_left'],
                            title: '',
                            main_text: '',
                            can_close: false,
                            is_closing: false,
                            actions: [],
                        } as AudioClipProcessingDetailsTypes;

                        const new_processing = this.updateProcessing(
                            audio_clip_id,
                            default_processing,
                            processing['frontend_processing_state'] as BackendAudioClipProcessingGenericStatusNames,
                            processing['attempts_left'],
                        )

                        //once there is a responder processing, EventReplyChoicesApp can have a more accurate dialog

                        if(processing['audio_clip_role_name'] === 'responder'){

                            this.responder_processing_audio_clip_id = audio_clip_id;
                        }

                        //do nothing if already closing, which is when user no longer cares about reupload

                        if(
                            Object.hasOwn(this.audio_clip_processings, audio_clip_id) === true &&
                            this.audio_clip_processings[audio_clip_id].is_closing === true
                        ){

                            continue;
                        }

                        this.audio_clip_processings[audio_clip_id] = new_processing;
                        this.event_id_key_audio_clip_id_value[processing['event'].id] = audio_clip_id;
                    }

                }).catch((error:any)=>{

                    if(Object.hasOwn(error, "request") === false){

                        throw error;
                    }

                    //do nothing if 404 "nothing is processing", so user can manually close popups
                });
            },
            async checkProcessingStatusAPI(audio_clip_id:number) : Promise<void> {

                const current_processing = this.getAudioClipProcessing(audio_clip_id);

                if(current_processing === null){

                    throw new Error('audio clip does not exist in store');
                }

                //prepare URL
                const target_url = window.location.origin + '/api/audio-clips/processings/check/' + audio_clip_id.toString();

                //make call
                await axios.get(target_url).then((result:any)=>{

                    if(result.request.status !== 200){

                        throw new Error('Unhandled success request.');
                    }

                    if(
                        Object.hasOwn(result.data, 'is_processed') === true &&
                        result.data['is_processed'] === true
                    ){

                        //already processed

                        const new_processing = this.updateProcessing(
                            audio_clip_id,
                            current_processing,
                            'ok',
                        );

                        this.audio_clip_processings[audio_clip_id] = new_processing;
                        this.updateLastRemovableAudioClipId(audio_clip_id);

                        return;

                    }else if(
                        Object.hasOwn(result.data, 'status') === true &&
                        Object.hasOwn(result.data, 'attempts_left') === true &&
                        result.data['status'] === 'processing_failed'
                    ){

                        //not processing, i.e. failed

                        const new_processing = this.updateProcessing(
                            audio_clip_id,
                            current_processing,
                            'processing_failed',
                            result.data['attempts_left']
                        );

                        this.audio_clip_processings[audio_clip_id] = new_processing;

                        return;
                    }

                    throw new Error('Unhandled success request.');

                }).catch((error:any)=>{

                    if(Object.hasOwn(error, "request") === false){

                        throw error;
                    }

                    switch(error.request.status){

                        //don't handle 400 here, since there are no permanent 400 errors
                        //just silently retry

                        case 404:{

                            //no longer available

                            const new_processing = this.updateProcessing(
                                audio_clip_id,
                                current_processing,
                                'not_found',
                            );
    
                            this.audio_clip_processings[audio_clip_id] = new_processing;

                            break;
                        }

                        case 409:{

                            if(
                                Object.hasOwn(error.response.data, 'status') === true &&
                                Object.hasOwn(error.response.data, 'attempts_left') === true &&
                                error.response.data['status'] === 'processing'
                            ){

                                //still processing

                                const new_processing = this.updateProcessing(
                                    audio_clip_id,
                                    current_processing,
                                    'processing',
                                    error.response.data['attempts_left']
                                );

                                this.audio_clip_processings[audio_clip_id] = new_processing;

                                break;
                            }

                            throw new Error('Unhandled error request.');
                        }

                        default:

                            //do nothing
                            break;
                    }
                });
            },
            async deleteProcessingAPI(audio_clip_id:number) : Promise<void> {

                //only use this if user decides to cancel processing when it's not at its final state

                if(Object.hasOwn(this.audio_clip_processings, audio_clip_id) === false){

                    throw new Error('Missing audio_clip_id.');
                }

                this.audio_clip_processings[audio_clip_id].is_closing = true;

                //prepare URL
                const target_url = window.location.origin + '/api/audio-clips/processings/delete';

                //prepare data
                //use Number() as temporary fix for the mistake "declare key in {} as number type"
                //API will error if we JSON.stringify() a string
                const data = new FormData();
                data.append('audio_clip_id', JSON.stringify(Number(audio_clip_id)));

                //make call
                await axios.post(target_url, data).catch((error:any)=>{

                    if(Object.hasOwn(this.audio_clip_processings, audio_clip_id) === false){

                        throw new Error('Missing audio_clip_id.');
                    }

                    switch(error.request.status){

                        case 404:

                            //nothing to delete
                            //user cache deletion will happen in another function
                            return;

                        case 409:

                            //still processing
                            return;

                        default:

                            //unexpected
                            this.audio_clip_processings[audio_clip_id].is_closing = false;

                            throw error;
                    }
                });
            },
            getStaticValuesFromTemplate(data_container_element:HTMLElement) : void {

                //get essential data first, where we don't proceed if they don't exist
                const audio_clip_unprocessed_expiry_seconds = data_container_element.getAttribute('data-audio-clip-unprocessed-expiry-seconds') as string;
    
                if(audio_clip_unprocessed_expiry_seconds === null){
    
                    //don't proceed because we lack essential data
                    throw new Error('Essential data was not passed into template.');
                }
    
                //get data from SSR template
                this.audio_clip_unprocessed_expiry_ms = parseInt(audio_clip_unprocessed_expiry_seconds) * 1000;
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
            handleVCreateAudioClipsSubmitSuccess(
                passed_is_originator:boolean,
                passed_audio_clip_id:number,
                passed_event:EventsTypes,
                passed_audio_clip_tone:AudioClipTonesTypes,
            ){

                const current_processing = this.getAudioClipProcessing(passed_audio_clip_id);

                if(current_processing === null){

                    const default_processing = {
                        audio_clip_role_name: passed_is_originator === true ? 'originator' : 'responder',
                        event: passed_event,
                        audio_clip_tone: passed_audio_clip_tone,
                        frontend_processing_state: 'processing',
                        last_attempt: '',
                        attempts_left: null,
                        title: '',
                        main_text: '',
                        can_close: false,
                        is_closing: false,
                        actions: [],
                    } as AudioClipProcessingDetailsTypes;

                    this.audio_clip_processings[passed_audio_clip_id] = this.updateProcessing(
                        passed_audio_clip_id,
                        default_processing,
                        'processing',
                        null
                    );

                    this.event_id_key_audio_clip_id_value[passed_event.id] = passed_audio_clip_id;

                }else{

                    this.audio_clip_processings[passed_audio_clip_id] = this.updateProcessing(
                        passed_audio_clip_id,
                        current_processing,
                        'processing',
                        current_processing['attempts_left'],
                    );

                    this.event_id_key_audio_clip_id_value[current_processing['event'].id] = passed_audio_clip_id;
                }
            },
            async deleteAudioClipProcessing(audio_clip_id:number) : Promise<void> {

                const main_callback = ()=>{

                    this.updateLastRemovableAudioClipId(audio_clip_id);

                    if(audio_clip_id === this.responder_processing_audio_clip_id){

                        this.responder_processing_audio_clip_id = null;
                    }

                    delete this.audio_clip_processings[audio_clip_id];

                    const event_ids = Object.keys(this.event_id_key_audio_clip_id_value);
                    const audio_clip_ids = Object.values(this.event_id_key_audio_clip_id_value);
    
                    const event_id_index = audio_clip_ids.indexOf(audio_clip_id);
    
                    if(event_id_index === -1){
    
                        return;
                    }

                    delete this.event_id_key_audio_clip_id_value[Number(event_ids[event_id_index])];
                };

                //if processing is at last unchangeable state, no need to call deleteProcessingAPI

                const target_processing = this.getAudioClipProcessing(audio_clip_id);

                if(
                    target_processing !== null &&
                    (
                        target_processing.frontend_processing_state === 'not_found' ||
                        target_processing.frontend_processing_state === 'ok'
                    )
                ){

                    main_callback();

                }else{

                    //processing is not at last unchangeable state, so delete everything

                    await this.deleteProcessingAPI(audio_clip_id).then(()=>{

                        //deleted something in db
                        main_callback();

                    }).catch(()=>{

                        notify({
                            title: 'Deletion error',
                            text: "Unexpectedly unable to delete reupload message. Try again later.",
                            type: 'error',
                        }, 4000);
                    });
                }
            },
            determineReuploadURL(event_id:number, audio_clip_id:number) : string {

                let final_url = window.location.origin;

                final_url += '/event/' + event_id.toString();
                final_url += '?reupload=' + audio_clip_id.toString();

                return final_url;
            },
            updateLastRemovableAudioClipId(audio_clip_id:number) : void {

                this.last_removable_audio_clip_id = audio_clip_id;
            },
            startPollingProcessings() : void {

                //be sure to sync store first before calling this
                //only check for those with statuses that have potential to change, i.e. "processing", "processing_failed"

                this.polling_processings_timeout = window.setTimeout(async ()=>{

                    const audio_clip_ids = Object.keys(this.audio_clip_processings);

                    const all_api_calls = [] as Promise<any>[];

                    for(let x=0; x < audio_clip_ids.length; x++){

                        const audio_clip_id = Number(audio_clip_ids[x]);

                        if(
                            this.audio_clip_processings[audio_clip_id].frontend_processing_state === 'processing_failed' ||
                            this.audio_clip_processings[audio_clip_id].frontend_processing_state === 'processing'
                        ){

                            all_api_calls.push(this.checkProcessingStatusAPI(audio_clip_id));
                        }
                    }

                    await Promise.allSettled(all_api_calls).finally(()=>{

                        this.startPollingProcessings();
                    });

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
                processing:AudioClipProcessingDetailsTypes,
                frontend_processing_state:FrontendAudioClipProcessingStates,
                attempts_left:number|null=null,
            ) : AudioClipProcessingDetailsTypes {

                switch(frontend_processing_state){

                    case 'processing': {

                        const main_text = (
                            'Event: "' +
                            getShortenedString(
                                processing.event.event_name,
                                8
                            ) +
                            '"'
                        );

                        processing.frontend_processing_state = 'processing';
                        processing.title = 'Processing recording';
                        processing.main_text = main_text;
                        processing.last_attempt = setPiniaDateObject(new Date());
                        processing.attempts_left = attempts_left;
                        processing.can_close = false;

                        return processing;
                    }

                    case 'ok': {

                        const event_url = (
                            window.location.origin + '/event/' +
                            processing.event.id.toString()
                        );

                        const main_text = (
                            'Event: "' +
                            getShortenedString(
                                processing.event.event_name,
                                8
                            ) +
                            '"'
                        );

                        processing.frontend_processing_state = 'ok';
                        processing.title = 'Recording processed';
                        processing.main_text = main_text;
                        processing.last_attempt = '';
                        processing.attempts_left = null;
                        processing.actions = [
                            {
                                type: 'url',
                                text: 'Open',
                                url: event_url,
                            },
                        ];
                        processing.can_close = true;

                        return processing;
                    }

                    case 'not_found' : {

                        const main_text = (
                            'Your recording for event "' +
                            getShortenedString(
                                processing.event.event_name,
                                8
                            ) +
                            '" could not be fixed.'
                        );

                        processing.frontend_processing_state = 'not_found';
                        processing.title = 'Recording removed';
                        processing.main_text = main_text;
                        processing.last_attempt = '';
                        processing.attempts_left = null;
                        processing.actions = [];
                        processing.can_close = true;

                        return processing;
                    }

                    case 'processing_failed': {

                        const main_text = (
                            'Your recording for event "' +
                            getShortenedString(
                                processing.event.event_name,
                                8
                            ) +
                            '" has issues.'
                        );

                        processing.frontend_processing_state = 'processing_failed';
                        processing.title = 'Recording error';
                        processing.main_text = main_text;
                        processing.attempts_left = attempts_left;
                        processing.actions = [
                            {
                                type: 'url',
                                text: 'Reupload',
                                url: this.determineReuploadURL(
                                    processing['event'].id,
                                    audio_clip_id
                                ),
                            },
                        ];
                        processing.can_close = true;

                        return processing;
                    }

                    default:

                        throw new Error('Invalid status for updateProcessing().');
                }
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

                const attempts_left = this.audio_clip_processings[audio_clip_id].attempts_left;

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