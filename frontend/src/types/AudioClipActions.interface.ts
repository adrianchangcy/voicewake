import AudioClipsAndLikeDetailsTypes from "./AudioClipsAndLikeDetails.interface";

interface AudioClipActionsTypes{
    audio_clip: AudioClipsAndLikeDetailsTypes,
    action: 'delete'|'ban'|'report',
    api_request: ()=>Promise<void>,
    event_list_index: number|null,
}

export default AudioClipActionsTypes;