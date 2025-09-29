import AudioClipTonesTypes from '@/types/AudioClipTones.interface';

export type AudioClipProcessingStatusesTypes = 'processing'|'processed'|'not_found'|'lambda_error';
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
            status: AudioClipProcessingStatusesTypes,
            is_processing: boolean,
            attempts_left: number|null,
        },
    },
}
export interface AudioClipProcessingDetailsTypes{
    audio_clip_role_name: 'originator'|'responder',
    event: EventsTypes,
    audio_clip_tone: AudioClipTonesTypes,
    status: AudioClipProcessingStatusesTypes,
    last_attempt: string,
    attempts_left: number|null,
    title: string,
    main_text: string,
    can_close: boolean,
    is_closing: boolean,
    actions?: ActionsTypes[],
}