<template>
    <NavBar
        :propUsername="username"
    />

    <!--all popups belong here so we can ensure that only one shows at a time-->
    <div class="w-full h-0 relative">
        <TransitionGroupFade>
            <div
                v-show="pop_up_manager_store.isUserLogInOpen || pop_up_manager_store.isUserSignUpOpen"
                class="absolute hidden lg:flex flex-row w-full h-[calc(100vh-4.5rem)] bg-theme-light/60 backdrop-blur"
            >
                <div
                    v-show="pop_up_manager_store.isUserLogInOpen"
                    v-click-outside="{
                        bool_status_variable_or_callback: forceCloseLogIn,
                        refs_to_exclude: []
                    }"
                    class="lg:w-2/6 xl:w-2/6 max-h-[90%] min-h-fit m-auto px-4 border border-theme-gray-2 bg-theme-light shadow-xl rounded-lg overflow-y-auto"
                >
                    <TransitionFade>
                        <keep-alive>
                            <UserLogInSignUp
                                v-if="pop_up_manager_store.isUserLogInOpen"
                                propRequestedSection="log-in-section"
                                :propIsForStaticPage="false"
                            />
                        </keep-alive>
                    </TransitionFade>
                </div>
                <div
                    v-show="pop_up_manager_store.isUserSignUpOpen"
                    v-click-outside="{
                        bool_status_variable_or_callback: forceCloseSignUp,
                        refs_to_exclude: []
                    }"
                    class="lg:w-2/6 xl:w-2/6 max-h-[90%] min-h-fit m-auto px-4 border border-theme-gray-2 bg-theme-light shadow-xl rounded-lg overflow-y-auto"
                >
                    <TransitionFade>
                        <keep-alive>
                            <UserLogInSignUp
                                v-if="pop_up_manager_store.isUserSignUpOpen"
                                propRequestedSection="sign-up-section"
                                :propIsForStaticPage="false"
                            />
                        </keep-alive>
                    </TransitionFade>
                </div>
            </div>
            <div
                v-if="pop_up_manager_store.isLoginRequiredPromptOpen"
                class="absolute flex items-center w-full h-[calc(100vh-4.5rem)] bg-theme-light/60 backdrop-blur"
            >
                <div
                    v-click-outside="{
                        bool_status_variable_or_callback: forceCloseLoginRequiredPromptMenu,
                        refs_to_exclude: []
                    }"
                    class="w-5/6 sm:w-fit max-h-[90%] min-h-fit m-auto px-4 pb-14 border border-theme-gray-2 bg-theme-light shadow-xl rounded-lg"
                >
                    <VLoginRequiredPrompt
                        @force-close="forceCloseLoginRequiredPromptMenu()"
                        :prop-prompt-text="pop_up_manager_store.getLoginRequiredPromptText"
                    />
                </div>
            </div>
        </TransitionGroupFade>
    </div>

    <!--toasts-->
    <!--if pop-ups clash with toasts, do v-if here-->
    <div
        class="w-0 h-0"
    >
        <VNotiwind/>
    </div>
</template>


<script setup lang="ts">
    import VNotiwind from '@/components/medium/VNotiwind.vue';
    import NavBar from '@/components/main/NavBar.vue';
    import UserLogInSignUp from '@/components/main/UserLogInSignUp.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VLoginRequiredPrompt from '@/components/medium/VLoginRequiredPrompt.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import { getDataFromTemplateJSONScript } from '@/helper_functions';
    import { usePageRefreshTriggerStore } from '@/stores/PageRefreshTriggerStore';
    import { usePopUpManagerStore } from '@/stores/PopUpManagerStore';
    import { notify } from 'notiwind';
    import { axiosCSRFSetup } from '@/helper_functions';

    export default defineComponent({
        name: 'BaseApp',
        data(){
            return {
                page_refresh_trigger_store: usePageRefreshTriggerStore(),
                pop_up_manager_store: usePopUpManagerStore(),

                username: "",
            };
        },
        computed: {
        },
        methods: {
            forceCloseLogIn() : void {

                this.pop_up_manager_store.toggleIsUserLogInOpen(false);
            },
            forceCloseSignUp() : void {

                this.pop_up_manager_store.toggleIsUserSignUpOpen(false);
            },
            forceCloseLoginRequiredPromptMenu() : void {

                this.pop_up_manager_store.toggleIsLoginRequiredPromptOpen(false);
            },
            checkHasCookiesConsent() : void {

                //currently not used
                //only need consent if collecting user data

                if(this.pop_up_manager_store.isLoggedIn === false || localStorage.getItem('user_consents_to_cookies') !== null){

                    return;
                }

                notify({
                    icon: 'fas fa-cookie-bite',
                    title: 'Cookies Consent',
                    text: 'We use cookies so you can stay logged in.',
                    type: 'generic',
                    button_1: {
                        text: 'Accept',
                        callback: this.setCookiesConsent,
                    },
                }, -1);
            },
            setCookiesConsent() : void {

                localStorage.setItem('user_consents_to_cookies', JSON.stringify(true));
            },
        },
        beforeMount(){

            axiosCSRFSetup();

            //is logged in
            this.pop_up_manager_store.setIsLoggedIn(
                getDataFromTemplateJSONScript("data-user-is-authenticated") as boolean
            );

            //username
            const username = getDataFromTemplateJSONScript("data-user-username") as string|null;

            if(username !== null){

                this.username = username;
            }

            //refresh all tabs when necessary
            //provided that every tab has BaseApp.vue
            this.page_refresh_trigger_store.$subscribe(()=>{

                this.page_refresh_trigger_store.resetRefreshContext();

                window.location.replace(window.location.href);
            });

            //allow use of ESC key to close popups
            window.addEventListener('keydown', this.pop_up_manager_store.forceCloseAllPopUps);

        },
        beforeUnmount(){

            window.removeEventListener('keydown', this.pop_up_manager_store.forceCloseAllPopUps);
        }
    });
</script>


