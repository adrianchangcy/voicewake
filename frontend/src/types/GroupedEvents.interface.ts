import EventsAndLikeDetailsTypes from "./EventsAndLikeDetails.interface";

interface GroupedEventsTypes{
    event_room: {
        id: number,
        event_room_name: string,
        when_created: string,
        generic_status: {
            id: number,
            generic_status_name: string,
        },
        when_locked: string|null,
        locked_for_user: {
            id: number,
            username: string
        }|null,
        is_replying: boolean|null,
    },
    originator: EventsAndLikeDetailsTypes|null,
    responder: EventsAndLikeDetailsTypes[]|[]
};

export default GroupedEventsTypes;