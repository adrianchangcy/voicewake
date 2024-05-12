import { defineStore } from 'pinia';
import EventsAndAudioClipsTypes from '@/types/EventsAndAudioClips.interface';
import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';
import AudioClipTonesTypes from '@/types/AudioClipTones.interface';
import { notify } from '@/wrappers/notify_wrapper';

const axios = require('axios');


type CurrentStatuses = ""|"no_new_event_reply_choices"|"event_reply_choices_expired"|
    "reply_cancelled"|"reply_expired"|"event_reply_daily_limit_reached";


//this store resets when user logs out, since this is user-specific

export const useEventReplyChoicesStore = defineStore('event_reply_choices', {
    state: ()=>({
        event_reply_choices: [] as EventsAndAudioClipsTypes[],
        replying_event: null as EventsAndAudioClipsTypes|null,

        shared_dialog_context: "" as CurrentStatuses,

        event_reply_choice_expiry_ms: 0,   //will be replaced with SSR data on beforeMount()
        event_reply_expiry_ms: 0,   //will be replaced with SSR data on beforeMount()
    }),    
    getters: {
        isReplying: (state)=>{

            return state.replying_event !== null;
        },
        getMainEvent: (state)=>{

            if(state.event_reply_choices.length > 0){

                return state.event_reply_choices[0];

            }else if(state.replying_event !== null){

                return state.replying_event;

            }else{

                return null;
            }
        },
        getEventReplyChoices: (state)=>{

            return state.event_reply_choices;
        },
        getReplyingEvent: (state)=>{

            return state.replying_event;
        },
        getReplyingEventId: (state)=>{

            if(state.replying_event === null){

                return null;
            }

            return state.replying_event.event.id;
        },
        getSharedDialogContext: (state)=>{

            return state.shared_dialog_context;
        },
        hasEventReplyChoices: (state)=>{

            return state.event_reply_choices.length > 0;
        },
        getReplyingEventURL: (state)=>{

            if(state.replying_event === null){

                return '';
            }
            return window.location.origin + '/event/' + state.replying_event.event.id;
        },
    },
    actions: {
        checkIsReplying(event_id:number) : boolean {

            return this.replying_event !== null && this.replying_event.event.id === event_id;
        },
        getStaticValuesFromTemplate(data_container_element:HTMLElement) : void {

            //get essential data first, where we don't proceed if they don't exist
            const event_reply_choice_expiry_seconds = (data_container_element.getAttribute('data-event-reply-choice-expiry-seconds') as string);
            const event_reply_expiry_seconds = (data_container_element.getAttribute('data-event-reply-expiry-seconds') as string);

            if(event_reply_choice_expiry_seconds === null || event_reply_expiry_seconds === null){

                //don't proceed because we lack essential data
                throw new Error('Essential data was not passed into template.');
            }

            //get data from SSR template
            this.event_reply_choice_expiry_ms = parseInt(event_reply_choice_expiry_seconds) * 1000;
            this.event_reply_expiry_ms = parseInt(event_reply_expiry_seconds) * 1000;
        },
        updateSharedDialogContext(shared_dialog_context:CurrentStatuses) : void {

            this.shared_dialog_context = shared_dialog_context;
        },
        newAudioClipIsLiked(
            new_value:{audio_clip:AudioClipsAndLikeDetailsTypes, new_is_liked:boolean|null}
        ) : void {

            //since objects are passed by reference, just pass the audio_clip here

            //only call this on API success, instead of following user's spam clicks
            //because on failure, this will be the source of truth, while server is the ultimate source
            //if you'd like to ensure 100% accuracy, maybe a log-and-retry request at storage can do

            switch(new_value.new_is_liked){

                case true:
        
                    if(new_value.audio_clip.is_liked_by_user === false){
        
                        new_value.audio_clip.dislike_count -= 1;
                    }
        
                    if(new_value.audio_clip.is_liked_by_user !== true){
        
                        new_value.audio_clip.like_count += 1;
                    }
        
                    break;
        
                case null:
        
                    switch(new_value.audio_clip.is_liked_by_user){
                        case true:
                            new_value.audio_clip.like_count -= 1;
                            break;
                        case false:
                            new_value.audio_clip.dislike_count -= 1;
                            break;
                        default:
                            break;
                    }
        
                    break;
        
                case false:
        
                    if(new_value.audio_clip.is_liked_by_user === true){
        
                        new_value.audio_clip.like_count -= 1;
                    }
        
                    if(new_value.audio_clip.is_liked_by_user !== false){
        
                        new_value.audio_clip.dislike_count += 1;
                    }
        
                    break;
        
                default:
        
                    break;
            }
        
            new_value.audio_clip.previous_is_liked_by_user = new_value.audio_clip.is_liked_by_user;
            new_value.audio_clip.is_liked_by_user = new_value.new_is_liked;
        },
        async queueNextEventReplyChoices(audio_clip_tone:AudioClipTonesTypes|null, unlock_all_locked_events:boolean) : Promise<void> {

            //if is first time, we pass unlock_all_locked_events=false
            //this allows us to get previous choices or currently replying events

            this.softReset();

            const data = new FormData();

            //id at db starts from 1
            if(audio_clip_tone !== null){

                data.append(
                    'audio_clip_tone_id',
                    JSON.stringify(audio_clip_tone.id)
                );
            }

            //for first List page visit, we get any replying events or any existing choices
            data.append(
                'unlock_all_locked_events',
                JSON.stringify(unlock_all_locked_events)
            );

            await axios.post(window.location.origin + "/api/events/replies/choices/list", data)
            .then((result:any) => {

                if(result.data["data"].length > 0){

                    this.event_reply_choices = result.data['data'];
                    this.updateSharedDialogContext('');

                }else if(result.data["data"].length === 0){

                    this.event_reply_choices = [];
                    this.updateSharedDialogContext('no_new_event_reply_choices');
                }

            }).catch((error:any) => {

                if(
                    Object.hasOwn(error, 'request') === false ||
                    Object.hasOwn(error, 'response') === false
                ){

                    return;
                }

                if(Object.hasOwn(error.response.data, 'event_reply_daily_limit_reached') === true){

                    this.updateSharedDialogContext('event_reply_daily_limit_reached');

                    notify({
                        title: 'Reply limit reached',
                        text: error.response.data['message'],
                        type: 'generic',
                        icon: {'font_awesome': 'fas fa-battery-empty'},
                    }, 4000);

                    return;
                }

                notify({
                    title: 'Error',
                    text: error.response.data['message'],
                    type: 'error',
                    icon: {'font_awesome': 'fas fa-exclamation'},
                }, 3000);
            });
        },
        async confirmEventReplyChoice(index:number) : Promise<void> {

            //store selected event to replying_event
            //update when_locked here, as server will also do the same, so no refetch is needed

            if(this.replying_event !== null){

                throw new Error('Cannot confirm when replying_event is not null.');
            }

            const data = new FormData();

            data.append("event_id", JSON.stringify(this.event_reply_choices[index].event.id));

            await axios.post(window.location.origin + "/api/events/replies/start", data)
            .then((result:any) => {

                //add event_reply_queue to event, and save

                if(Object.hasOwn(result.data, 'data') === false){

                    throw new Error("Missing 'data' key.");
                }

                //receives event_reply_queue as-is, not [{}]
                this.event_reply_choices[index].event_reply_queue = result.data['data'];

                this.replying_event = this.event_reply_choices[index];

                this.event_reply_choices = [];

            }).catch((error:any) => {

                if(
                    Object.hasOwn(error, 'request') === false ||
                    Object.hasOwn(error, 'response') === false
                ){

                    return;
                }

                //if we get can_retry=false, we must move on

                if(
                    Object.hasOwn(error.response.data, 'can_retry') === true &&
                    error.response.data['can_retry'] === false
                ){

                    this.softReset();

                    notify({
                        title: 'Reply choice skipped',
                        text: "The event was unexpectedly unavailable.",
                        type: 'generic',
                        icon: {'font_awesome': 'far fa-face-meh-blank'},
                    }, 4000);

                    return;
                }

                notify({
                    title: 'Error',
                    text: error.response.data['message'],
                    type: 'error',
                    icon: {'font_awesome': 'fas fa-exclamation'},
                }, 3000);
            });
        },
        async cancelEvent(is_replying:boolean, to_expire:boolean=true) : Promise<void> {

            if(
                (is_replying === true && this.replying_event === null) ||
                (is_replying === false && this.event_reply_choices.length === 0)
            ){

                return;
            }

            //currently only one event_reply_choices
            //no need to call this if user searches for more choices
                //in that case, backend cancels for us

            const data = new FormData();

            if(is_replying === true && this.replying_event !== null){

                data.append('event_id', JSON.stringify(this.replying_event.event.id));

            }else if(is_replying === false && this.event_reply_choices.length === 1){

                data.append('event_id', JSON.stringify(this.event_reply_choices[0].event.id));
            }

            await axios.post(window.location.origin + '/api/events/replies/cancel', data)
            .then(() => {

                this.softReset();

                if(to_expire === true){

                    this.updateSharedDialogContext(
                        is_replying === true ? 'reply_expired' : 'event_reply_choices_expired'
                    );

                }else{

                    this.updateSharedDialogContext('reply_cancelled');
                }

            }).catch((error:any) => {

                if(
                    Object.hasOwn(error, 'request') === false ||
                    Object.hasOwn(error, 'response') === false
                ){

                    throw error;
                }

                //if we get can_retry=false, we must move on

                if(
                    error.request.status === 404 &&
                    Object.hasOwn(error.response.data, 'can_retry') === true &&
                    error.response.data['can_retry'] === false
                ){

                    this.softReset();

                    notify({
                        title: 'Reply choice removed',
                        text: "The event is no longer unavailable.",
                        type: 'generic',
                        icon: {'font_awesome': 'far fa-face-meh-blank'},
                    }, 3000);

                    return;
                }

                notify({
                    title: 'Unexpected error',
                    text: "Try again later.",
                    type: 'error',
                    icon: {'font_awesome': 'fas fa-exclamation'},
                }, 3000);
            });
        },
        updateReplyingEvent(replying_event:EventsAndAudioClipsTypes|null) : void {

            if(replying_event === null){

                this.replying_event = null;

            }else if(
                Object.hasOwn(replying_event, 'event_reply_queue') === true &&
                replying_event.event_reply_queue!.is_replying === true
            ){

                //use this when replying_event does not exist and is retrieved from GetEventsApp
                this.replying_event = replying_event;
            }
        },
        softReset() : void {

            this.event_reply_choices = [];
            this.replying_event = null;

            this.shared_dialog_context = "";
        },
    },
    persist: {
        paths: ['event_reply_choices', 'replying_event'],
    },
    share: {
        //array of fields that the plugin will ignore
        omit: [],
        //override global config for this store
        enable: true,
        initialize: false,
    },
});