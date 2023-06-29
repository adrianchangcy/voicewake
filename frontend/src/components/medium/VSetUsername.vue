<template>
    <VTitleXL class="py-8">
        <template #title>
            <span class="block text-center">
                Voicewake
            </span>
        </template>
        <template #titleDescription>
            <span class="block text-center">
                New user
            </span>
        </template>
    </VTitleXL>

    <p class="text-xl font-medium block">
        Set your username.
    </p>

    <VInput
        propElementId="set-username"
        propLabel="Username"
        propPlaceholder=""
        :propMaxLength="30"
        :propHasTextCounter="true"
        :propIsRequired="true"
        :propHasStatusText="true"
        :propStatusText="username_validation_status_text"
        :propIsError="username_validation_has_error"
        :propIsOk="username_is_ok === true"
        :propAllowWhitespace="false"
        @hasNewValue="validateUsername($event)"
        class="mt-6"
    />

    <!--main action-->
    <div class="mt-8 h-fit">
        <VActionSpecialM
            :propIsEnabled="username_is_ok"
            @click.stop="submitOTPForSignUp()"
            propElement="button"
            type="button"
            class="w-full"
        >
            <span class="mx-auto">Save</span>
        </VActionSpecialM>
    </div>
</template>


<script setup lang="ts">
    import VTitleXL from '@/components/small/VTitleXL.vue';
    import VInput from '@/components/small/VInput.vue';
    import VActionSpecialM from '@/components/small/VActionSpecialM.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    const axios = require('axios');

    export default defineComponent({
        name: "UserOptionsApp",
        data() {
            return {
                username_string:"",
                username_validation_status_text: "",
                username_validation_has_error: false,
                username_is_ok: false,
                username_check_timeout: null as number|null,
            };
        },
        methods: {
            validateUsername(new_value:String) : void {

                this.username_string = "";
                this.username_validation_status_text = "";
                this.username_validation_has_error = false;
                this.username_is_ok = false;

                //do nothing if there is no text
                if(new_value.length === 0){

                    return;
                }

                //has text
                this.username_check_timeout = window.setTimeout(() => {

                    //must not have any whitespace, must have "@" and ".", must have char before "@"
                    //do not make this too complicated, it is easier to just send email and see if user receives it
                    if(/\s+/g.test(new_value) === false) {

                        this.username_string = new_value;
                        this.checkUsernameExists();

                    }else if(/\s+/g.test(new_value) === true){

                        this.username_string = "";
                        this.username_is_ok = false;
                        this.username_validation_has_error = true;
                        this.username_validation_status_text = "Please remove all spaces.";

                    }else{

                        this.username_string = "";
                        this.username_is_ok = false;
                        this.username_validation_has_error = true;
                        this.username_validation_status_text = "Does not look like a proper username.";
                    }

                    //maximum 254 characters for email
                    //since email path has 256 limit and needs to add "<" and ">"
                    //https://stackoverflow.com/questions/386294/what-is-the-maximum-length-of-a-valid-email-address

                }, 400);
            },
            async checkUsernameExists() : Promise<void> {

                await axios.get(window.location.origin + "/api/users/username/check-exists/" + this.username_string)
                .then((response:any) => {

                    if(response.data['data']['exists'] === false){

                        this.username_is_ok = true;
                        this.username_validation_has_error = false;
                        this.username_validation_status_text = "This username is available.";

                    }else{

                        this.username_is_ok = false;
                        this.username_validation_has_error = true;
                        this.username_validation_status_text = "This username has already been taken. Try another.";
                    }
                })
                .catch((error: any) => {

                    this.username_is_ok = false;
                    this.username_validation_has_error = true;
                    this.username_validation_status_text = "We cannot check for usernames at this time. Try again later.";
                    console.log(error);
                });
            },
            async updateUsername() : Promise<void> {

                //no need to proceed if error on validating username
                if(this.username_is_ok === false){

                    return;
                }

                // let data = new FormData();
                // data.append("email", this.email_string);
                // data.append("is_requesting_new_otp", JSON.stringify(true));

                // await axios.post(window.location.origin + "/api/users/log-in", data)
                // .then((response:any) => {

                //     console.log(response.data['message']);

                // })
                // .catch((error: any) => {

                //     console.log(error);

                //     //unexpected error
                //     if(this.otp_request_cooldown_interval !== null){

                //         window.clearInterval(this.otp_request_cooldown_interval);
                //         this.otp_request_cooldown_interval = null;
                //     }
                    
                //     this.otp_request_status_text = "Oops, could not send code.";
                // });
            },
        }
    });
</script>