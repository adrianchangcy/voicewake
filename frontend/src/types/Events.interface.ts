interface EventsTypes{
        id: number,
        event_name: string,
        when_created: string,
        generic_status: {
            id: number,
            generic_status_name: string,
        },
}

export default EventsTypes;