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
                    leave="transition ease-in duration-500"
                    leave-from="opacity-100"
                    leave-to="opacity-0"
                    move="transition duration-500"
                    move-delay="delay-300"
                >
                    <!--nested v-if inside v-for is bad practice-->
                    <!--but Notiwind docs show that this is how it's done for this case-->
                    <div
                        class="flex w-full mx-auto mb-4 overflow-hidden backdrop-blur bg-white/60 rounded-lg shadow-xl"
                        v-for="notification in notifications"
                        :key="notification.id"
                    >
                        <!--error-->
                        <div
                            v-if="notification.type === 'error'"
                            class="flex"
                        >
                            <div class="flex shrink-0 items-center justify-center w-10 bg-red-500 text-white">
                                <FontAwesomeIcon icon="fas fa-exclamation" class="text-xl"/>
                            </div>
                            <div class="w-full px-4 py-2">
                                <span class="text-base font-semibold text-red-500">{{ notification.title }}</span>
                                <p class="text-sm text-theme-black">{{ notification.text }}</p>
                            </div>
                        </div>                        

                        <!--ok-->
                        <div
                            v-else-if="notification.type === 'ok'"
                            class="flex"
                        >
                            <div class="flex shrink-0 items-center justify-center w-10 bg-green-500 text-white">
                                <FontAwesomeIcon icon="fas fa-check" class="text-xl"/>
                            </div>
                            <div class="px-4 py-2">
                                <span class="text-base font-semibold text-green-500">{{ notification.title }}</span>
                                <p class="text-sm text-theme-black">{{ notification.text }}</p>
                            </div>
                        </div>

                        <!--generic-->
                        <div
                            v-else-if="notification.type === 'generic'"
                            class="flex"
                        >
                            <div class="flex shrink-0 items-center justify-center w-10 bg-theme-black text-white">
                                <FontAwesomeIcon :icon="notification.icon!" class="text-xl"/>
                            </div>
                            <div class="w-full px-4 py-2 text-theme-black">
                                <span class="text-base font-semibold">{{ notification.title }}</span>
                                <p class="text-sm">{{ notification.text }}</p>
                                <div v-if="notification.button_1" class="w-full pt-2">
                                    <button
                                        @click="[(notification as ExtendedNotificationType).button_1.callback(), close(notification.id)]"
                                        type="button"
                                        class="w-full h-10 flex flex-row items-center     shade-border-when-hover active:bg-theme-gray-1 transition-colors       border border-theme-gray-2 rounded-full     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline"
                                    >
                                        <span class="px-4 pb-0.5 mx-auto text-sm font-medium">{{ (notification as ExtendedNotificationType).button_1.text }}</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </Notification>
            </div>
        </NotificationGroup>
    </Teleport>
</template>


<script setup lang="ts">
    import {Notification, NotificationGroup} from 'notiwind';

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

    library.add(faExclamation, faCheck, faCookieBite, faBatteryEmpty, faFlag, faFaceMehBlank);
</script>


<script lang="ts">
    interface ExtendedNotificationType {
        [x: string]: unknown,
        id: number,
        group: string,
        icon: string|undefined,
        button_1: {
            text: string,
            callback: () => any,
        },
    }[]
</script>





