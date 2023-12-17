import AudioClipsTypes from "./AudioClips.interface";

interface AudioClipsAndLikeDetailsTypes extends AudioClipsTypes {
    like_count: number,
    dislike_count: number,
    is_liked_by_user: boolean|null,

    previous_is_liked_by_user?: boolean|null,
}

export default AudioClipsAndLikeDetailsTypes;