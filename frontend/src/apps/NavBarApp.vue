<template>
    <div class="h-full text-theme-black text-center">

        <!--main nav-->
        <nav class="h-full grid grid-cols-4 sm:grid-cols-6 lg:grid-cols-8 px-2 lg:px-8 py-2 gap-x-2 backdrop-blur bg-theme-light/60 border-b border-theme-light-gray">
            <!--home-->
            <div class="col-start-1 col-span-1">
                <VNavigationButton2 class="w-full h-full">
                    <a href="/" class="block w-full h-full relative">
                        <i class="fas fa-wave-square text-xl absolute w-fit h-fit left-0 right-0 top-0 bottom-0 m-auto"></i>
                        <span class="sr-only">home</span>
                    </a>
                </VNavigationButton2>
            </div>
            <!--start-->
            <div class="col-start-2 sm:col-start-3 lg:col-start-3 col-span-1 lg:col-span-2">
                <VNavigationButton2 class="w-full h-full">
                    <a href="/say" class="block w-full h-full relative">
                        <span class="text-lg font-medium leading-none w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto">
                            Start
                        </span>
                    </a>
                </VNavigationButton2>
            </div>
            <!--reply-->
            <div class="col-start-3 sm:col-start-4 lg:col-start-5 col-span-1 lg:col-span-2">
                <VNavigationButton2 class="w-full h-full">
                    <a href="/hear" class="block w-full h-full relative">
                        <span class="text-lg font-medium leading-none w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto">
                            Reply
                        </span>
                    </a>
                </VNavigationButton2>
            </div>
            <!--nav-burger-->
            <div
                ref="nav_main_more_mobile_button"
                class="col-start-4 sm:col-start-6 lg:col-start-8 col-span-1"
            >
                <VNavigationButton2
                    @click.stop="toggle_nav_main_more"
                    class="w-full h-full   grid grid-rows-3 grid-flow-row      justify-items-center place-items-center"
                    type="button"
                >
                    <div
                        :class="[
                            is_nav_main_more_open ? 'mb-0 rotate-45' : 'mb-4 rotate-0',
                            'nav-burger-line row-span-1 bg-theme-black absolute   w-5 h-1     transition-all duration-200 ease-in-out',
                        ]"
                    >
                    </div>
                    <div
                        :class="[
                            is_nav_main_more_open ? 'opacity-0' : 'opacity-100',
                            'nav-burger-line row-span-1 bg-theme-black absolute   w-5 h-1     transition-all duration-200 ease-in-out',
                        ]"
                    >
                    </div>
                    <div
                        :class="[
                            is_nav_main_more_open ? 'mt-0 -rotate-45' : 'mt-4 rotate-0',
                            'nav-burger-line row-span-1 bg-theme-black absolute   w-5 h-1     transition-all duration-200 ease-in-out',
                        ]"
                    >
                    </div>
                    <span class="sr-only">more navigation options</span>
                </VNavigationButton2>
            </div>
        </nav>

        <!--more nav options, following main nav grid but separated-->
        <div class="h-0 grid grid-cols-4 sm:grid-cols-6 lg:grid-cols-8 px-2 lg:px-8 gap-x-2">
            <div class="h-0 relative col-start-1 lg:col-start-7 col-span-4 sm:col-span-6 lg:col-span-2 right-0">
                <TransitionFade>
                    <div 
                        v-show="is_nav_main_more_open"
                        v-click-outside="{
                            var_name_for_element_bool_status: 'is_nav_main_more_open',
                            refs_to_exclude: ['nav_main_more_button', 'nav_main_more_mobile_button']
                        }"
                        class="absolute w-full h-screen lg:border-l border-theme-light-gray      backdrop-blur bg-theme-light/60"
                    >
                        <div class="p-4 lg:p-8 overflow-y-auto">
                            <div v-if="is_logged_in" class="p-4 grid gap-y-2">
                                <i class="col-span-1 fas fa-circle-user text-4xl"></i>
                                <p>{{username}}</p>
                            </div>
                            <div v-if="is_logged_in" class="flex flex-nowrap flex-col gap-y-2">
                                <VNavigationButton propElement="a" propUrl="/" class="w-full h-full p-4 lg:p-2">
                                    <div class="grid grid-cols-4 grid-flow-col">
                                        <i class="col-span-1 fas fa-door-open"></i>
                                        <span class="col-span-2">Logout</span>
                                    </div>
                                </VNavigationButton>
                            </div>
                            <div v-else class="flex flex-nowrap flex-col gap-y-2">
                                <VNavigationButton propElement="button" class="w-full h-full p-4 lg:p-2">
                                    <div class="grid grid-cols-4 grid-flow-col">
                                        <i class="col-span-1 fas fa-user"></i>
                                        <span class="col-span-2">Login</span>
                                    </div>
                                </VNavigationButton>
                                <VNavigationButton propElement="button" class="w-full h-full p-4 lg:p-2">
                                    <div class="grid grid-cols-4 grid-flow-col">
                                        <i class="col-span-1 fas fa-right-to-bracket"></i>
                                        <span class="col-span-2">Sign Up</span>
                                    </div>
                                </VNavigationButton>
                            </div>
                        </div>
                    </div>
                </TransitionFade>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    // import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
    import VNavigationButton from '/src/components/small/VNavigationButton.vue';
    import TransitionFade from '/src/transitions/TransitionFade.vue';
    import VNavigationButton2 from '@/components/small/VNavigationButton2.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { getUsername } from '@/helper_functions';

    export default defineComponent({
        name: 'NavBarApp',
        data(){
            return {
                is_nav_main_more_open: false,
                is_logged_in: false,
                username: "",
            };
        },
        beforeMount(){

            this.username = getUsername();

            if(this.username !== ''){

                this.is_logged_in = true;
            }
        },
        methods: {
            toggle_nav_main_more(){

                this.is_nav_main_more_open = !this.is_nav_main_more_open;
            },
        },
    });




</script>