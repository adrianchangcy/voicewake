interface BaseActionsTypes {
    style: "primary" | "secondary",
    text: string,
}
interface ActionButtonsTypes extends BaseActionsTypes {
    type: "button",
    callback?: ()=>any,
}
interface ActionURLsTypes extends BaseActionsTypes {
    type: "url",
    url?: string,
}

//must have these icons imported at <script setup lang="ts">
export type FontAwesomeIconTypes = {
    font_awesome: "fas fa-check" | "fas fa-exclamation" |
    "fas fa-cookie-bite" | "fas fa-battery-empty" | "fas fa-flag" | "far fa-face-meh-blank" |
    "fas fa-xmark",
}

export type AudioClipToneIconTypes = {
    audio_clip_tone: {
        audio_clip_tone_name: string,
        audio_clip_tone_symbol: string
    }
}

export default interface NotificationsTypes {
    title: string,
    text: string,
    type: "ok" | "error" | "generic",
    //omit "icon" to use defaults, e.g. for types "ok"/"error"/etc.
    //specify icon:null to not use icons
    icon?: null|FontAwesomeIconTypes|AudioClipToneIconTypes,
    has_close_button?: boolean,
    close_callback?: ()=>any,
    //we assume that for good UX, max actions to show should be 2
    actions?: (ActionButtonsTypes|ActionURLsTypes)[],
}