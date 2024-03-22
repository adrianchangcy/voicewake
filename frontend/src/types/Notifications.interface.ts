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

export default interface NotificationsTypes {
    title: string,
    text: string,
    type: "ok" | "error" | "generic",
    icon: {
        //must have these icons imported at <script setup lang="ts">
        font_awesome?: "fas fa-check" | "fas fa-exclamation" |
            "fas fa-cookie-bite" | "fas fa-battery-empty" | "fas fa-flag" | "far fa-face-meh-blank" |
            "fas fa-xmark",
        audio_clip_tone?: {
            audio_clip_tone_name: string,
            audio_clip_tone_symbol: string,
        },
    },
    has_close_button?: boolean,
    close_callback?: ()=>any,
    //we assume that for good UX, max actions to show should be 2
    actions?: (ActionButtonsTypes|ActionURLsTypes)[],
}