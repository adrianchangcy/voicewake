interface AudioClipsAndLikeDetailsTypes{
    id: number,
    user: {
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
    like_count: number,
    dislike_count: number,
    is_banned: boolean,
    is_liked_by_user: boolean|null,

    previous_is_liked_by_user?: boolean|null,
}

export default AudioClipsAndLikeDetailsTypes;