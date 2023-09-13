import EventTonesTypes from "./EventTones.interface"

interface FilteredGroupedEventsStoreNewLikeDislikeTypes{
    selected_event_tone: EventTonesTypes|null,
    current_filter_type_index: number,
    event_room_index: number|null,
    event_role_name: "originator"|"responder",
    event_index: number|null,
    is_liked: boolean|null
};

export default FilteredGroupedEventsStoreNewLikeDislikeTypes;