//best way to use this is to store the values you need in component
//then, with an arg with the same type as this, check via "" in this.statuses
type StatusValues = "" |
    "no_reply_choices" | "choosing_audio_clip_choice" | "choosing_audio_clip_choice_expired" |
    "replying" | "replying_successful" | "replying_expired" | "replying_deleted";

export default StatusValues;