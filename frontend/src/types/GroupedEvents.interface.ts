import EventAndLikeDetailsTypes from "./EventAndLikeDetails.interface";

interface GroupedEventsTypes{
    event_room: {
        id: number,
        event_room_name: string,
        when_created: string,
        generic_status: {
            id: number,
            generic_status_name: string,
        },
        when_locked: string,
        locked_for_user: {
            id: number,
            username: string
        },
        is_replying: boolean,
    },
    originator: EventAndLikeDetailsTypes|null,
    responder: EventAndLikeDetailsTypes[]|[]
};

export default GroupedEventsTypes;