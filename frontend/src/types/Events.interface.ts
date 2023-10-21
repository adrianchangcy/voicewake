interface EventsTypes{
    id: number,
    user: {
        id: number,
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
    is_banned: boolean,
}

export default EventsTypes;