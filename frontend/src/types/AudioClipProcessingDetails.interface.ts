import AudioClipTonesTypes from '@/types/AudioClipTones.interface';

export type BackendAudioClipProcessingGenericStatusNames = 'processing_pending'|'processing'|'processing_failed';
export type FrontendAudioClipProcessingStates = BackendAudioClipProcessingGenericStatusNames|'ok'|'not_found';
export interface EventsTypes{
    id:number,
    event_name: string,
}
export interface ActionsTypes{
    type: "button"|"url",
    text: string,
    url?: string,
    callback_context?: '',  //at VAudioClipProcessings, have a function return a callback that evaluates this
}
export interface ProcessingCacheTypes{
    processings: {
        [audio_clip_id:number]: {
            audio_clip_role_name: 'originator'|'responder',
            event: EventsTypes,
            audio_clip_tone: AudioClipTonesTypes,
            status: BackendAudioClipProcessingGenericStatusNames,
            attempts_left: number|null,
        },
    },
}
export interface AudioClipProcessingDetailsTypes{
    audio_clip_role_name: 'originator'|'responder',
    event: EventsTypes,
    audio_clip_tone: AudioClipTonesTypes,
    frontend_processing_state: FrontendAudioClipProcessingStates,
    last_attempt: string,
    attempts_left: number|null,
    title: string,
    main_text: string,
    can_close: boolean,
    is_closing: boolean,
    actions?: ActionsTypes[],
}