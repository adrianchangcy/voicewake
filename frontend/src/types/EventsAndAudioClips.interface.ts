import AudioClipsAndLikeDetailsTypes from "./AudioClipsAndLikeDetails.interface";
import EventsTypes from "./Events.interface";


interface EventsAndAudioClipsTypes{
    event: EventsTypes,
    originator: AudioClipsAndLikeDetailsTypes|null,
    responder: AudioClipsAndLikeDetailsTypes[]|[],
    //need this because RecycleScroller's keyField is not flexible for nested values
    event_id_as_scroller_index?: number,
}

export default EventsAndAudioClipsTypes;