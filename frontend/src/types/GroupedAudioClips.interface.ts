import AudioClipsAndLikeDetailsTypes from "./AudioClipsAndLikeDetails.interface";

interface GroupedAudioClipsTypes{
    event: {
        id: number,
        event_name: string,
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
    originator: AudioClipsAndLikeDetailsTypes|null,
    responder: AudioClipsAndLikeDetailsTypes[]|[]
}

export default GroupedAudioClipsTypes;