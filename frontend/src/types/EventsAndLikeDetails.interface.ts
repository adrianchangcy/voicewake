interface EventsAndLikeDetailsTypes{
    id: number,
    user: {
        username: string
    },
    event_role: {
        id: number,
        event_role_name: string
    },
    event_tone: {
        id: number,
        event_tone_name: string,
        event_tone_slug: string,
        event_tone_symbol: string
    },
    event_room_id: number,
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
    is_liked_by_user: boolean|null
}

export default EventsAndLikeDetailsTypes;