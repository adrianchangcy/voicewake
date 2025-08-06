interface AudioClipsTypes{
    id: number,
    user: {
        username: string
    },
    audio_clip_role: {
        id: number,
        audio_clip_role_name: 'originator'|'responder',
    },
    audio_clip_tone: {
        id: number,
        audio_clip_tone_name: string,
        audio_clip_tone_slug: string,
        audio_clip_tone_symbol: string,
    },
    event_id: number,
    generic_status: {
        generic_status_name: 'ok'|'deleted',
    },
    audio_file: string,
    audio_duration_s: number,
    audio_volume_peaks: number[],
    is_banned: boolean,
}

export default AudioClipsTypes;