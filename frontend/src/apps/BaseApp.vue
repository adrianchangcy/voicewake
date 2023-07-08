<template>
    <NavBar
        :propIsLoggedIn="is_logged_in"
        :propUsername="username"
        @emitToOpenUserLogInSignUp="handleOpenUserLogInSignUp($event)"
    />

    <!--all popups belong here so we can ensure that only one shows at a time-->
    <div class="w-full h-0 relative">
        <TransitionFade>
            <div
                v-if="must_set_username === true"
                class="absolute w-full h-[calc(100vh-4.5rem)] mx-auto bg-theme-light/60 backdrop-blur"
            >
                <UserUsername/>
            </div>
            <div
                v-else-if="is_user_log_in_sign_up_open === true"
                class="absolute hidden lg:flex flex-row w-full h-[calc(100vh-4.5rem)] bg-theme-light/60 backdrop-blur"
            >
                <!--10.25rem is precisely the height, as of 2023-07-05-->
                <div
                    v-click-outside="{
                        var_name_for_element_bool_status: 'is_user_log_in_sign_up_open',
                        refs_to_exclude: []
                    }"
                    class="lg:w-2/6 xl:w-2/6 h-[90%] m-auto px-4 border border-theme-light-gray bg-theme-light shadow-xl rounded-lg overflow-y-auto"
                >
                    <UserLogInSignUp
                        :propRequestedSection="requested_section"
                        :propIsForStaticPage="false"
                        @emitManualClose="handleOpenUserLogInSignUp($event)"
                    />
                </div>
            </div>
        </TransitionFade>
    </div>

    <Testing/>
</template>


<script setup lang="ts">
    import Testing from '@/components/main/Testing.vue';
    import NavBar from '@/components/main/NavBar.vue';
    import UserLogInSignUp from '@/components/main/UserLogInSignUp.vue';
    import UserUsername from '@/components/main/UserUsername.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import { getDataFromTemplate } from '@/helper_functions';

    export default defineComponent({
        name: 'BaseApp',
        data(){
            return {
                is_logged_in: false,
                username: "",
                must_set_username: false,

                requested_section: "",
                is_user_log_in_sign_up_open: false
            };
        },
        methods: {
            handleOpenUserLogInSignUp(section:string) : void {

                this.requested_section = section;

                //"..." means open, "" means close
                this.is_user_log_in_sign_up_open = section.length > 0;
            },
        },
        beforeMount(){

            //is logged in
            this.is_logged_in = getDataFromTemplate("data-is-authenticated") as boolean;

            //username
            const username = getDataFromTemplate("data-username") as string|null;

            if(username !== null){

                this.username = username;

            }else if(username === null && this.is_logged_in === true){

                this.must_set_username = true;
            }
        },
    });
</script>


