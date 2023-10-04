<template>
    <NavBar
        :propUsername="username"
    />

    <!--all popups belong here so we can ensure that only one shows at a time-->
    <div class="w-full h-0 relative">
        <TransitionFade>
            <div
                v-if="pop_up_manager_store.getIsUserLogInSignUpOpen"
                class="absolute hidden lg:flex flex-row w-full h-[calc(100vh-4.5rem)] bg-theme-light/60 backdrop-blur"
            >
                <div
                    class="lg:w-2/6 xl:w-2/6 max-h-[90%] min-h-fit m-auto px-4 border border-theme-light-gray bg-theme-light shadow-xl rounded-lg overflow-y-auto"
                >
                    <UserLogInSignUp
                        :propRequestedSection="pop_up_manager_store.getRequestedSection"
                        :propIsForStaticPage="false"
                    />
                </div>
            </div>
            <div
                v-else-if="pop_up_manager_store.getIsLoginRequiredPromptOpen"
                class="absolute flex items-center w-full h-[calc(100vh-4.5rem)] bg-theme-light/60 backdrop-blur"
            >
                <div
                    v-click-outside="{
                        var_name_for_element_bool_status: forceCloseLoginRequiredPromptMenu,
                        refs_to_exclude: []
                    }"
                    class="w-5/6 sm:w-fit max-h-[90%] min-h-fit m-auto px-4 pb-14 border border-theme-light-gray bg-theme-light shadow-xl rounded-lg"
                >
                    <VLoginRequiredPrompt
                        @is-open="forceCloseLoginRequiredPromptMenu()"
                    />
                </div>
            </div>
        </TransitionFade>
    </div>

    <!--toasts-->
    <TransitionFade>

        <!--ensure pop-ups don't clash with toasts-->
        <div
            v-show="!pop_up_manager_store.getHasPopUpOpen"
            class="w-0 h-0"
        >
            <VNotiwind/>
        </div>
    </TransitionFade>

    <!--tests-->
    <TestingStuff/>
</template>


<script setup lang="ts">
    import VNotiwind from '@/components/medium/VNotiwind.vue';
    import TestingStuff from '@/components/main/TestingStuff.vue';
    import NavBar from '@/components/main/NavBar.vue';
    import UserLogInSignUp from '@/components/main/UserLogInSignUp.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VLoginRequiredPrompt from '@/components/medium/VLoginRequiredPrompt.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import { getDataFromTemplateJSONScript } from '@/helper_functions';
    import { usePageRefreshTriggerStore } from '@/stores/PageRefreshTriggerStore';
    import { usePopUpManagerStore } from '@/stores/PopUpManagerStore';
    import { notify } from 'notiwind';

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
            forceCloseLoginRequiredPromptMenu() : void {

                this.pop_up_manager_store.toggleIsLoginRequiredPromptOpen(false);
            },
            checkHasCookiesConsent() : void {

                if(this.pop_up_manager_store.getIsLoggedIn === false || localStorage.getItem('user_consents_to_cookies') !== null){

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
        mounted(){

            this.checkHasCookiesConsent();
        },
        beforeUnmount(){

            window.removeEventListener('keydown', this.pop_up_manager_store.forceCloseAllPopUps);
        }
    });
</script>


