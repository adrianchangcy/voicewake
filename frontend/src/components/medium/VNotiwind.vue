<template>
    <!--you can create multiple groups via <NotificationGroup group="group1">, <NotificationGroup group="group2">, etc. -->
    <!--then you can do notify({group:"group1",...}, 1000)-->
    <!--you probably only need this if you want toasts at multiple places of screen-->
    <!--handles 'undefined' well by ommitting "text" value,
        i.e. when error occurs that does not return error.response.data['message']
    -->
    <!--notify({}, param2) is duration, accepts ms, and you can pass -1 for permanence, default is 3000-->
    <NotificationGroup>
        <div
            class="fixed w-full max-w-sm h-fit left-0 right-0 bottom-0 m-auto flex items-start px-6"
        >
            <div class="w-full">
                <Notification
                    v-slot="{ notifications }"
                    enter="transform ease-out duration-300 transition"
                    enter-from="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-4"
                    enter-to="translate-y-0 opacity-100 sm:translate-x-0"
                    leave="transition ease-in duration-500"
                    leave-from="opacity-100"
                    leave-to="opacity-0"
                    move="transition duration-500"
                    move-delay="delay-300"
                >
                    <div
                        class="flex w-full mx-auto mb-4 overflow-hidden backdrop-blur bg-white/60 rounded-lg shadow-xl"
                        v-for="notification in notifications"
                        :key="notification.id"
                    >
                        <!--error-->
                        <div
                            v-if="notification.type === 'error'"
                            class="flex w-full"
                        >
                            <div class="flex shrink-0 items-center justify-center w-10 bg-red-500 text-white">
                                <i class="fas fa-exclamation text-xl" aria-hidden="true"></i>
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
                                <i class="fas fa-check text-xl" aria-hidden="true"></i>
                            </div>
                            <div class="px-4 py-2">
                                <span class="text-base font-semibold text-green-500">{{ notification.title }}</span>
                                <p class="text-sm text-theme-black">{{ notification.text }}</p>
                            </div>
                        </div>
                    </div>
                </Notification>
            </div>
        </div>
    </NotificationGroup>
</template>


<script setup lang="ts">
    import {Notification, NotificationGroup} from 'notiwind';
</script>






