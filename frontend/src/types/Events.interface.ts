interface EventTypes{
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
    event_room: {
        id: number,
        generic_status: {
            id: number,
            generic_status_name: string
        },
        locked_for_user: {
            id: number,
            username: string
        }|null,
        created_by: {
            id: number,
            username: string
        },
        event_room_name: string,
        when_locked: string|null,
        is_replying: boolean|null,
        when_created: string,
        last_modified: string
    },
    generic_status: {
        id: number,
        generic_status_name: string
    },
    audio_file: string,
    audio_file_seconds: number,
    audio_volume_peaks: number[],
    like_count: number,
    dislike_count: number,
    is_liked_by_user: boolean|null
};

export default EventTypes;