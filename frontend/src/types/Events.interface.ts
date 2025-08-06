interface EventsTypes{
        id: number,
        event_name: string,
        when_created: string,
        generic_status: {
            generic_status_name: 'incomplete'|'completed'|'deleted',
        },
}

export default EventsTypes;