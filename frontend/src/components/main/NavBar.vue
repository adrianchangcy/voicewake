<template>
    <div class="h-full text-theme-black text-center">

        <!--main nav-->
        <nav class="h-full grid grid-cols-4 sm:grid-cols-8 p-2 gap-x-2 backdrop-blur bg-theme-light/60 border-b border-theme-light-gray/50">

            <!--home-->
            <div class="col-start-1 col-span-1">
                <VActionTextOnly
                    propElement="a"
                    propFontSize="m"
                    href="/"
                    :propIsIconOnly="true"
                    class="w-full h-full pb-0.5"
                >
                    <i class="fas fa-wave-square mx-auto" aria-hidden="true"></i>
                    <span class="sr-only">home</span>
                </VActionTextOnly>
            </div>

            <!--start-->
            <div class="col-start-2 col-span-1 sm:col-start-3 sm:col-span-2 lg:col-start-4 lg:col-span-1">
                <VActionTextOnly
                    propElement="a"
                    propFontSize="m"
                    href="/start"
                    :propIsIconOnly="false"
                    class="w-full h-full pb-0.5"
                >
                    <span class="block mx-auto">
                        <i class="fas fa-comment" aria-hidden="true"></i>
                        <!-- <span class="hidden font-normal sm:inline sm:pl-2">Start</span> -->
                    </span>
                    <span class="sr-only sm:hidden">start event</span>
                </VActionTextOnly>
            </div>

            <!--reply-->
            <div class="col-start-3 col-span-1 sm:col-start-5 sm:col-span-2 lg:col-start-5 lg:col-span-1">
                <VActionTextOnly
                    propElement="a"
                    propFontSize="m"
                    href="/reply"
                    :propIsIconOnly="false"
                    class="w-full h-full pb-0.5"
                >
                    <span class="block mx-auto">
                        <i class="fas fa-comments" aria-hidden="true"></i>
                        <!-- <span class="hidden font-normal sm:inline sm:pl-2">Reply</span> -->
                    </span>
                    <span class="sr-only sm:hidden">reply to events</span>
                </VActionTextOnly>
            </div>

            <!--mobile, always show-->
            <div
                ref="nav_menu_button_1"
                class="block lg:hidden col-start-4 col-span-1 sm:col-start-8"
            >
                <VActionTextOnly
                    @click.stop="pop_up_manager_store.toggleIsNavMenuOpen()"
                    propElement="button"
                    type="button"
                    :propIsIconOnly="true"
                    class="w-full h-full"
                >
                    <!--burger-->
                    <div class="w-full h-full grid grid-rows-3 grid-flow-row      justify-items-center place-items-center">
                        <div
                            :class="[
                                pop_up_manager_store.getIsNavMenuOpen ? 'mb-0 rotate-45' : 'mb-4 rotate-0',
                                'nav-burger-line row-span-1 bg-theme-black absolute   w-5 h-0.5     transition-all duration-200 ease-in-out',
                            ]"
                        >
                        </div>
                        <div
                            :class="[
                                pop_up_manager_store.getIsNavMenuOpen ? 'opacity-0' : 'opacity-100',
                                'nav-burger-line row-span-1 bg-theme-black absolute   w-5 h-0.5     transition-all duration-200 ease-in-out',
                            ]"
                        >
                        </div>
                        <div
                            :class="[
                                pop_up_manager_store.getIsNavMenuOpen ? 'mt-0 -rotate-45' : 'mt-4 rotate-0',
                                'nav-burger-line row-span-1 bg-theme-black absolute   w-5 h-0.5     transition-all duration-200 ease-in-out',
                            ]"
                        >
                        </div>
                        <span class="sr-only">more navigation options</span>
                    </div>
                </VActionTextOnly>
            </div>

            <!--desktop, if logged in-->
            <!--not using v-if because we need the ref-->
            <div
                ref="nav_menu_button_2"
                :class="[
                    pop_up_manager_store.getIsLoggedIn === true ? 'hidden lg:block lg:col-start-8 lg:col-span-1' : 'hidden'
                ]"
            >
                <VActionTextOnly
                    @click.stop="pop_up_manager_store.toggleIsNavMenuOpen()"
                    propElement="button"
                    type="button"
                    :propIsIconOnly="true"
                    class="w-full h-full"
                >
                    <span class="mx-auto">
                        <i class="fas fa-circle-user text-xl" aria-hidden="true"></i>
                        <!--do this so user icon stays truly centered-->
                        <span class="relative w-0">
                            <i
                                :class="[
                                    pop_up_manager_store.getIsNavMenuOpen ? '-rotate-180' : 'rotate-0',
                                    'fas fa-chevron-down text-xs transition-transform h-fit absolute top-0 bottom-0 left-2 m-auto'
                                ]"
                                aria-hidden="true"
                            ></i>
                        </span>
                    </span>
                    <span class="sr-only">you are logged in, more navigation options</span>
                </VActionTextOnly>
            </div>

            <!--desktop, if not logged in, show log in option-->
            <div
                v-if="pop_up_manager_store.getIsLoggedIn === false"
                class="hidden lg:block lg:col-start-7 lg:col-span-1"
            >
                <TransitionFade>
                    <VActionTextOnly
                        v-show="canShowLogInSignUpAtNav"
                        @click.stop="openUserLogInSignUp('log-in-section')"
                        propElement="button"
                        propFontSize="m"
                        type="button"
                        class="w-full h-full pb-0.5"
                    >
                        <span class="block mx-auto">
                            <i class="fas fa-circle-user sm:pr-2" aria-hidden="true"></i>
                            <span>Log in</span>
                        </span>
                    </VActionTextOnly>
                </TransitionFade>
            </div>

            <!--desktop, if not logged in, show sign up option-->
            <div
                v-if="pop_up_manager_store.getIsLoggedIn === false"
                class="hidden lg:block lg:col-start-8 col-span-1"
            >
                <TransitionFade>
                    <VActionSpecial
                        v-show="canShowLogInSignUpAtNav"
                        @click.stop="openUserLogInSignUp('sign-up-section')"
                        propElement="button"
                        type="button"
                        propElementSize="s"
                        class="w-full h-full pb-0.5"
                    >
                        <span class="block mx-auto text-xl font-medium">
                            <i class="fas fa-right-to-bracket sm:pr-2" aria-hidden="true"></i>
                            <span>Sign up</span>
                        </span>
                    </VActionSpecial>
                </TransitionFade>
            </div>
        </nav>

        <!--more nav options, same grid layout as main nav grid-->
        <div class="h-0 grid grid-cols-4 sm:grid-cols-8">

            <!--extra area to click when nav menu is open-->
            <div
                :class="pop_up_manager_store.getIsLoggedIn === false ? 'lg:hidden' : ''"
                class="relative col-start-1 col-span-1 sm:col-span-5 xl:col-span-6"
            >
                <TransitionFade>
                    <div
                        v-show="pop_up_manager_store.getIsNavMenuOpen"
                        class="absolute w-full h-[calc(100vh-4.5rem)] bg-theme-light/60 backdrop-blur"
                    >
                    </div>
                </TransitionFade>
            </div>

            <!--nav menu-->
            <!--don't show when lg and pop_up_manager_store.getIsLoggedIn, because the button to open will become a URL-->
            <div
                :class="pop_up_manager_store.getIsLoggedIn === false ? 'lg:hidden' : ''"
                class="relative col-start-2 col-span-3 sm:col-start-6 sm:col-span-3 xl:col-start-7 xl:col-span-2"
            >
                <TransitionFade>
                    <!--uses calc to minus fixed height of navbar at base.html-->
                    <div
                        v-show="pop_up_manager_store.getIsNavMenuOpen"
                        v-click-outside="{
                            var_name_for_element_bool_status: forceCloseNavMenu,
                            refs_to_exclude: ['nav_menu_button_1', 'nav_menu_button_2']
                        }"
                        class="absolute w-full h-[calc(100vh-4.5rem)] flex flex-col overflow-hidden p-2 border-l border-theme-light-gray bg-theme-light"
                    >

                        <!--profile area-->
                        <div class="pt-12 pb-14">

                            <!--logged in, can click to view profile-->
                            <VActionTextOnly
                                v-if="pop_up_manager_store.getIsLoggedIn"
                                prop-element="a"
                                :href="getProfileURL()"
                            >
                                <div class="w-full flex flex-col">
                                    <i class="fas fa-circle-user text-2xl w-fit h-fit mx-auto" aria-hidden="true"></i>
                                    <span class="max-w-full h-fit mx-auto text-xl font-medium break-words">
                                        <span>012345678901234567890123456789</span>
                                    </span>
                                </div>
                            </VActionTextOnly>

                            <!--not logged in-->
                            <div
                                v-else
                                class="flex flex-col"
                            >
                                <i class="fas fa-circle-user text-2xl w-fit h-fit mx-auto" aria-hidden="true"></i>
                                <span class="max-w-full h-fit mx-auto text-xl font-light break-words">
                                    <span>Not logged in</span>
                                </span>
                            </div>
                        </div>

                        <!--divider-->
                        <div class="pb-4">
                            <div class="w-[75%] h-[1px] bg-theme-light-gray mx-auto"></div>
                        </div>

                        <!--log in / sign up-->
                        <div
                            v-if="pop_up_manager_store.getIsLoggedIn === false"
                            class="h-fit grid"
                        >

                            <!--log in-->
                            <VActionTextOnly
                                propElement="a"
                                href="/login"
                                propFontSize="s"
                                propElementSize="s"
                                class="row-span-1 w-full"
                            >
                                <div class="w-full h-full grid grid-cols-4">
                                    <div class="col-span-1 flex items-center">
                                        <i class="fas fa-circle-user pt-0.5 w-fit h-fit mx-auto" aria-hidden="true"></i>
                                    </div>
                                    <div class="col-span-3 flex items-center">
                                        <span class="text-left break-all">
                                            Log in
                                        </span>
                                    </div>
                                </div>
                            </VActionTextOnly>

                            <!--sign up-->
                            <VActionTextOnly
                                propElement="a"
                                href="/signup"
                                propFontSize="s"
                                propElementSize="s"
                                class="row-span-1 w-full"
                            >
                                <div class="w-full h-full grid grid-cols-4">
                                    <div class="col-span-1 flex items-center">
                                        <i class="fas fa-right-to-bracket pt-0.5 w-fit h-fit mx-auto" aria-hidden="true"></i>
                                    </div>
                                    <div class="col-span-3 flex items-center">
                                        <span class="text-left break-all">
                                            Sign up
                                        </span>
                                    </div>
                                </div>
                            </VActionTextOnly>
                        </div>

                        <!--block list-->
                        <div
                            v-if="pop_up_manager_store.getIsLoggedIn === true"
                            class="h-fit grid"
                        >
                            <!--block list-->
                            <VActionTextOnly
                                propElement="a"
                                href="/block"
                                propFontSize="s"
                                propElementSize="s"
                                class="row-span-1 w-full"
                            >
                                <div class="w-full h-full grid grid-cols-4">
                                    <div class="col-span-1 flex items-center">
                                        <i class="fas fa-ban pt-0.5 w-fit h-fit mx-auto" aria-hidden="true"></i>
                                    </div>
                                    <div class="col-span-3 flex items-center">
                                        <span class="text-left break-all">
                                            Block list
                                        </span>
                                    </div>
                                </div>
                            </VActionTextOnly>
                        </div>

                        <!--divider-->
                        <div
                            v-if="pop_up_manager_store.getIsLoggedIn === true"
                            class="py-4"
                        >
                            <div class="w-[75%] h-[1px] bg-theme-light-gray mx-auto"></div>
                        </div>

                        <!--log out-->
                        <div
                            v-if="pop_up_manager_store.getIsLoggedIn === true"
                            class="h-fit grid gap-2"
                        >
                            <!--log out-->
                            <VActionTextOnly
                                v-if="pop_up_manager_store.getIsLoggedIn === true"
                                :propIsEnabled="!is_log_out_loading"
                                @click.stop="logOut()"
                                propElement="button"
                                propFontSize="s"
                                propElementSize="s"
                                type="button"
                                class="w-full"
                            >
                                <div class="w-full h-full grid grid-cols-4">
                                    <div class="col-span-1 flex items-center">
                                        <VLoading
                                            v-if="is_log_out_loading"
                                            propElementSize="s"
                                            class="mx-auto"
                                        />
                                        <span v-else class="mx-auto">
                                            <i class="fas fa-door-open" aria-hidden="true"></i>
                                        </span>
                                    </div>
                                    <div class="col-span-3 flex items-center">
                                        <span class="text-left break-all">
                                            <span v-if="is_log_out_loading">
                                                Logging out...
                                            </span>
                                            <span v-else>
                                                Log out
                                            </span>
                                        </span>
                                    </div>
                                </div>
                            </VActionTextOnly>
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
    import VActionTextOnly from '@/components/small/VActionTextOnly.vue';
    import VActionSpecial from '../small/VActionSpecial.vue';
    import VLoading from '../small/VLoading.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { usePageRefreshTriggerStore } from '@/stores/PageRefreshTriggerStore';
    import { usePopUpManagerStore } from '@/stores/PopUpManagerStore';
    const axios = require('axios');

    export default defineComponent({
        name: 'NavBar',
        data(){
            return {
                page_refresh_trigger_store: usePageRefreshTriggerStore(),
                pop_up_manager_store: usePopUpManagerStore(),

                is_log_out_loading: false,
                is_currently_log_in_sign_up_static_page: false,
            };
        },
        props: {
            propUsername: {
                type: String,
                default: ""
            },
        },
        computed: {
            canShowLogInSignUpAtNav() : boolean {
                return (
                    this.is_currently_log_in_sign_up_static_page === false &&
                    this.pop_up_manager_store.getIsUserLogInSignUpOpen === false &&
                    this.pop_up_manager_store.getIsLoginRequiredPromptOpen === false
                );
            },
        },
        watch: {
        },
        methods: {
            getProfileURL() : string {

                return window.location.origin + '/user/' + this.propUsername;
            },
            forceCloseNavMenu() : void {

                this.pop_up_manager_store.toggleIsNavMenuOpen(false);
            },
            openUserLogInSignUp(section:"log-in-section"|"sign-up-section") : void {

                this.pop_up_manager_store.toggleIsNavMenuOpen(false);
                this.pop_up_manager_store.toggleIsUserLogInSignUpOpen(true, section);
            },
            async logOut() : Promise<void> {

                this.is_log_out_loading = true;

                await axios.post(window.location.origin + "/api/users/log-out")
                .then(() => {

                    //doing this will refresh all open tabs/pages for us
                    this.page_refresh_trigger_store.$patch({
                        refresh_context: "logging_out"
                    });
                })
                .catch((error: any) => {

                    console.log(error);

                    this.is_log_out_loading = false;
                });
            },
            handleIsLogInSignUpStaticPage() : void {

                //we want login/signup button to be URL to static page if so, not open/close
                const current_url = window.location.href;

                if(current_url.includes("login") === true || current_url.includes("signup") === true){

                    this.is_currently_log_in_sign_up_static_page = true;

                }else{

                    this.is_currently_log_in_sign_up_static_page = false;
                }
            },
        },
        beforeMount(){

            this.handleIsLogInSignUpStaticPage();
        },
    });
</script>