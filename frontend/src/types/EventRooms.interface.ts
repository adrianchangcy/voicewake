import EventTypes from "./Events.interface";

interface EventRoomTypes{
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
    originator: EventTypes|null,
    responder: EventTypes[]|[]
};

export default EventRoomTypes;