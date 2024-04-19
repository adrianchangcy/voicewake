<template>
    <div class="h-full text-center">

        <!--main nav-->
        <nav class="h-full grid grid-cols-4 sm:grid-cols-8 p-2 gap-x-2       bg-theme-light/90 dark:bg-theme-dark/90">

            <!--home-->
            <div class="col-start-1 col-span-1">
                <VActionText
                    prop-element="a"
                    prop-font-size="m"
                    href="/"
                    :propIsIconOnly="false"
                    class="w-full h-full pb-0.5"
                >
                    <FontAwesomeIcon icon="fas fa-wave-square" class="mx-auto"/>
                    <span class="sr-only">home</span>
                </VActionText>
            </div>

            <!--start-->
            <!--intentional propIsIconOnly="false"-->
            <div
                class="col-start-2 col-span-1 sm:col-start-3 sm:col-span-2 lg:col-start-4 lg:col-span-1"
            >
                <VActionText
                    prop-element="a"
                    prop-font-size="m"
                    href="/start"
                    :propIsIconOnly="false"
                    class="w-full h-full pb-0.5"
                >
                    <FontAwesomeIcon icon="fas fa-comment" class="mx-auto"/>
                    <span class="sr-only">start event</span>
                </VActionText>
            </div>

            <!--reply-->
            <!--intentional propIsIconOnly="false"-->
            <div
                class="col-start-3 col-span-1 sm:col-start-5 sm:col-span-2 lg:col-start-5 lg:col-span-1"
            >
                <VActionText
                    prop-element="a"
                    prop-font-size="m"
                    href="/reply"
                    :propIsIconOnly="false"
                    class="w-full h-full pb-0.5"
                >
                    <FontAwesomeIcon icon="fas fa-comments" class="mx-auto"/>
                    <span class="sr-only">reply in events</span>
                </VActionText>
            </div>

            <!--mobile, always show-->
            <div
                ref="nav_menu_button_1"
                class="block lg:hidden col-start-4 col-span-1 sm:col-start-8"
            >
                <VActionText
                    @click.stop="pop_up_manager_store.toggleIsNavMenuOpen()"
                    prop-element="button"
                    type="button"
                    :propIsIconOnly="true"
                    class="w-full h-full"
                >
                    <!--burger-->
                    <div class="w-full h-full grid grid-rows-3 grid-flow-row      justify-items-center place-items-center">
                        <div
                            :class="[
                                pop_up_manager_store.isNavMenuOpen ? 'mb-0 rotate-45' : 'mb-4 rotate-0',
                                'nav-burger-line row-span-1 bg-theme-black dark:bg-dark-theme-white-2 absolute   w-5 h-0.5     transition-all duration-200 ease-in-out',
                            ]"
                        >
                        </div>
                        <div
                            :class="[
                                pop_up_manager_store.isNavMenuOpen ? 'opacity-0' : 'opacity-100',
                                'nav-burger-line row-span-1 bg-theme-black dark:bg-dark-theme-white-2 absolute   w-5 h-0.5     transition-all duration-200 ease-in-out',
                            ]"
                        >
                        </div>
                        <div
                            :class="[
                                pop_up_manager_store.isNavMenuOpen ? 'mt-0 -rotate-45' : 'mt-4 rotate-0',
                                'nav-burger-line row-span-1 bg-theme-black dark:bg-dark-theme-white-2 absolute   w-5 h-0.5     transition-all duration-200 ease-in-out',
                            ]"
                        >
                        </div>
                        <span class="sr-only">more navigation options</span>
                    </div>
                </VActionText>
            </div>

            <!--desktop, if logged in-->
            <!--not using v-if because we need the ref-->
            <div
                ref="nav_menu_button_2"
                :class="[
                    pop_up_manager_store.isLoggedIn === true ? 'hidden lg:block lg:col-start-8 lg:col-span-1' : 'hidden'
                ]"
            >
                <VActionText
                    @click.stop="pop_up_manager_store.toggleIsNavMenuOpen()"
                    prop-element="button"
                    type="button"
                    :propIsIconOnly="true"
                    class="w-full h-full"
                >
                    <span class="mx-auto">
                        <FontAwesomeIcon icon="fas fa-circle-user" class="text-xl"/>
                        <!--do this so user icon stays truly centered-->
                        <span class="relative w-0">
                            <FontAwesomeIcon
                                icon="fas fa-chevron-down"
                                :class="[
                                    pop_up_manager_store.isNavMenuOpen ? '-rotate-180' : 'rotate-0',
                                    'text-xs transition-transform absolute top-0 bottom-0 left-2 m-auto'
                                ]"
                            />
                        </span>
                    </span>
                    <span class="sr-only">you are logged in, more navigation options</span>
                </VActionText>
            </div>

            <!--desktop, if not logged in, show log in option-->
            <div
                v-if="pop_up_manager_store.isLoggedIn === false"
                class="hidden lg:block lg:col-start-7 lg:col-span-1"
            >
                <TransitionFade>
                    <VActionText
                        v-show="canShowLogInSignUpAtNav"
                        @click.stop="openUserLogInSignUp('log-in-section')"
                        prop-element="button"
                        type="button"
                        prop-font-size="m"
                        :prop-is-icon-only="true"
                        class="w-full h-full pb-1 dark:text-dark-theme-white-1"
                    >
                        <span class="block mx-auto">
                            <FontAwesomeIcon icon="fas fa-circle-user" class="sm:pr-2"/>
                            <span>Log in</span>
                        </span>
                    </VActionText>
                </TransitionFade>
            </div>

            <!--desktop, if not logged in, show sign up option-->
            <div
                v-if="pop_up_manager_store.isLoggedIn === false"
                class="hidden lg:block lg:col-start-8 col-span-1"
            >
                <TransitionFade>
                    <!--using size "m" everything, but "s" shadow-->
                    <VActionSpecial
                        v-show="canShowLogInSignUpAtNav"
                        @click.stop="openUserLogInSignUp('sign-up-section')"
                        prop-element="button"
                        prop-font-size="m"
                        type="button"
                        class="w-full h-full shadow-md dark:shadow-surround-md active:shadow-sm dark:active:shadow-surround-sm      pb-1.5"
                    >
                        <span class="block mx-auto">
                            <FontAwesomeIcon icon="fas fa-right-to-bracket" class="sm:pr-2"/>
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
                :class="pop_up_manager_store.isLoggedIn === false ? 'lg:hidden' : ''"
                class="relative col-start-1 col-span-1 sm:col-span-5 xl:col-span-6"
            >
                <TransitionFade>
                    <div
                        v-show="pop_up_manager_store.isNavMenuOpen"
                        class="absolute w-full h-[calc(100vh-4.5rem)] bg-theme-light/90 dark:bg-theme-dark/90"
                    >
                    </div>
                </TransitionFade>
            </div>

            <!--nav menu-->
            <!--don't show when lg and pop_up_manager_store.isLoggedIn, because the button to open will become a URL-->
            <div
                :class="pop_up_manager_store.isLoggedIn === false ? 'lg:hidden' : ''"
                class="h-0 relative col-start-2 col-span-3 sm:col-start-6 sm:col-span-3 xl:col-start-7 xl:col-span-2"
            >

                <TransitionFade>
                    <!--menu itself-->
                    <!--has pb simply for better UI, i.e. allows user to scroll to eye-level-->
                    <div
                        v-show="pop_up_manager_store.isNavMenuOpen"
                        v-click-outside="{
                            bool_status_variable_or_callback: forceCloseNavMenu,
                            refs_to_exclude: ['nav_menu_button_1', 'nav_menu_button_2']
                        }"
                        class="absolute w-full h-[calc(100vh-4.5rem)] overflow-auto px-4 pb-20 bg-theme-light dark:bg-theme-dark"
                    >
                        <!--profile area-->
                        <div class="py-2 dark:text-dark-theme-white-1">

                            <!--logged in, can click to view profile-->
                            <VActionText
                                v-if="pop_up_manager_store.isLoggedIn"
                                prop-element="a"
                                :prop-is-icon-only="false"
                                :href="getProfileURL()"
                                class="w-full h-fit py-10"
                            >
                                <div class="w-full flex flex-col">
                                    <FontAwesomeIcon icon="fas fa-circle-user" class="text-2xl mx-auto"/>
                                    <span class="max-w-full h-fit mx-auto text-xl font-medium break-words">
                                        <span>{{ propUsername }}</span>
                                    </span>
                                </div>
                            </VActionText>

                            <!--not logged in-->
                            <div
                                v-else
                                class="w-full flex flex-col py-10"
                            >
                                <FontAwesomeIcon icon="fas fa-circle-user" class="text-2xl mx-auto"/>
                                <span class="max-w-full h-fit mx-auto text-xl font-light break-words">
                                    <span>Not logged in</span>
                                </span>
                            </div>
                        </div>

                        <!--divider-->
                        <div class="pb-6">
                            <div class="w-full h-[1px] bg-theme-gray-2 dark:bg-dark-theme-gray-2 mx-auto"></div>
                        </div>

                        <!--log in / sign up-->
                        <div
                            v-if="pop_up_manager_store.isLoggedIn === false"
                            class="h-fit flex flex-col gap-1 dark:text-dark-theme-white-1"
                        >

                            <!--log in-->
                            <VActionText
                                prop-element="a"
                                href="/login"
                                prop-font-size="s"
                                prop-element-size="s"
                                :prop-is-icon-only="false"
                            >
                                <div class="h-full flex flex-row">
                                    <div class="px-4 flex items-center">
                                        <FontAwesomeIcon icon="fas fa-circle-user" class="pt-0.5 mx-auto"/>
                                    </div>
                                    <div class="flex items-center">
                                        <span class="text-left break-all">
                                            Log in
                                        </span>
                                    </div>
                                </div>
                            </VActionText>

                            <!--sign up-->
                            <VActionText
                                prop-element="a"
                                href="/signup"
                                prop-font-size="s"
                                prop-element-size="s"
                                :prop-is-icon-only="false"
                            >
                                <div class="h-full flex flex-row">
                                    <div class="px-4 flex items-center">
                                        <FontAwesomeIcon icon="fas fa-right-to-bracket" class="pt-0.5 mx-auto"/>
                                    </div>
                                    <div class="flex items-center">
                                        <span class="text-left break-all">
                                            Sign up
                                        </span>
                                    </div>
                                </div>
                            </VActionText>
                        </div>

                        <!--main URLs-->
                        <div
                            v-if="pop_up_manager_store.isLoggedIn === true"
                            class="flex flex-col gap-1"
                        >

                            <!--own recordings-->
                            <div
                                class="h-fit"
                            >
                                <VActionText
                                    prop-element="a"
                                    :href="getProfileURL()"
                                    prop-font-size="s"
                                    prop-element-size="s"
                                    :prop-is-icon-only="false"
                                >
                                    <div class="h-full flex flex-row">
                                        <div class="px-4 flex items-center">
                                            <FontAwesomeIcon icon="fas fa-microphone-lines" class="pt-0.5 mx-auto text-xl"/>
                                        </div>
                                        <div class="flex items-center">
                                            <span class="text-left break-all">
                                                Recordings
                                            </span>
                                        </div>
                                    </div>
                                </VActionText>
                            </div>

                            <!--likes/dislikes-->
                            <div
                                class="h-fit grid"
                            >
                                <VActionText
                                    prop-element="a"
                                    href="/likes"
                                    prop-font-size="s"
                                    prop-element-size="s"
                                    :prop-is-icon-only="false"
                                >
                                    <div class="h-full flex flex-row">
                                        <div class="px-4 flex items-center">
                                            <FontAwesomeIcon icon="far fa-thumbs-up" class="mx-auto text-lg"/>
                                        </div>
                                        <div class="flex items-center">
                                            <span class="text-left break-all">
                                                Likes &#38; dislikes
                                            </span>
                                        </div>
                                    </div>
                                </VActionText>
                            </div>

                            <!--block list-->
                            <div
                                class="h-fit grid"
                            >
                                <VActionText
                                    prop-element="a"
                                    href="/block"
                                    prop-font-size="s"
                                    prop-element-size="s"
                                    :prop-is-icon-only="false"
                                >
                                    <div class="h-full flex flex-row">
                                        <div class="px-4 flex items-center">
                                            <FontAwesomeIcon icon="fas fa-ban" class="pt-0.5 mx-auto"/>
                                        </div>
                                        <div class="flex items-center">
                                            <span class="text-left break-all">
                                                Block list
                                            </span>
                                        </div>
                                    </div>
                                </VActionText>
                            </div>

                            <!--divider-->
                            <div
                                class="py-6"
                            >
                                <div class="w-full h-[1px] bg-theme-gray-2 dark:bg-dark-theme-gray-2 mx-auto"></div>
                            </div>

                            <!--light/dark theme-->
                            <div class="h-full flex flex-row">
                                <div class="px-4 flex items-center">
                                    <FontAwesomeIcon icon="far fa-moon" class="mx-auto text-lg"/>
                                </div>
                                <!--follows "s" size action-->
                                <div class="w-full flex items-center text-base font-medium pb-0.5">
                                    <span class="text-left break-all">
                                        Dark mode
                                    </span>
                                </div>
                                <VSwitch
                                    :prop-screen-reader-text="getDarkModeScreenReaderText"
                                    :prop-default-toggle="isDarkMode"
                                    @is-toggled="handleDarkMode($event)"
                                />
                            </div>

                            <!--divider-->
                            <div
                                v-if="pop_up_manager_store.isLoggedIn === true"
                                class="py-6"
                            >
                                <div class="w-full h-[1px] bg-theme-gray-2 dark:bg-dark-theme-gray-2 mx-auto"></div>
                            </div>

                            <!--log out-->
                            <div
                                v-if="pop_up_manager_store.isLoggedIn === true"
                                class="h-fit flex flex-col"
                            >
                                <VActionText
                                    v-if="pop_up_manager_store.isLoggedIn === true"
                                    :prop-is-enabled="!is_log_out_loading"
                                    @click.stop="logOut()"
                                    prop-element="button"
                                    prop-font-size="s"
                                    prop-element-size="s"
                                    :prop-is-icon-only="false"
                                    type="button"
                                    class="w-full"
                                >
                                    <div class="h-full flex flex-row">
                                        <div class="px-4 flex items-center">
                                            <VLoading
                                                v-if="is_log_out_loading"
                                                prop-element-size="s"
                                                class="mx-auto"
                                            />
                                            <span v-else class="mx-auto">
                                                <FontAwesomeIcon icon="fas fa-door-open"/>
                                            </span>
                                        </div>
                                        <div class="flex items-center">
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
                                </VActionText>
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
    import TransitionFade from '/src/transitions/TransitionFade.vue';
    import VActionText from '../small/VActionText.vue';
    import VActionSpecial from '../small/VActionSpecial.vue';
    import VLoading from '../small/VLoading.vue';
    import VSwitch from '../small/VSwitch.vue';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faWaveSquare } from '@fortawesome/free-solid-svg-icons/faWaveSquare';
    import { faComment } from '@fortawesome/free-solid-svg-icons/faComment';
    import { faComments } from '@fortawesome/free-solid-svg-icons/faComments';
    import { faCircleUser } from '@fortawesome/free-solid-svg-icons/faCircleUser';
    import { faChevronDown } from '@fortawesome/free-solid-svg-icons/faChevronDown';
    import { faRightToBracket } from '@fortawesome/free-solid-svg-icons/faRightToBracket';
    import { faBan } from '@fortawesome/free-solid-svg-icons/faBan';
    import { faDoorOpen } from '@fortawesome/free-solid-svg-icons/faDoorOpen';
    import { faMicrophoneLines } from '@fortawesome/free-solid-svg-icons/faMicrophoneLines';
    import { faThumbsUp as farThumbsUp } from '@fortawesome/free-regular-svg-icons/faThumbsUp';
    import { faMoon } from '@fortawesome/free-regular-svg-icons/faMoon';

    library.add(
        faWaveSquare, faComment, faComments, faCircleUser,
        faChevronDown, faRightToBracket, faBan, faDoorOpen, faMicrophoneLines,
        farThumbsUp, faMoon,
    );
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { usePageRefreshTriggerStore } from '@/stores/PageRefreshTriggerStore';
    import { usePopUpManagerStore } from '@/stores/PopUpManagerStore';
    import { useFilteredEventsStore } from '@/stores/FilteredEventsStore';
    import { useEventReplyChoicesStore } from '@/stores/EventReplyChoicesStore';
    import { useVPlaybackStore } from '@/stores/VPlaybackStore';
    import { useAudioClipProcessingsStore } from '@/stores/AudioClipProcessingsStore';
    import { useRedrawCanvasesStore } from '@/stores/RedrawCanvasesStore';
    const axios = require('axios');

    export default defineComponent({
        name: 'NavBar',
        data(){
            return {
                page_refresh_trigger_store: usePageRefreshTriggerStore(),
                pop_up_manager_store: usePopUpManagerStore(),
                redraw_canvases_store: useRedrawCanvasesStore(),

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
                    this.pop_up_manager_store.isLoginRequiredPromptOpen === false &&
                    this.pop_up_manager_store.isUserLogInOpen === false &&
                    this.pop_up_manager_store.isUserSignUpOpen === false
                );
            },
            getDarkModeScreenReaderText() : string {

                if(localStorage.getItem('dark_mode') === null){

                    return '';

                }else if(Boolean(localStorage.getItem('dark_mode')) === true){

                    return 'Currently in dark mode. Click to change to light mode.';

                }else{

                    return 'Currently in light mode. Click to change to dark mode.';
                }
            },
            isDarkMode() : boolean {

                return localStorage.getItem('dark_mode') !== null && JSON.parse(localStorage.getItem('dark_mode')!) === true;
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

                if(section === 'log-in-section'){

                    this.pop_up_manager_store.toggleIsUserLogInOpen(true);

                }else if(section === 'sign-up-section'){

                    this.pop_up_manager_store.toggleIsUserSignUpOpen(true);
                }
            },
            async logOut() : Promise<void> {

                this.is_log_out_loading = true;

                await axios.post(window.location.origin + "/api/users/log-out")
                .then(() => {

                    //reset user-specific stores

                    //logged-in users can have extra interactions with certain data
                    //on logout, we reset all for current logged-in user
                    const stores_to_reset = [
                        useEventReplyChoicesStore(),
                        useFilteredEventsStore('home'),
                        useFilteredEventsStore('user_likes_dislikes'),
                        useFilteredEventsStore('user_profile'),
                        useVPlaybackStore(),
                        useAudioClipProcessingsStore(),
                    ];

                    for(let x=0; x < stores_to_reset.length; x++){

                        stores_to_reset[x].$reset();
                    }

                    //doing this will refresh all open tabs/pages for us
                    this.page_refresh_trigger_store.$patch({
                        refresh_context: "logging_out"
                    });

                })
                .catch((error:any) => {

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
            handleDarkMode(is_dark_mode:boolean) : void {

                localStorage.setItem('dark_mode', JSON.stringify(is_dark_mode));

                //add/remove "dark"

                const target_element = document.documentElement;

                //dark
                if(is_dark_mode === true && target_element.classList.contains('dark') === false){

                    target_element.classList.add('dark');
                    this.redraw_canvases_store.redrawAllAudioVolumePeakCanvases();
                    return;
                }

                //not dark
                if(is_dark_mode === false && target_element.classList.contains('dark') === true){

                    target_element.classList.remove('dark');
                    this.redraw_canvases_store.redrawAllAudioVolumePeakCanvases();
                    return;
                }
            },
        },
        beforeMount(){

            this.handleIsLogInSignUpStaticPage();
        },
    });
</script>