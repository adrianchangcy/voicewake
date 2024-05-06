import AudioClipProcessingStatusesTypes from '@/types/values/AudioClipProcessingStatuses';
import AudioClipTonesTypes from '@/types/AudioClipTones.interface';

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
export interface AudioClipProcessingDetailsTypes{
    audio_clip_role_name: 'originator'|'responder',
    event: EventsTypes,
    audio_clip_tone: AudioClipTonesTypes,
    status: AudioClipProcessingStatusesTypes,
    last_lambda_attempt: string,
    lambda_attempts_left: number|null,
    title: string,
    main_text: string,
    can_close: boolean,
    actions?: ActionsTypes[],
}