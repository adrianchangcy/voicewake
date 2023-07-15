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
                class="absolute flex w-full h-[calc(100vh-4.5rem)] mx-auto bg-theme-light/60 backdrop-blur"
            >
                <div
                    class="w-[90%] sm:w-2/4 lg:w-2/6 xl:w-2/6 max-h-[90%] min-h-fit m-auto px-4 border border-theme-light-gray bg-theme-light shadow-xl rounded-lg overflow-y-auto"
                >
                    <VUserUsername
                        @newUsername="handleNewUsername($event)"
                    />
                </div>
            </div>
            <div
                v-else-if="is_user_log_in_sign_up_open === true"
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

    <TestingStuff/>
</template>


<script setup lang="ts">
    import TestingStuff from '@/components/main/TestingStuff.vue';
    import NavBar from '@/components/main/NavBar.vue';
    import UserLogInSignUp from '@/components/main/UserLogInSignUp.vue';
    import VUserUsername from '@/components/medium/VUserUsername.vue';
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
            handleNewUsername(new_value:string) : void {

                this.must_set_username = false;
                this.username = new_value;
            }
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


