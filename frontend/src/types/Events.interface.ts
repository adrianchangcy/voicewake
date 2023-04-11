interface EventTypes{
    id: number,
    generic_status: {
        id: number,
        generic_status_name: string,
    },
    event_tone: {
        id: number,
        event_tone_name: string,
        event_tone_symbol: string
    },
    audio_file: string,
    audio_volume_peaks: number[],
    user_event_role: {
        id: number,
        user: {
            id: number,
            username: string
        },
        event_role: {
            id: number,
            event_role_name: 'originator'|'responder',
        },
    },
    event_room: {
        id: number,
        event_room_name: string,
        when_locked: string|null,
        when_created: string,
        generic_status: {
            id: number,
            generic_status_name: string,
        },
        locked_for_user: number|null
    },
    like_count: number,
    dislike_count: number,
    is_liked_by_user: boolean|null
};

export default EventTypes;