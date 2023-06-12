<template>
    <div class="h-full text-theme-black text-center">

        <!--main nav-->
        <nav class="h-full grid grid-cols-4 sm:grid-cols-8 xl:grid-cols-12 px-2 py-2 gap-x-2 backdrop-blur bg-theme-light/60 border-b border-theme-light-gray">

            <!--home-->
            <div class="col-start-1 col-span-1">
                <VNavigationButton
                    propElement="a"
                    href="/"
                    class="block w-full h-full relative"
                >
                    <i class="fas fa-wave-square text-xl absolute w-fit h-fit left-0 right-0 top-0 bottom-0 m-auto"></i>
                    <span class="sr-only">home</span>
                </VNavigationButton>
            </div>

            <!--start-->
            <div class="col-start-2 col-span-1 sm:col-start-3 sm:col-span-2 xl:col-start-5">
                <VNavigationButton
                    propElement="a"
                    href="/say"
                    class="block w-full h-full relative"
                >
                    <span class="text-lg font-medium leading-none w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto">
                        <span class="hidden sm:inline"><i class="fas fa-comment pr-1"></i>Start</span>
                        <span class="inline sm:hidden">
                            <i class="fas fa-comment"></i>
                            <span class="sr-only">start event</span>
                        </span>
                    </span>
                </VNavigationButton>
            </div>

            <!--reply-->
            <div class="col-start-3 col-span-1 sm:col-start-5 sm:col-span-2 xl:col-start-7">
                <VNavigationButton
                    propElement="a"
                    href="/hear"
                    class="block w-full h-full relative"
                >
                    <span class="text-lg font-medium leading-none w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto">
                        <span class="hidden sm:inline"><i class="fas fa-comments pr-1"></i>Reply</span>
                        <span class="inline sm:hidden">
                            <i class="fas fa-comments"></i>
                            <span class="sr-only">reply to events</span>
                        </span>
                    </span>
                </VNavigationButton>
            </div>

            <!--more options-->
            <div
                ref="nav_main_more_button"
                class="col-start-4 col-span-1 sm:col-start-8 xl:col-start-12"
            >
                <VNavigationButton
                    @click.stop="toggle_nav_main_more"
                    :class="is_logged_in === false ? 'lg:hidden' : ''"
                    class="w-full h-full"
                    propElement="button"
                    type="button"
                >
                    <!--mobile burger-->
                    <div class="lg:hidden w-full h-full grid grid-rows-3 grid-flow-row      justify-items-center place-items-center">
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
                    <div v-if="is_logged_in === true" class="hidden lg:block w-full h-full relative">
                        <i class="fas fa-circle-user text-2xl w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto"></i>
                    </div>
                </VNavigationButton>

                <VNavigationButton
                    v-if="is_logged_in === false"
                    propElement="a"
                    href="/"
                    class="hidden lg:block w-full h-full relative"
                >
                    <span class="text-lg font-medium leading-none w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto">
                        <span><i class="fas fa-circle-user pr-1"></i>Log In</span>
                    </span>
                </VNavigationButton>

            </div>
        </nav>

        <!--more nav options, same grid layout as main nav grid-->
        <div class="h-0 grid grid-cols-4 sm:grid-cols-8 xl:grid-cols-12 pl-2 gap-x-2">
            <!--don't show when lg and is_logged_in, because the button to open will become a URL-->
            <div
                :class="is_logged_in === false ? 'lg:hidden' : ''"
                class="h-0 relative col-start-1 col-span-4 sm:col-start-7 sm:col-span-2 xl:col-start-11 right-0"
            >
                <TransitionFade>
                    <div 
                        v-show="is_nav_main_more_open"
                        v-click-outside="{
                            var_name_for_element_bool_status: 'is_nav_main_more_open',
                            refs_to_exclude: ['nav_main_more_button']
                        }"
                        class="absolute w-full h-screen p-2 pt-10 flex flex-col gap-4 overflow-hidden sm:border-l border-theme-light-gray      backdrop-blur bg-theme-light/60"
                    >

                        <!--profile area-->
                        <div v-if="is_logged_in" class="h-20 grid grid-cols-4">
                            <div class="col-span-1 flex items-center">
                                <i class="fas fa-circle-user text-4xl w-fit h-fit mx-auto"></i>
                            </div>
                            <div class="col-span-3 flex items-center">
                                <span class="w-full h-fit text-left overflow-hidden text-ellipsis break-words leading-none">
                                    {{ username }}
                                </span>
                            </div>
                        </div>

                        <!--account options-->
                        <div class="h-fit grid grid-rows-5 gap-2">

                            <!--sign in-->
                            <VNavigationButton
                                v-if="is_logged_in === false"
                                propElement="a"
                                href="/"
                                class="row-start-1 row-span-1 h-10 relative grid grid-cols-4"
                            >
                                <div class="col-span-1 flex items-center">
                                    <i class="fas fa-circle-user text-xl w-fit h-fit mx-auto"></i>
                                </div>
                                <div class="col-span-3 flex items-center">
                                    <span class="w-full h-fit text-left text-base font-medium">
                                        Log In
                                    </span>
                                </div>
                            </VNavigationButton>

                            <!--create account-->
                            <VNavigationButton
                                v-if="is_logged_in === false"
                                propElement="a"
                                href="/"
                                class="row-start-2 row-span-1 h-10 relative grid grid-cols-4"
                            >
                                <div class="col-span-1 flex items-center">
                                    <i class="fas fa-right-to-bracket text-xl w-fit h-fit mx-auto"></i>
                                </div>
                                <div class="col-span-3 flex items-center">
                                    <span class="w-full h-fit text-left text-base font-medium">
                                        Create Account
                                    </span>
                                </div>
                            </VNavigationButton>

                            <!--sign out-->
                            <VNavigationButton
                                v-if="is_logged_in === true"
                                propElement="a"
                                href="/"
                                class="row-start-1 row-span-1 w-full h-10 relative grid grid-cols-4"
                            >
                                <div class="col-span-1 flex items-center">
                                    <i class="fas fa-door-open text-xl w-fit h-fit mx-auto"></i>
                                </div>
                                <div class="col-span-3 flex items-center">
                                    <span class="w-full h-fit text-left text-base font-medium">
                                        Log Out
                                    </span>
                                </div>
                            </VNavigationButton>
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
    import VNavigationButton from '@/components/small/VNavigationButton.vue';
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