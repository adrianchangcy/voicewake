<template>
    <!--you can create multiple groups via <NotificationGroup group="group1">, <NotificationGroup group="group2">, etc. -->
    <!--then you can do notify({group:"group1",...}, 1000)-->
    <!--you probably only need this if you want toasts at multiple places of screen-->
    <!--handles 'undefined' well by ommitting "text" value,
        i.e. when error occurs that does not return error.response.data['message']
    -->
    <!--notify({}, param2) is duration, accepts ms, and you can pass -1 for permanence, default is 3000-->
    <Teleport to="#notiwind-target">
        <NotificationGroup>
            <div class="w-full">
                <Notification
                    v-slot="{ notifications, close }"
                    enter="transform ease-out duration-300 transition"
                    enter-from="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-4"
                    enter-to="translate-y-0 opacity-100 sm:translate-x-0"
                    leave="transition ease-in duration-150"
                    leave-from="opacity-100"
                    leave-to="opacity-0"
                    move="transition duration-150"
                    move-delay="delay-300"
                >
                    <!--nested v-if inside v-for is bad practice-->
                    <!--but Notiwind docs show that this is how it's done for this case-->
                    <div
                        class="flex w-full mx-auto mb-4 overflow-hidden backdrop-blur bg-white/60 rounded-lg shadow-xl"
                        v-for="notification in (notifications as FullNotificationsTypes[])"
                        :key="notification.id"
                    >

                        <div class="w-full flex">

                            <!--left panel-->
                            <div
                                :class="[
                                    notification.type === 'ok' ? 'bg-green-500' : '',
                                    notification.type === 'error' ? 'bg-red-500' : '',
                                    notification.type === 'generic' ? 'bg-theme-black' : '',
                                    'w-10 shrink-0 flex flex-col items-center justify-center text-white text-xl'
                                ]"
                            >
                                <span v-if="hasIcon(notification, 'font_awesome')">
                                    <FontAwesomeIcon :icon="notification.icon!.font_awesome!" class="text-xl"/>
                                </span>
                                <span v-else-if="hasIcon(notification, 'audio_clip_tone')">
                                    <span class="sr-only">
                                        {{ notification.icon!.audio_clip_tone!.audio_clip_tone_name }}
                                    </span>
                                    <span>
                                        {{ notification.icon!.audio_clip_tone!.audio_clip_tone_symbol }}
                                    </span>
                                </span>
                            </div>

                            <!--middle panel-->
                            <!--when hasActions() === false, padding is to balance title's translate-->
                            <div
                                :class="[
                                    hasCloseButton(notification) ? 'pl-4' : 'px-4',
                                    hasActions(notification) ? 'pb-4' : 'pb-0.5',
                                    'flex-1'
                                ]"
                            >
                                <!--title, aligning to 'close' button-->
                                <div class="w-full h-10 flex items-center">
                                    <span
                                        :class="[
                                            notification.type === 'ok' ? 'text-green-700' : '',
                                            notification.type === 'error' ? 'text-red-700' : '',
                                            notification.type === 'generic' ? 'text-theme-black' : '',
                                            'text-base font-semibold pb-0.5 break-words'
                                        ]"
                                    >
                                        {{ notification.title }}
                                    </span>
                                </div>

                                <!--text and actions-->
                                <!--translate back into title's space-->
                                <!--translate conveniently lets us skip padding-top on actions-->
                                <span class="block text-sm -translate-y-2 break-words">
                                    {{ notification.text }}
                                </span>
                                <div
                                    v-if="hasActions(notification)"
                                    :class="[
                                        notification.actions!.length === 2 ? 'grid-cols-2' : 'grid-cols-1',
                                        'grid grid-rows-1 gap-1'
                                    ]"
                                >
                                    <div
                                        v-for="action in notification.actions" :key="action.style"
                                        class="row-start-1 col-span-1 h-10"
                                    >
                                        <a
                                            v-if="action.type === 'url'"
                                            :href="action.url"
                                            :class="[
                                                action.style === 'primary' ? 'bg-theme-black active:brightness-75 darken-when-hover text-theme-light' : 'border border-theme-gray-2 shade-border-when-hover active:bg-theme-gray-1',
                                                'w-full h-full flex flex-row items-center rounded-full transition       focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline'
                                            ]"
                                        >
                                            <span class="px-4 pb-0.5 mx-auto text-sm font-medium">
                                                {{ action.text }}
                                            </span>
                                        </a>
                                        <button
                                            v-else-if="action.type === 'button'"
                                            @click="hasActionCallback(action) ? action.callback!() : null"
                                            type="button"
                                            :class="[
                                                action.style === 'primary' ? 'bg-theme-black active:brightness-75 darken-when-hover text-theme-light' : 'border border-theme-gray-2 shade-border-when-hover active:bg-theme-gray-1',
                                                'w-full h-full flex flex-row items-center rounded-full transition       focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline'
                                            ]"
                                        >
                                            <span class="px-4 pb-0.5 mx-auto text-sm font-medium">
                                                {{ action.text }}
                                            </span>
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <!--right panel-->
                            <VActionText
                                v-if="hasCloseButton(notification)"
                                @click="[
                                    close(notification.id),
                                    hasCloseCallback(notification) ? notification.close_callback!() : null
                                ]"
                                prop-element="button"
                                prop-element-size="s"
                                :prop-is-icon-only="true"
                                class="w-10 h-10 shrink-0 flex items-center justify-center focus-visible:-outline-offset-4"
                            >
                                <FontAwesomeIcon icon="fas fa-xmark" class="text-xl mx-auto"/>
                            </VActionText>
                        </div>
                    </div>
                </Notification>
            </div>
        </NotificationGroup>
    </Teleport>
