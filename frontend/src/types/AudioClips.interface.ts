interface AudioClipsTypes{
    id: number,
    user: {
        id: number,
        username: string
    },
    audio_clip_role: {
        id: number,
        audio_clip_role_name: string
    },
    audio_clip_tone: {
        id: number,
        audio_clip_tone_name: string,
        audio_clip_tone_slug: string,
        audio_clip_tone_symbol: string
    },
    event_id: number,
    generic_status: {
        id: number,
        generic_status_name: string
    },
    audio_file: string,
    audio_duration_s: number,
    audio_volume_peaks: number[],
    is_banned: boolean,
}

export default AudioClipsTypes;