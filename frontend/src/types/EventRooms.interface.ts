import EventTypes from "./Events.interface";

interface EventRoomTypes{
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
    originator: EventTypes,
    responder: EventTypes[]
};

export default EventRoomTypes;