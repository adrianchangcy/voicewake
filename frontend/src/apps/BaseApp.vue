<template>
    <NavBar
        :propIsLoggedIn="is_logged_in"
        :propUsername="username"
        @emitIsNavBarOpen="handleIsNavBarOpen($event)"
        @emitToOpenUserLogInSignUp="handleOpenUserLogInSignUp($event)"
    />

    <!--all popups belong here so we can ensure that only one shows at a time-->
    <div class="w-full h-0 relative">
        <TransitionFade>
            <div
                v-if="is_user_log_in_sign_up_open === true"
                class="absolute hidden lg:flex flex-row w-full h-[calc(100vh-4.5rem)] bg-theme-light/60 backdrop-blur"
            >
                <div
                    class="lg:w-2/6 xl:w-2/6 max-h-[90%] min-h-fit m-auto px-4 border border-theme-light-gray bg-theme-light shadow-xl rounded-lg overflow-y-auto"
                >
                    <UserLogInSignUp
                        :propRequestedSection="requested_section"
                        :propIsForStaticPage="false"
                        @isClosed="handleOpenUserLogInSignUp($event)"
                    />
                </div>
            </div>
        </TransitionFade>
    </div>

    <!--toasts-->
    <TransitionFade>

        <!--ensure pop-ups don't clash with toasts-->
        <div
            v-show="!is_nav_bar_open"
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
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import { getDataFromTemplateJSONScript } from '@/helper_functions';
    import { usePageRefreshTriggerStore } from '@/stores/PageRefreshTriggerStore';

    export default defineComponent({
        name: 'BaseApp',
        data(){
            return {
                page_refresh_trigger_store: usePageRefreshTriggerStore(),

                is_nav_bar_open: false,
                is_logged_in: false,
                username: "",

                requested_section: "",
                is_user_log_in_sign_up_open: false
            };
        },
        methods: {
            handleIsNavBarOpen(new_value:boolean) : void {

                this.is_nav_bar_open = new_value;
            },
            handleOpenUserLogInSignUp(section:string) : void {

                this.requested_section = section;

                //"..." means open, "" means close
                this.is_user_log_in_sign_up_open = section.length > 0;
            },
        },
        beforeMount(){

            //is logged in
            this.is_logged_in = getDataFromTemplateJSONScript("data-user-is-authenticated") as boolean;

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
        },
    });
</script>


