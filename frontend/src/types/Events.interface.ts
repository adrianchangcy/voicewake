interface EventsTypes{
        id: number,
        event_name: string,
        when_created: string,
        generic_status: {
            id: number,
            generic_status_name: string,
        },
        when_locked?: string,
        is_replying?: boolean,
}

export default EventsTypes;