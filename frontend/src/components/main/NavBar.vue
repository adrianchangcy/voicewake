<template>
    <div class="h-full text-theme-black text-center">

        <!--main nav-->
        <nav class="h-full grid grid-cols-4 sm:grid-cols-8 xl:grid-cols-12 px-2 py-2 gap-x-2 backdrop-blur bg-theme-light/60 border-b border-theme-light-gray">

            <!--home-->
            <div class="col-start-1 col-span-1">
                <VActionNavigation
                    propElement="a"
                    href="/"
                    class="block w-full h-full relative"
                >
                    <i class="fas fa-wave-square absolute w-fit h-fit left-0 right-0 top-0 bottom-0 m-auto"></i>
                    <span class="sr-only">home</span>
                </VActionNavigation>
            </div>

            <!--start-->
            <div class="col-start-2 col-span-1 sm:col-start-3 sm:col-span-2 xl:col-start-5">
                <VActionNavigation
                    propElement="a"
                    href="/say"
                    class="block w-full h-full relative"
                >
                    <span class="leading-none w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto">
                        <span class="hidden sm:inline"><i class="fas fa-comment pr-2"></i>Start</span>
                        <span class="inline sm:hidden">
                            <i class="fas fa-comment"></i>
                            <span class="sr-only">start event</span>
                        </span>
                    </span>
                </VActionNavigation>
            </div>

            <!--reply-->
            <div class="col-start-3 col-span-1 sm:col-start-5 sm:col-span-2 xl:col-start-7">
                <VActionNavigation
                    propElement="a"
                    href="/hear"
                    class="block w-full h-full relative"
                >
                    <span class="leading-none w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto">
                        <span class="hidden sm:inline"><i class="fas fa-comments pr-2"></i>Reply</span>
                        <span class="inline sm:hidden">
                            <i class="fas fa-comments"></i>
                            <span class="sr-only">reply to events</span>
                        </span>
                    </span>
                </VActionNavigation>
            </div>

            <!--more options-->
            <div
                ref="nav_main_more_button"
                class="col-start-4 col-span-1 sm:col-start-8 xl:col-start-12"
            >
                <VActionNavigation
                    @click.stop="toggle_nav_main_more"
                    :class="propIsLoggedIn === false ? 'lg:hidden' : ''"
                    class="w-full h-full"
                    propElement="button"
                    type="button"
                >
                    <!--mobile burger-->
                    <div class="sm:hidden w-full h-full grid grid-rows-3 grid-flow-row      justify-items-center place-items-center">
                        <div
                            :class="[
                                is_nav_main_more_open ? 'mb-0 rotate-45' : 'mb-4 rotate-0',
                                'nav-burger-line row-span-1 bg-theme-black absolute   w-5 h-0.5     transition-all duration-200 ease-in-out',
                            ]"
                        >
                        </div>
                        <div
                            :class="[
                                is_nav_main_more_open ? 'opacity-0' : 'opacity-100',
                                'nav-burger-line row-span-1 bg-theme-black absolute   w-5 h-0.5     transition-all duration-200 ease-in-out',
                            ]"
                        >
                        </div>
                        <div
                            :class="[
                                is_nav_main_more_open ? 'mt-0 -rotate-45' : 'mt-4 rotate-0',
                                'nav-burger-line row-span-1 bg-theme-black absolute   w-5 h-0.5     transition-all duration-200 ease-in-out',
                            ]"
                        >
                        </div>
                        <span class="sr-only">more navigation options</span>
                    </div>

                    <!--user icon-->
                    <div class="hidden sm:block w-full h-full relative">
                        <i class="fas fa-user text-xl w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto"></i>
                    </div>
                </VActionNavigation>

                <VActionNavigation
                    v-if="propIsLoggedIn === false"
                    propElement="a"
                    href="/"
                    class="hidden lg:block w-full h-full relative"
                >
                    <span class="leading-none w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto">
                        <span><i class="fas fa-circle-user text-2xl pr-2"></i>Log in</span>
                    </span>
                </VActionNavigation>

            </div>
        </nav>

        <!--more nav options, same grid layout as main nav grid-->
        <div class="h-0 grid grid-cols-4 sm:grid-cols-8 xl:grid-cols-12 gap-x-2">
            <!--don't show when lg and propIsLoggedIn, because the button to open will become a URL-->
            <div
                :class="propIsLoggedIn === false ? 'lg:hidden' : ''"
                class="relative col-start-1 col-span-4 sm:col-start-6 sm:col-span-3 xl:col-start-11 right-0"
            >
                <TransitionFade>
                    <div 
                        v-show="is_nav_main_more_open"
                        v-click-outside="{
                            var_name_for_element_bool_status: 'is_nav_main_more_open',
                            refs_to_exclude: ['nav_main_more_button']
                        }"
                        class="absolute w-full h-screen flex flex-col overflow-hidden sm:border-l border-theme-light-gray px-2 sm:px-4      backdrop-blur bg-theme-light/60"
                    >

                        <!--profile area-->
                        <div class="grid grid-cols-4 py-10">
                            <div class="col-span-1 flex items-center">
                                <i class="fas fa-user text-3xl w-fit h-fit mx-auto"></i>
                            </div>
                            <div class="col-span-3 flex items-center">
                                <span class="w-full h-fit text-base font-medium text-left break-words">
                                    <span v-if="propIsLoggedIn">@{{ propUsername }}</span>
                                    <span v-else>Not logged in</span>
                                </span>
                            </div>
                        </div>

                        <!--account options-->
                        <div class="h-fit grid grid-rows-5 gap-2">

                            <!--log in-->
                            <VActionNavigation
                                v-if="propIsLoggedIn === false"
                                :propUseDefaultHeight="true"
                                propElement="a"
                                href="/"
                                class="row-start-1 row-span-1 w-full"
                            >
                                <div class="w-full h-full grid grid-cols-4">
                                    <div class="col-span-1 flex items-center">
                                        <i class="fas fa-circle-user text-2xl w-fit h-fit mx-auto"></i>
                                    </div>
                                    <div class="col-span-3 flex items-center">
                                        <span class="text-left">
                                            Log in
                                        </span>
                                    </div>
                                </div>
                            </VActionNavigation>

                            <!--sign up-->
                            <VActionNavigation
                                v-if="propIsLoggedIn === false"
                                :propUseDefaultHeight="true"
                                propElement="a"
                                href="/"
                                class="row-start-2 row-span-1 w-full"
                            >
                                <div class="w-full h-full grid grid-cols-4">
                                    <div class="col-span-1 flex items-center">
                                        <i class="fas fa-right-to-bracket w-fit h-fit mx-auto"></i>
                                    </div>
                                    <div class="col-span-3 flex items-center">
                                        <span class="text-left">
                                            Sign up
                                        </span>
                                    </div>
                                </div>
                            </VActionNavigation>

                            <!--log out-->
                            <VActionNavigation
                                v-if="propIsLoggedIn === true"
                                :propUseDefaultHeight="true"
                                propElement="a"
                                href="/"
                                class="row-start-1 row-span-1 w-full"
                            >
                                <div class="w-full h-full grid grid-cols-4">
                                    <div class="col-span-1 flex items-center">
                                        <i class="fas fa-door-open w-fit h-fit mx-auto"></i>
                                    </div>
                                    <div class="col-span-3 flex items-center">
                                        <span class="text-left">
                                            Log out
                                        </span>
                                    </div>
                                </div>
                            </VActionNavigation>
                        </div>
                    </div>
                </TransitionFade>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    // import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
    import TransitionFade from '/src/transitions/TransitionFade.vue';
    import VActionNavigation from '@/components/small/VActionNavigation.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        name: 'NavBarApp',
        data(){
            return {
                is_nav_main_more_open: false,
            };
        },
        props: {
            propIsLoggedIn: {
                type: Boolean,
                default: false
            },
            propUsername: {
                type: String,
                default: ""
            },
        },
        methods: {
            toggle_nav_main_more(){

                this.is_nav_main_more_open = !this.is_nav_main_more_open;
            },
        },
    });




</script>