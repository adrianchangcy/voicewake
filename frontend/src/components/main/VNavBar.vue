<template>
    <div class="h-full">

        <!--main nav-->
        <!--px-5 to align with main content-->
        <nav
            class="h-full text-center grid grid-cols-4 lg:grid-cols-8 gap-2 p-2 bg-theme-nav dark:bg-dark-theme-nav border-b border-theme-gray-2 dark:border-transparent"
        >

            <!--home-->
            <div class="col-start-1 col-span-1 lg:col-start-1 lg:col-span-1">
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
                class="col-start-2 col-span-1 lg:col-start-4 lg:col-span-1"
            >
                <VActionText
                    prop-element="a"
                    prop-font-size="m"
                    href="/start"
                    :propIsIconOnly="false"
                    class="w-full h-full pb-0.5"
                >
                    <FontAwesomeIcon icon="fas fa-comment" class="mx-auto text-lg"/>
                    <span class="sr-only">start event</span>
                </VActionText>
            </div>

            <!--reply-->
            <!--intentional propIsIconOnly="false"-->
            <div
                class="col-start-3 col-span-1 lg:col-start-5 lg:col-span-1"
            >
                <VActionText
                    prop-element="a"
                    prop-font-size="m"
                    href="/reply"
                    :propIsIconOnly="false"
                    class="w-full h-full pb-0.5"
                >
                    <FontAwesomeIcon icon="fas fa-comments" class="mx-auto text-lg"/>
                    <span class="sr-only">reply in events</span>
                </VActionText>
            </div>

            <!--show on deskstop when not logged in-->
            <div
                ref="nav_big_sign_up_button"
                :class="[
                    canShowLogInSignUpAtNav ? 'lg:block lg:col-start-7 col-span-1' : '',
                    'hidden'
                ]"
            >
                <div
                    class="h-full flex items-center"
                >
                    <VActionSpecial
                        @click="openVUserLogInSignUp('sign-up-section')"
                        prop-element="button"
                        prop-font-size="s"
                        prop-element-size="s"
                        type="button"
                        class="w-full"
                    >
                        <span class="mx-auto px-2">
                            <FontAwesomeIcon icon="fas fa-right-to-bracket" class="sm:pr-2"/>
                            <span>Sign up</span>
                        </span>
                    </VActionSpecial>
                </div>
            </div>

            <!--nav menu opener-->
            <div
                ref="nav_menu_opener"
                class="col-start-4 col-span-1 lg:col-start-8 lg:col-span-1"
            >
                <!--not logged in-->
                <VActionText
                    @click="pop_up_manager_store.openPopup({context: 'nav_menu', kwargs: null})"
                    prop-element="button"
                    type="button"
                    :propIsIconOnly="true"
                    class="w-full h-full"
                >
                    <!--burger-->
                    <div class="w-full h-full relative">
                        <div
                            :class="[
                                pop_up_manager_store.isNavMenuOpen ? 'rotate-45' : 'translate-y-2 rotate-0',
                                'absolute left-0 right-0 top-0 bottom-0 m-auto w-5 h-0.5 bg-theme-black dark:bg-dark-theme-white-2 transition-all',
                            ]"
                        >
                        </div>
                        <div
                            :class="[
                                pop_up_manager_store.isNavMenuOpen ? 'opacity-0' : 'opacity-100',
                                'absolute left-0 right-0 top-0 bottom-0 m-auto w-5 h-0.5 bg-theme-black dark:bg-dark-theme-white-2 transition-all',
                            ]"
                        >
                        </div>
                        <div
                            :class="[
                                pop_up_manager_store.isNavMenuOpen ? '-rotate-45' : '-translate-y-2 rotate-0',
                                'absolute left-0 right-0 top-0 bottom-0 m-auto w-5 h-0.5 bg-theme-black dark:bg-dark-theme-white-2 transition-all',
                            ]"
                        >
                        </div>
                        <span class="sr-only">more navigation options</span>
                    </div>
                </VActionText>
            </div>
        </nav>

        <!--relevant popups-->
        <div class="w-full h-0 flex flex-col">

            <!--nav menu-->
            <!--don't show when lg and propIsLoggedIn, because the button to open will become a URL-->
            <TransitionFade>
                <div
                    v-show="pop_up_manager_store.isNavMenuOpen"
                    class="w-full h-0 absolute grid grid-cols-4 sm:grid-cols-8 lg:grid-cols-10 xl:grid-cols-12"
                >

                    <!--extra area to click when nav menu is open-->
                    <div
                        class="h-0 relative row-span-1 col-start-1 col-span-1 sm:col-span-5 lg:col-span-7 xl:col-span-9 2xl:col-span-10"
                    >
                        <div
                            class="absolute w-full h-[calc(100vh-4.5rem)] bg-theme-light/90 dark:bg-theme-dark/90"
                        >
                        </div>
                    </div>

                    <!--menu itself-->
                    <div class="h-0 relative row-span-1 col-start-2 col-span-3 sm:col-start-6 sm:col-span-3 lg:col-start-8 lg:col-span-3 xl:col-start-10 xl:col-span-3 2xl:col-start-11 2xl:col-span-2">

                        <div
                            v-click-outside="{
                                bool_status_variable_or_callback: pop_up_manager_store.closeNavMenuPopup,
                                refs_to_exclude: ['nav_menu_opener']
                            }"
                            class="absolute w-full h-[calc(100vh-4.5rem)] overflow-auto px-2 md:px-4 pb-10 bg-theme-nav dark:bg-dark-theme-nav    border-l border-theme-gray-2 dark:border-transparent"
                        >
                            <!--profile area-->
                            <div class="py-2 dark:text-dark-theme-white-1">

                                <!--logged in, can click to view profile-->
                                <VActionText
                                    v-if="propIsLoggedIn"
                                    prop-element="a"
                                    :prop-is-icon-only="false"
                                    :href="getProfileURL()"
                                    class="w-full h-fit py-10"
                                >
                                    <div class="w-full flex flex-col">
                                        <FontAwesomeIcon fixed-width icon="fas fa-circle-user" class="text-2xl mx-auto"/>
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
                                    <FontAwesomeIcon fixed-width icon="fas fa-circle-user" class="text-2xl mx-auto"/>
                                    <span class="max-w-full h-fit mx-auto text-xl font-light break-words">
                                        <span>Not logged in</span>
                                    </span>
                                </div>
                            </div>

                            <!--divider-->
                            <div class="pb-6">
                                <div class="w-full h-[1px] bg-theme-gray-2 dark:bg-dark-theme-gray-2 mx-auto"></div>
                            </div>

                            <!--log in / sign up / dark mode-->
                            <div
                                v-if="propIsLoggedIn === false"
                                class="h-fit flex flex-col gap-1"
                            >
                                <!--log in-->
                                <VActionText
                                    prop-element="a"
                                    href="/login"
                                    prop-font-size="s"
                                    prop-element-size="s"
                                    :prop-is-icon-only="false"
                                    class=""
                                >
                                    <div class="h-full flex flex-row">
                                        <div class="pl-2 pr-4 md:pr-6 flex items-center">
                                            <FontAwesomeIcon fixed-width icon="fas fa-circle-user" class="pt-0.5 mx-auto"/>
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
                                    class=""
                                >
                                    <div class="h-full flex flex-row">
                                        <div class="pl-2 pr-4 md:pr-6 flex items-center">
                                            <FontAwesomeIcon fixed-width icon="fas fa-right-to-bracket" class="pt-0.5 mx-auto"/>
                                        </div>
                                        <div class="flex items-center">
                                            <span class="text-left break-all">
                                                Sign up
                                            </span>
                                        </div>
                                    </div>
                                </VActionText>

                                <!--about-->
                                <VActionText
                                    prop-element="a"
                                    href="/about"
                                    prop-font-size="s"
                                    prop-element-size="s"
                                    :prop-is-icon-only="false"
                                    class=""
                                >
                                    <div class="h-full flex flex-row">
                                        <div class="pl-2 pr-4 md:pr-6 flex items-center">
                                            <FontAwesomeIcon fixed-width icon="fas fa-question" class="pt-0.5 mx-auto"/>
                                        </div>
                                        <div class="flex items-center">
                                            <span class="text-left break-all">
                                                About
                                            </span>
                                        </div>
                                    </div>
                                </VActionText>

                                <!--light/dark theme-->
                                <div class="flex flex-row">
                                    <div class="pl-2 pr-4 md:pr-6 flex items-center">
                                        <FontAwesomeIcon fixed-width icon="fas fa-moon" class="mx-auto"/>
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
                            </div>

                            <!--main URLs-->
                            <div
                                v-if="propIsLoggedIn === true"
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
                                            <div class="pl-2 pr-4 md:pr-6 flex items-center">
                                                <FontAwesomeIcon fixed-width icon="fas fa-microphone-lines" class="pt-0.5 mx-auto"/>
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
                                            <div class="pl-2 pr-4 md:pr-6 flex items-center">
                                                <FontAwesomeIcon fixed-width icon="fas fa-thumbs-up" class="mx-auto"/>
                                            </div>
                                            <div class="flex items-center">
                                                <span class="text-left break-all">
                                                    Likes &#38; dislikes
                                                </span>
                                            </div>
                                        </div>
                                    </VActionText>
                                </div>

                                <!--following-->
                                <div
                                    class="h-fit grid"
                                >
                                    <VActionText
                                        prop-element="a"
                                        href="/following"
                                        prop-font-size="s"
                                        prop-element-size="s"
                                        :prop-is-icon-only="false"
                                    >
                                        <div class="h-full flex flex-row">
                                            <div class="pl-2 pr-4 md:pr-6 flex items-center">
                                                <FontAwesomeIcon fixed-width icon="fas fa-star" class="pt-0.5 mx-auto"/>
                                            </div>
                                            <div class="flex items-center">
                                                <span class="text-left break-all">
                                                    Following
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
                                            <div class="pl-2 pr-4 md:pr-6 flex items-center">
                                                <FontAwesomeIcon fixed-width icon="fas fa-ban" class="pt-0.5 mx-auto"/>
                                            </div>
                                            <div class="flex items-center">
                                                <span class="text-left break-all">
                                                    Block list
                                                </span>
                                            </div>
                                        </div>
                                    </VActionText>
                                </div>

                                <!--about-->
                                <VActionText
                                    prop-element="a"
                                    href="/about"
                                    prop-font-size="s"
                                    prop-element-size="s"
                                    :prop-is-icon-only="false"
                                    class=""
                                >
                                    <div class="h-full flex flex-row">
                                        <div class="pl-2 pr-4 md:pr-6 flex items-center">
                                            <FontAwesomeIcon fixed-width icon="fas fa-question" class="pt-0.5 mx-auto"/>
                                        </div>
                                        <div class="flex items-center">
                                            <span class="text-left break-all">
                                                About
                                            </span>
                                        </div>
                                    </div>
                                </VActionText>

                                <!--light/dark theme-->
                                <div class="flex flex-row">
                                    <div class="pl-2 pr-4 md:pr-6 flex items-center">
                                        <FontAwesomeIcon fixed-width icon="fas fa-moon" class="mx-auto"/>
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

                                <!--log out-->
                                <div
                                    v-if="propIsLoggedIn === true"
                                    class="h-fit flex flex-col"
                                >
                                    <VActionText
                                        v-if="propIsLoggedIn === true"
                                        :prop-is-enabled="!is_log_out_loading"
                                        @click="logOut()"
                                        prop-element="button"
                                        prop-font-size="s"
                                        prop-element-size="s"
                                        :prop-is-icon-only="false"
                                        type="button"
                                        class="w-full"
                                    >
                                        <div class="h-full flex flex-row">
                                            <div class="pl-2 pr-4 md:pr-6 flex items-center">
                                                <VLoading
                                                    v-if="is_log_out_loading"
                                                    prop-element-size="s"
                                                    class="mx-auto"
                                                />
                                                <span v-else class="mx-auto">
                                                    <FontAwesomeIcon fixed-width icon="fas fa-door-open"/>
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

                            <!--copyright-->
                            <div class="w-full text-center text-sm pt-10 flex flex-col">
                                <span id="nav-copyright">Copyright &copy; 2025</span>
                                <span>Adrian C.</span>
                            </div>
                        </div>
                    </div>
                </div>
            </TransitionFade>

            <!--login/signup popup, login required popup-->
            <!--no v-click-outside, because these are more important-->
            <!--furthermore, v-click-outside here cannot target VAudioClipTools for login_required-->
            <div
                v-if="!propIsLoggedIn"
                class="h-0 relative"
            >
                <div
                    v-show="pop_up_manager_store.isLogInOpen || pop_up_manager_store.isSignUpOpen"
                    class="absolute hidden lg:flex flex-row w-full h-[calc(100vh-4.5rem)] bg-theme-light/90 dark:bg-theme-dark/90"
                >
                    <div
                        v-show="pop_up_manager_store.isLogInOpen"
                        class="sm:w-3/4 md:w-2/4 xl:w-5/12 2xl:w-4/12 max-h-[90%] min-h-fit m-auto px-4 border border-theme-gray-2 dark:border-dark-theme-gray-2 bg-theme-light dark:bg-theme-dark rounded-lg overflow-y-auto"
                    >
                        <TransitionFade>
                            <keep-alive>
                                <VUserLogInSignUp
                                    v-if="pop_up_manager_store.isLogInOpen"
                                    propRequestedSection="log-in-section"
                                    :propIsForStaticPage="false"
                                />
                            </keep-alive>
                        </TransitionFade>
                    </div>
                    <div
                        v-show="pop_up_manager_store.isSignUpOpen"
                        class="sm:w-3/4 md:w-2/4 xl:w-5/12 2xl:w-4/12 max-h-[90%] min-h-fit m-auto px-4 border border-theme-gray-2 dark:border-dark-theme-gray-2 bg-theme-light dark:bg-theme-dark rounded-lg overflow-y-auto"
                    >
                        <TransitionFade>
                            <keep-alive>
                                <VUserLogInSignUp
                                    v-if="pop_up_manager_store.isSignUpOpen"
                                    propRequestedSection="sign-up-section"
                                    :propIsForStaticPage="false"
                                />
                            </keep-alive>
                        </TransitionFade>
                    </div>
                </div>
                <div
                    v-show="pop_up_manager_store.isLoginRequiredOpen"
                    class="absolute flex items-center w-full h-[calc(100vh-4.5rem)] bg-theme-light/90 dark:bg-theme-dark/90"
                >
                    <div
                        class="w-5/6 sm:w-fit max-h-[90%] min-h-fit m-auto"
                    >
                        <VPopupLoginRequired
                            @force-close="pop_up_manager_store.closeLoginRequiredPopup()"
                        />
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    // import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VActionText from '@/components/small/VActionText.vue';
    import VActionSpecial from '@/components/small/VActionSpecial.vue';
    import VLoading from '@/components/small/VLoading.vue';
    import VSwitch from '@/components/small/VSwitch.vue';
    // import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
    import VPopupLoginRequired from '@/components/medium/VPopupLoginRequired.vue';
    import VUserLogInSignUp from './VUserLogInSignUp.vue';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faWaveSquare } from '@fortawesome/free-solid-svg-icons/faWaveSquare';
    import { faComment } from '@fortawesome/free-solid-svg-icons/faComment';
    import { faComments } from '@fortawesome/free-solid-svg-icons/faComments';
    import { faRightToBracket } from '@fortawesome/free-solid-svg-icons/faRightToBracket';

    import { faCircleUser } from '@fortawesome/free-solid-svg-icons/faCircleUser';
    import { faBan } from '@fortawesome/free-solid-svg-icons/faBan';
    import { faDoorOpen } from '@fortawesome/free-solid-svg-icons/faDoorOpen';
    import { faMicrophoneLines } from '@fortawesome/free-solid-svg-icons/faMicrophoneLines';
    import { faThumbsUp as fasThumbsUp } from '@fortawesome/free-solid-svg-icons/faThumbsUp';
    import { faMoon } from '@fortawesome/free-solid-svg-icons/faMoon';
    import { faQuestion } from '@fortawesome/free-solid-svg-icons/faQuestion';
    import { faStar } from '@fortawesome/free-solid-svg-icons/faStar';

    library.add(
        faWaveSquare, faComment, faComments, faCircleUser,
        faRightToBracket, faBan, faDoorOpen, faMicrophoneLines,
        fasThumbsUp, faMoon, faQuestion, faStar
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
    import { useUserBlocksStore } from '@/stores/UserBlocksStore';
    import { useUserFollowsStore } from '@/stores/UserFollowsStore';
    import axios from 'axios';

    export default defineComponent({
        name: 'VNavBar',
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
            propIsLoggedIn: {
                type: Boolean,
                required: true,
            },
            propUsername: {
                type: String,
                required: true,
            },
        },
        computed: {
            canShowLogInSignUpAtNav() : boolean {
                return (
                    this.propIsLoggedIn === false &&
                    this.is_currently_log_in_sign_up_static_page === false &&
                    this.pop_up_manager_store.getCurrentPopupContext !== 'log_in' &&
                    this.pop_up_manager_store.getCurrentPopupContext !== 'sign_up'
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

                if(this.propUsername.length > 0){

                    return window.location.origin + '/user/' + this.propUsername;
                }

                return "";
            },
            openVUserLogInSignUp(section:"log-in-section"|"sign-up-section") : void {

                if(section === 'log-in-section'){

                    this.pop_up_manager_store.openPopup({context: 'log_in', kwargs: null});

                }else if(section === 'sign-up-section'){

                    this.pop_up_manager_store.openPopup({context: 'sign_up', kwargs: null});
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
                        useUserBlocksStore(),
                        useUserFollowsStore(),
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
            handleCopyright() : void {

                const target_element = document.getElementById('nav-copyright');

                if(target_element === null){

                    console.error('Missing copyright element.');
                }

                const current_year = new Date().getUTCFullYear();

                //.textContent does not decode, so use .innerHTML instead

                if(current_year > 2025){

                    target_element!.innerHTML = 'Copyright &copy; 2025 - ' + current_year.toString();
                }
            }
        },
        beforeMount(){

            this.handleIsLogInSignUpStaticPage();
        },
        mounted(){

            this.handleCopyright();
        }
    });
</script>