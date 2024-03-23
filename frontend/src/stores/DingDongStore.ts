import { defineStore } from 'pinia';
import AudioClipTonesTypes from '@/types/AudioClipTones.interface';
import AudioClipProcessingStatusesTypes from '@/types/values/AudioClipProcessingStatuses';



//an object, i.e. processing, can always change its state
//to account for this, processing:notification must always be 1:1 per page/tab
    //otherwise, if using notify(), it becomes 1:++
        //it gets confusing when old + new states show up together



interface EventsTypes{
    id:number,
    event_name: string,
}
interface ActionURLTypes{
    url: string,
    text: string,
}
interface ProcessingDetailsTypes {
    status: AudioClipProcessingStatusesTypes,
    can_poll: boolean,
    is_originator: boolean,
    event: EventsTypes,
    audio_clip_tone: AudioClipTonesTypes,
    action_url: ActionURLTypes|null,
    close_callback: ()=>void,
}
interface ProcessingsTypes {
    [audio_clip_id:number]: ProcessingDetailsTypes
}

export const useDingDongStore = defineStore('dingdong_store', {
    state: ()=>({
        processings: {} as ProcessingsTypes,
    }),
    getters: {
        getProcessings: (state) => {
            return state.processings;
        },
    },
    actions: {
        getProcessing(audio_clip_id:number) : ProcessingDetailsTypes | null {

            if(Object.hasOwn(this.processings, audio_clip_id) === false){

                return null;
            }

            return this.processings[audio_clip_id];
        },
        storeProcessing(
            passed_audio_clip_id:number,
            passed_is_originator:boolean,
            passed_event:EventsTypes,
            passed_audio_clip_tone:AudioClipTonesTypes
        ) : void {

            if(this.getProcessing(passed_audio_clip_id) !== null){

                return;
            }

            this.processings[passed_audio_clip_id] = {
                status: 'processing',
                can_poll: true,
                is_originator: passed_is_originator,
                event: passed_event,
                audio_clip_tone: passed_audio_clip_tone,
                action_url: null,
                close_callback: ()=>{
                    this.deleteProcessing(passed_audio_clip_id);
                },
            };
        },
        deleteProcessing(audio_clip_id:number) : void {

            //will not throw exception if it does not exist
            delete this.processings[audio_clip_id];
        },
    },
    //all things considered, we get overall better usability with persistence than without
    persist: false,
    share: {
        //array of fields that the plugin will ignore
        omit: [],
        //override global config for this store
        enable: true,
        initialize: false,
    },
});