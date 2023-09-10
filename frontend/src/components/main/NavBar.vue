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
                    class="w-full h-full"
                >
                    <i class="fas fa-wave-square mx-auto"></i>
                    <span class="sr-only">home</span>
                </VActionTextOnly>
            </div>

            <!--start-->
            <div class="col-start-2 col-span-1 sm:col-start-3 sm:col-span-2 lg:col-start-4 lg:col-span-1">
                <VActionTextOnly
                    propElement="a"
                    propFontSize="m"
                    href="/start"
                    :propIsIconOnly="true"
                    class="w-full h-full"
                >
                    <span class="block mx-auto sm:pb-1">
                        <i class="fas fa-comment sm:pr-2"></i>
                        <span class="hidden font-normal sm:inline">Start</span>
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
                    :propIsIconOnly="true"
                    class="w-full h-full"
                >
                    <span class="block mx-auto sm:pb-1">
                        <i class="fas fa-comments sm:pr-2"></i>
                        <span class="hidden font-normal sm:inline">Reply</span>
                    </span>
                    <span class="sr-only sm:hidden">reply to events</span>
                </VActionTextOnly>
            </div>

            <!--mobile, always show-->
            <div
                ref="nav_main_more_button_1"
                class="block lg:hidden col-start-4 col-span-1 sm:col-start-8"
            >
                <VActionTextOnly
                    @click.stop="toggleNavMainMore()"
                    propElement="button"
                    type="button"
                    :propIsIconOnly="true"
                    class="w-full h-full"
                >
                    <!--burger-->
                    <div class="w-full h-full grid grid-rows-3 grid-flow-row      justify-items-center place-items-center">
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
                </VActionTextOnly>
            </div>

            <!--desktop, if logged in-->
            <!--not using v-if because we need the ref-->
            <div
                ref="nav_main_more_button_2"
                :class="[
                    propIsLoggedIn === true ? 'hidden lg:block lg:col-start-8 lg:col-span-1' : 'hidden'
                ]"
            >
                <VActionTextOnly
                    @click.stop="toggleNavMainMore()"
                    propElement="button"
                    type="button"
                    :propIsIconOnly="true"
                    class="w-full h-full"
                >
                    <span class="mx-auto">
                        <i class="fas fa-user text-xl"></i>
                        <!--do this so user icon stays truly centered-->
                        <span class="relative w-0">
                            <i
                                :class="[
                                    is_nav_main_more_open ? '-rotate-180' : 'rotate-0',
                                    'fas fa-chevron-down text-xs transition-transform h-fit absolute top-0 bottom-0 left-2 m-auto'
                                ]"
                            ></i>
                        </span>
                    </span>
                    <span class="sr-only">you are logged in, more navigation options</span>
                </VActionTextOnly>
            </div>

            <!--desktop, if not logged in, show log in option-->
            <div
                v-if="propIsLoggedIn === false"
                class="hidden lg:block lg:col-start-7 lg:col-span-1"
            >
                <VActionTextOnly
                    v-if="is_currently_log_in_sign_up_static_page"
                    propElement="a"
                    href="/login"
                    propFontSize="m"
                    class="w-full h-full"
                >
                    <span class="block mx-auto">
                        <i class="fas fa-circle-user sm:pr-2"></i>
                        <span>Log in</span>
                    </span>
                </VActionTextOnly>
                <VActionTextOnly
                    v-else
                    @click.stop="emitToOpenUserLogInSignUp('log-in-section')"
                    propElement="button"
                    propFontSize="m"
                    type="button"
                    class="w-full h-full"
                >
                    <span class="block mx-auto">
                        <i class="fas fa-circle-user sm:pr-2"></i>
                        <span>Log in</span>
                    </span>
                </VActionTextOnly>
            </div>

            <!--desktop, if not logged in, show sign up option-->
            <div
                v-if="propIsLoggedIn === false"
                class="hidden lg:block lg:col-start-8 col-span-1"
            >
                <VActionSpecial
                    v-if="is_currently_log_in_sign_up_static_page"
                    propElement="a"
                    href="/signup"
                    propElementSize="s"
                    class="w-full h-full"
                >
                    <span class="block mx-auto text-xl font-medium">
                        <i class="fas fa-right-to-bracket sm:pr-2"></i>
                        <span>Sign up</span>
                    </span>
                </VActionSpecial>
                <VActionSpecial
                    v-else
                    @click.stop="emitToOpenUserLogInSignUp('sign-up-section')"
                    propElement="button"
                    type="button"
                    propElementSize="s"
                    class="w-full h-full"
                >
                    <span class="block mx-auto text-xl font-medium">
                        <i class="fas fa-right-to-bracket sm:pr-2"></i>
                        <span>Sign up</span>
                    </span>
                </VActionSpecial>
            </div>
        </nav>

        <!--more nav options, same grid layout as main nav grid-->
        <div class="h-0 grid grid-cols-4 sm:grid-cols-8">

            <!--extra area to click when nav menu is open-->
            <div
                :class="propIsLoggedIn === false ? 'lg:hidden' : ''"
                class="relative col-start-1 col-span-1 sm:col-span-5 xl:col-span-6"
            >
                <TransitionFade>
                    <div
                        v-show="is_nav_main_more_open"
                        class="absolute w-full h-[calc(100vh-4.5rem)] bg-theme-light/60 backdrop-blur"
                    >
                    </div>
                </TransitionFade>
            </div>

            <!--nav menu-->
            <!--don't show when lg and propIsLoggedIn, because the button to open will become a URL-->
            <div
                :class="propIsLoggedIn === false ? 'lg:hidden' : ''"
                class="relative col-start-2 col-span-3 sm:col-start-6 sm:col-span-3 xl:col-start-7 xl:col-span-2"
            >
                <TransitionFade>
                    <!--uses calc to minus fixed height of navbar at base.html-->
                    <div
                        v-show="is_nav_main_more_open"
                        v-click-outside="{
                            var_name_for_element_bool_status: 'is_nav_main_more_open',
                            refs_to_exclude: ['nav_main_more_button_1', 'nav_main_more_button_2']
                        }"
                        class="absolute w-full h-[calc(100vh-4.5rem)] flex flex-col overflow-hidden p-2 border-l border-theme-light-gray bg-theme-light"
                    >

                        <!--profile area-->
                        <div class="pt-12 flex flex-col">
                            <i class="fas fa-user text-base w-fit h-fit mx-auto"></i>
                            <span class="max-w-full h-fit mx-auto text-xl font-light break-words">
                                <span v-if="propIsLoggedIn">{{ propUsername }}</span>
                                <span v-else>Not logged in</span>
                            </span>
                        </div>

                        <!--divider-->
                        <div class="w-[75%] h-[1px] mt-14 mb-12 bg-theme-light-gray mx-auto"></div>

                        <!--account options-->
                        <div class="h-fit grid grid-rows-2 gap-2">

                            <!--log in-->
                            <VActionTextOnly
                                v-if="propIsLoggedIn === false"
                                propElement="a"
                                href="/login"
                                propFontSize="m"
                                propElementSize="s"
                                class="row-start-1 row-span-1 w-full"
                            >
                                <div class="w-full h-full grid grid-cols-4">
                                    <div class="col-span-1 flex items-center">
                                        <i class="fas fa-circle-user w-fit h-fit mx-auto"></i>
                                    </div>
                                    <div class="col-span-3 flex items-center">
                                        <span class="text-left font-normal break-all">
                                            Log in
                                        </span>
                                    </div>
                                </div>
                            </VActionTextOnly>

                            <!--sign up-->
                            <VActionTextOnly
                                v-if="propIsLoggedIn === false"
                                propElement="a"
                                href="/signup"
                                propFontSize="m"
                                propElementSize="s"
                                class="row-start-2 row-span-1 w-full"
                            >
                                <div class="w-full h-full grid grid-cols-4">
                                    <div class="col-span-1 flex items-center">
                                        <i class="fas fa-right-to-bracket w-fit h-fit mx-auto"></i>
                                    </div>
                                    <div class="col-span-3 flex items-center">
                                        <span class="text-left font-normal break-all">
                                            Sign up
                                        </span>
                                    </div>
                                </div>
                            </VActionTextOnly>

                            <!--log out-->
                            <VActionTextOnly
                                v-if="propIsLoggedIn === true"
                                :propIsEnabled="!is_log_out_loading"
                                @click.stop="logOut()"
                                propElement="button"
                                propFontSize="m"
                                propElementSize="s"
                                type="button"
                                class="row-start-1 row-span-1 w-full"
                            >
                                <div class="w-full h-full grid grid-cols-4">
                                    <div class="col-span-1 flex items-center">
                                        <VLoading
                                            v-if="is_log_out_loading"
                                            propElementSize="s"
                                            class="mx-auto"
                                        />
                                        <span v-else class="mx-auto">
                                            <i class="fas fa-door-open"></i>
                                        </span>
                                    </div>
                                    <div class="col-span-3 flex items-center">
                                        <span class="text-left font-normal break-all">
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
    const axios = require('axios');

    export default defineComponent({
        name: 'NavBar',
        data(){
            return {
                page_refresh_trigger_store: usePageRefreshTriggerStore(),

                is_nav_main_more_open: false,
                is_log_out_loading: false,
                is_currently_log_in_sign_up_static_page: false,
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
        emits: [
            'emitToOpenUserLogInSignUp', 'emitIsNavBarOpen'
        ],
        watch: {
            is_nav_main_more_open(new_value:boolean){

                this.$emit('emitIsNavBarOpen', new_value);
            }
        },
        methods: {
            emitToOpenUserLogInSignUp(section:"log-in-section"|"sign-up-section") : void {

                this.is_nav_main_more_open = false;

                this.$emit('emitToOpenUserLogInSignUp', section);
            },
            toggleNavMainMore(force_close=false) : void {

                if(force_close === true){

                    this.is_nav_main_more_open = false;

                }else{

                    this.is_nav_main_more_open = !this.is_nav_main_more_open;
                }
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
            axiosSetup() : boolean {

                //your template must have {% csrf_token %}
                let token = document.getElementsByName("csrfmiddlewaretoken")[0];

                if(token === undefined){

                    console.log('CSRF not found.');
                    return false;
                }

                axios.defaults.headers.common['X-CSRFToken'] = (token as HTMLFormElement).value;
                axios.defaults.headers.post['Content-Type'] = 'multipart/form-data';
                return true;
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
        mounted(){

            this.axiosSetup();
        }
    });
</script>