</template>


<script setup lang="ts">
    import {Notification, NotificationGroup} from 'notiwind';
    import VActionText from '../small/VActionText.vue';

    //this is for notify({icon: "..."}) when allowed to specify
    //search for "icon: ..." folder-wide and import all of it here in advance
    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faExclamation } from '@fortawesome/free-solid-svg-icons/faExclamation';
    import { faCheck } from '@fortawesome/free-solid-svg-icons/faCheck';
    import { faCookieBite } from '@fortawesome/free-solid-svg-icons/faCookieBite';
    import { faBatteryEmpty } from '@fortawesome/free-solid-svg-icons/faBatteryEmpty';
    import { faFlag } from '@fortawesome/free-solid-svg-icons/faFlag';
    import { faFaceMehBlank } from '@fortawesome/free-regular-svg-icons/faFaceMehBlank';
    import { faXmark } from '@fortawesome/free-solid-svg-icons/faXmark';

    //remember to update Notifications.interface.ts
    library.add(
        faExclamation, faCheck, faCookieBite,
        faBatteryEmpty, faFlag, faFaceMehBlank, faXmark,
    );

    const hasCloseButton = (notification:NotificationsTypes)=>{
        return (
            Object.hasOwn(notification, 'has_close_button') === true &&
            notification.has_close_button === true
        );
    }

    const hasCloseCallback = (notification:NotificationsTypes)=>{
        return Object.hasOwn(notification, 'close_callback') === true;
    }

    const hasActions = (notification:NotificationsTypes)=>{
        return (
            Object.hasOwn(notification, 'actions') === true &&
            Array.isArray(notification.actions) === true
        );
    }

    const hasActionCallback = (action:{callback?:()=>any})=>{
        return (
            Object.hasOwn(action, 'callback') === true
        );
    }

    const hasIcon = (notification:NotificationsTypes, icon_type:"font_awesome"|"audio_clip_tone")=>{
        return (
            Object.hasOwn(notification, 'icon') === true &&
            Object.hasOwn(notification.icon, icon_type) === true
        )
    };

</script>


<script lang="ts">
    import NotificationsTypes from '@/types/Notifications.interface';
    
    interface FullNotificationsTypes extends NotificationsTypes {
        [x: string]: unknown,
        id: number,
        group: string,
    }

</script>





