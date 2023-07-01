<template>
    <div class="text-theme-black">
        <VSetUsername/>
        <!--title-->
        <VTitleXL class="pt-8 pb-6">
            <template #title>
                <span class="block text-center">Voicewake</span>
            </template>
            <template #titleDescription>
                <TransitionFade>
                    <span
                        v-if="current_section === 'log-in-section'"
                        class="block text-center"
                    >
                        Log in
                    </span>
                    <span
                        v-else-if="current_section === 'sign-up-section'"
                        class="block text-center"
                    >
                        Sign up
                    </span>
                </TransitionFade>
            </template>
        </VTitleXL>

        <TransitionFade>

            <!--log in-->
            <div
                v-if="current_section === 'log-in-section'"
                class="flex flex-col relative overflow-hidden min-h-[32rem]"
            >

                <TransitionGroupSlide
                    :prop-is-forward="transition_slide_is_forward"
                >
                    <!--step 0-->
                    <div
                        class="w-full flex flex-col p-2"
                        v-show="current_step === 'log-in-step-0'"
                    >

                        <!--choices-->
                        <div class="flex flex-col">

                            <div class="flex flex-col gap-4 mt-6">
                                <VActionButtonS
                                    @click.stop="overrideNavigation('log-in-section', 'log-in-step-1')"
                                    class="w-full px-4 gap-4"
                                >
                                    <i class="fas fa-hat-wizard text-2xl"></i>
                                    <span>Log in with email</span>
                                </VActionButtonS>
                            </div>
                        </div>

                        <!--extra options-->
                        <div class="h-fit flex flex-col mt-2 gap-2">
                            <div class="mx-auto flex flex-row items-center">
                                <span class="text-base block">Don't have an account?&nbsp;</span>
                                <VActionButtonTextOnly
                                    @click.stop="overrideNavigation('sign-up-section', 'sign-up-step-0', false)"
                                    :prop-is-enabled="true"
                                >
                                    <span class="font-bold">Sign up</span>
                                </VActionButtonTextOnly>
                            </div>
                        </div>
                    </div>

                    <!--step 1-->
                    <div
                        class="w-full flex flex-col p-2"
                        v-show="current_step === 'log-in-step-1'"
                    >

                        <p class="text-xl font-medium block">
                            Log in and rejoin the fun.
                        </p>

                        <VInput
                            propElementId="email-address"
                            propLabel="Email address"
                            propPlaceholder=""
                            propType="text"
                            propInputmode="email"
                            propName="email"
                            propAutocomplete="on"
                            :propMaxLength="254"
                            :propIsRequired="true"
                            :propHasStatusText="true"
                            :propStatusText="email_validation_status_text"
                            :propIsError="email_validation_has_error"
                            :propIsOk="email_is_ok === true"
                            :propAllowWhitespace="false"
                            @hasNewValue="validateEmail($event)"
                            class="mt-6"
                        />

                        <!--main action-->
                        <div class="mt-8 w-full h-fit">
                            <VActionSpecialM
                                @click.stop="[
                                    overrideNavigation('log-in-section', 'log-in-step-2'),
                                    submitEmailAndRequestOTPForLogIn()
                                ]"
                                :propIsEnabled="email_is_ok"
                                propElement="button"
                                type="button"
                                class="w-full"
                            >
                                <span class="mx-auto">Continue</span>
                            </VActionSpecialM>
                        </div>

                        <!--extra options-->
                        <div class="h-fit flex flex-col mt-2">
                            <div class="mx-auto flex flex-row items-center">
                                <span class="text-base block">Don't have an account?&nbsp;</span>
                                <VActionButtonTextOnly
                                    @click.stop="overrideNavigation('sign-up-section', 'sign-up-step-1', false)"
                                    :prop-is-enabled="true"
                                >
                                    <span class="font-bold">Sign up</span>
                                </VActionButtonTextOnly>
                            </div>
                        </div>
                    </div>

                    <!--step 2-->
                    <div
                        class="w-full flex flex-col p-2"
                        v-show="current_step === 'log-in-step-2'"
                    >

                        <VActionButtonTextOnly
                            @click.stop="[overrideNavigation('log-in-section', 'log-in-step-1', false)]"
                            class="flex-row"
                        >
                            <i class="fas fa-arrow-left w-fit h-fit text-2xl block pr-2"></i>
                            <span class="font-bold break-words">Back to email</span>
                        </VActionButtonTextOnly>

                        <p class="text-xl font-medium block">
                            Enter the login code.
                        </p>
                        <p class="text-base block">
                            <span class="break-words">{{ email_string }}</span> 
                        </p>

                        <VNumberSlots
                            @hasNewValue="validateOTP($event)"
                            prop-element-id="log-in-otp"
                            prop-label-text="Login code"
                            :prop-extra-slots="calcExtraVNumberSlots"
                            :prop-trigger-reset="email_has_change"
                            class="mt-6"
                        />

                        <!--resend OTP-->
                        <div class="h-10 flex flex-row items-center">
                            <span class="text-base">{{ otp_request_status_text }}&nbsp;</span>
                            <VActionButtonTextOnly
                                v-show="canSubmitEmailAndRequestOTP"
                                @click.stop="submitEmailAndRequestOTPForLogIn(true)"
                            >
                                <span class="font-bold">Resend</span>
                            </VActionButtonTextOnly>
                        </div>

                        <!--main action-->
                        <div class="mt-8 h-fit">
                            <VActionSpecialM
                                :propIsEnabled="canSubmitOTP"
                                @click.stop="submitOTPForLogIn()"
                                propElement="button"
                                type="button"
                                class="w-full"
                            >
                                <span class="mx-auto">Log in</span>
                            </VActionSpecialM>
                        </div>

                        <!--extra options-->
                        <div class="h-fit flex flex-col mt-2 gap-2">
                            <div class="mx-auto flex flex-row items-center">
                                <span class="text-base block">Don't have an account?&nbsp;</span>
                                <VActionButtonTextOnly
                                    @click.stop="overrideNavigation('sign-up-section', 'sign-up-step-1', false)"
                                    :prop-is-enabled="true"
                                >
                                    <span class="font-bold">Sign up</span>
                                </VActionButtonTextOnly>
                            </div>
                        </div>
                    </div>
                </TransitionGroupSlide>
            </div>

            <!--signup-->
            <div
                v-else-if="current_section === 'sign-up-section'"
                class="flex flex-col relative overflow-hidden min-h-[32rem]"
            >

                <TransitionGroupSlide
                    :prop-is-forward="transition_slide_is_forward"
                >
                    <!--step 0-->
                    <div
                        class="w-full flex flex-col p-2"
                        v-show="current_step === 'sign-up-step-0'"
                    >

                        <!--choices-->
                        <div class="flex flex-col">

                            <div class="flex flex-col gap-4 mt-6">
                                <VActionButtonS
                                    @click.stop="overrideNavigation('sign-up-section', 'sign-up-step-1')"
                                    class="w-full px-4 gap-4"
                                >
                                    <i class="fas fa-hat-wizard text-2xl"></i>
                                    <span>Sign in with email</span>
                                </VActionButtonS>
                            </div>
                        </div>

                        <!--extra options-->
                        <div class="h-fit flex flex-col mt-2 gap-2">
                            <div class="mx-auto flex flex-row items-center">
                                <span class="text-base block">Already have an account?&nbsp;</span>
                                <VActionButtonTextOnly
                                    @click.stop="overrideNavigation('log-in-section', 'log-in-step-0', false)"
                                    :prop-is-enabled="true"
                                >
                                    <span class="font-bold">Log in</span>
                                </VActionButtonTextOnly>
                            </div>
                        </div>
                    </div>

                    <!--step 1-->
                    <div
                        class="w-full flex flex-col p-2"
                        v-show="current_step === 'sign-up-step-1'"
                    >

                        <p class="text-xl font-medium block">
                            Sign up to chat with others.
                        </p>

                        <VInput
                            propElementId="email-address"
                            propLabel="Email address"
                            propPlaceholder=""
                            propType="text"
                            propInputmode="email"
                            propName="email"
                            propAutocomplete="on"
                            :propMaxLength="254"
                            :propIsRequired="true"
                            :propHasStatusText="true"
                            :propStatusText="email_validation_status_text"
                            :propIsError="email_validation_has_error"
                            :propIsOk="email_is_ok === true"
                            :propAllowWhitespace="false"
                            @hasNewValue="validateEmail($event)"
                            class="mt-6"
                        />

                        <!--main action-->
                        <div class="mt-8 w-full h-fit">
                            <VActionSpecialM
                                @click.stop="[
                                    overrideNavigation('sign-up-section', 'sign-up-step-2'),
                                    submitEmailAndRequestOTPForSignUp()
                                ]"
                                :propIsEnabled="email_is_ok"
                                propElement="button"
                                type="button"
                                class="w-full"
                            >
                                <span class="mx-auto">Continue</span>
                            </VActionSpecialM>
                        </div>

                        <!--extra options-->
                        <div class="h-fit flex flex-col mt-2">
                            <div class="mx-auto flex flex-row items-center">
                                <span class="text-base block">Already have an account?&nbsp;</span>
                                <VActionButtonTextOnly
                                    @click.stop="overrideNavigation('log-in-section', 'log-in-step-1', false)"
                                    :prop-is-enabled="true"
                                >
                                    <span class="font-bold">Log in</span>
                                </VActionButtonTextOnly>
                            </div>
                        </div>
                    </div>

                    <!--step 2-->
                    <div
                        class="w-full flex flex-col p-2"
                        v-show="current_step === 'sign-up-step-2'"
                    >

                        <VActionButtonTextOnly
                            @click.stop="[overrideNavigation('sign-up-section', 'sign-up-step-1', false)]"
                            class="flex-row"
                        >
                            <i class="fas fa-arrow-left w-fit h-fit text-2xl block pr-2"></i>
                            <span class="font-bold break-words">Back to email</span>
                        </VActionButtonTextOnly>

                        <p class="text-xl font-medium block">
                            Enter the sign-up code.
                        </p>
                        <p class="text-base block">
                            <span class="break-words">{{ email_string }}</span>
                        </p>

                        <VNumberSlots
                            @hasNewValue="validateOTP($event)"
                            prop-element-id="sign-up-otp"
                            prop-label-text="Sign-up code"
                            :prop-extra-slots="calcExtraVNumberSlots"
                            :prop-trigger-reset="email_has_change"
                            class="mt-6"
                        />

                        <!--resend OTP-->
                        <div class="h-10 flex flex-row items-center">
                            <span class="text-base">{{ otp_request_status_text }}&nbsp;</span>
                            <VActionButtonTextOnly
                                v-show="canSubmitEmailAndRequestOTP"
                                @click.stop="submitEmailAndRequestOTPForSignUp(true)"
                            >
                                <span class="font-bold">Resend</span>
                            </VActionButtonTextOnly>
                        </div>

                        <!--main action-->
                        <div class="mt-8 h-fit">
                            <VActionSpecialM
                                :propIsEnabled="canSubmitOTP"
                                @click.stop="submitOTPForSignUp()"
                                propElement="button"
                                type="button"
                                class="w-full"
                            >
                                <span class="mx-auto">Sign up</span>
                            </VActionSpecialM>
                        </div>

                        <!--extra options-->
                        <div class="h-fit flex flex-col mt-2">
                            <div class="mx-auto flex flex-row items-center">
                                <span class="text-base block">Already have an account?&nbsp;</span>
                                <VActionButtonTextOnly
                                    @click.stop="overrideNavigation('log-in-section', 'log-in-step-1', false)"
                                    :prop-is-enabled="true"
                                >
                                    <span class="font-bold">Log in</span>
                                </VActionButtonTextOnly>
                            </div>
                        </div>
                    </div>
                </TransitionGroupSlide>
            </div>
        </TransitionFade>
    </div>

</template>

<style scoped>
</style>


<script setup lang="ts">
    import VInput from '@/components/small/VInput.vue';
    import VTitleXL from '@/components/small/VTitleXL.vue';
    import VNumberSlots from '@/components/small/VNumberSlots.vue';
    import VActionSpecialM from '@/components/small/VActionSpecialM.vue';
    import VActionButtonTextOnly from '@/components/small/VActionButtonTextOnly.vue';
    import TransitionGroupSlide from '@/transitions/TransitionGroupSlide.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VActionButtonS from '@/components/small/VActionButtonS.vue';
    import VSetUsername from '@/components/medium/VSetUsername.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    const axios = require('axios');

    interface StepsType {
        [key: number]: string[],
    }

    export default defineComponent({
        name: "UserOptionsApp",
        data() {
            return {
                email_string: "",
                email_check_timeout: null as number|null,
                email_is_ok: false,
                email_validation_has_error: false,
                email_validation_status_text: "",

                otp: "",
                otp_length: 6,

                otp_request_cooldown_interval: null as number|null,
                otp_request_cooldown_duration_s: 30,
                otp_request_cooldown_s: 0,
                otp_request_status_text: "",
                otp_request_is_first_time: true,
                email_has_change: false,    //used to determine whether otp resets

                is_loading: false,

                current_section: "",
                sections: ["log-in-section", "sign-up-section"] as string[],

                current_step: "",
                steps: {
                    0: ["log-in-step-0", "log-in-step-1", "log-in-step-2"],
                    1: ["sign-up-step-0", "sign-up-step-1", "sign-up-step-2"],
                } as StepsType,
                transition_slide_is_forward: true,
            };
        },
        watch: {
            current_section(){

                //when new section, always reset current section's data
                this.resetEmailRelatedValues();
                this.resetOTPRelatedValues();
            },
        },
        computed: {
            calcExtraVNumberSlots() : number {

                return this.otp_length - 1;
            },
            canSubmitOTP() : boolean {

                //VNumberSlots only returns full string when successful and valid
                return this.otp !== "" && this.otp.length === this.otp_length && this.is_loading === false;
            },
            canSubmitEmailAndRequestOTP() : boolean {

                return this.email_is_ok === true && this.otp_request_cooldown_interval === null && this.is_loading === false;
            }
        },
        methods: {
            resetOTPRelatedValues() : void {

                this.otp_request_cooldown_interval !== null ? window.clearTimeout(this.otp_request_cooldown_interval) : null;
                this.otp_request_cooldown_interval = null;
                this.otp_request_cooldown_duration_s = 30;
                this.otp_request_cooldown_s = 0;
                this.otp_request_status_text = "";
                this.email_has_change = false;
            },
            resetEmailRelatedValues() : void {

                this.email_string = "";
                this.email_check_timeout !== null ? window.clearTimeout(this.email_check_timeout) : null;
                this.email_is_ok = false;
                this.email_validation_has_error = false;
                this.email_validation_status_text = "";
            },
            overrideNavigation(section:string="", step:string="", transition_slide_is_forward=true) : void {

                this.transition_slide_is_forward = transition_slide_is_forward;

                let section_index = this.sections.indexOf(section);

                if(section_index !== -1){

                    //if value is the same, it won't trigger watcher, so no need to worry
                    this.current_section = this.sections[section_index];
                }

                let steps_value_index = (this.steps as StepsType)[section_index].indexOf(step);

                if (steps_value_index !== -1){

                    this.current_step = (this.steps as StepsType)[section_index][steps_value_index];
                }
            },
            async submitOTPForLogIn() : Promise<void> {

                if(this.canSubmitOTP === false){

                    return;
                }

                this.is_loading = true;

                let data = new FormData();
                data.append("email", this.email_string);
                data.append("otp", this.otp);

                await axios.post(window.location.origin + "/api/users/log-in", data)
                .then((response:any) => {

                    console.log(response.data['message']);
                    this.is_loading = false;

                    window.location.href = window.location.origin;

                })
                .catch((error: any) => {

                    console.log(error);
                    this.is_loading = false;
                });
            },
            async submitOTPForSignUp() : Promise<void> {

                if(this.canSubmitOTP === false){

                    return;
                }

                this.is_loading = true;

                let data = new FormData();
                data.append("email", this.email_string);
                data.append("otp", this.otp);

                await axios.post(window.location.origin + "/api/users/sign-up", data)
                .then((response:any) => {

                    console.log(response.data['message']);
                    this.is_loading = false;

                    window.location.href = window.location.origin;

                })
                .catch((error: any) => {

                    console.log(error);
                    this.is_loading = false;
                });
            },
            async submitEmailAndRequestOTPForLogIn(is_resubmit=false) : Promise<void> {

                //no need to proceed if error on validating email
                //no need to proceed if email from step 1 to 2 has no change
                if(this.email_is_ok === false || (this.email_has_change === false && is_resubmit === false)){

                    return;
                }

                //reset step 2 if validateEmail() detects email change
                this.resetOTPRelatedValues();

                //set cooldown
                this.otp_request_cooldown_s = this.otp_request_cooldown_duration_s;

                this.otp_request_cooldown_interval = window.setInterval(()=>{

                    if(this.otp_request_cooldown_s === 0 && this.otp_request_cooldown_interval !== null){

                        window.clearInterval(this.otp_request_cooldown_interval);
                        this.otp_request_cooldown_interval = null;
                        this.otp_request_status_text = "Didn't receive code?";
                        return;
                    }

                    if(this.otp_request_cooldown_s === 1){
                        this.otp_request_status_text = "Code should arrive in " +
                            this.otp_request_cooldown_s.toString() +
                            " second...";
                    }else{
                        this.otp_request_status_text = "Code should arrive in " +
                            this.otp_request_cooldown_s.toString() +
                            " seconds...";
                    }

                    this.otp_request_cooldown_s -= 1;

                }, 1000);

                this.is_loading = true;

                let data = new FormData();
                data.append("email", this.email_string);
                data.append("is_requesting_new_otp", JSON.stringify(true));

                await axios.post(window.location.origin + "/api/users/log-in", data)
                .then((response:any) => {

                    console.log(response.data['message']);
                    this.is_loading = false;

                })
                .catch((error: any) => {

                    console.log(error);

                    //unexpected error
                    if(this.otp_request_cooldown_interval !== null){

                        window.clearInterval(this.otp_request_cooldown_interval);
                        this.otp_request_cooldown_interval = null;
                    }
                    
                    this.otp_request_status_text = "Oops! Could not send code.";

                    this.is_loading = false;
                });
            },
            async submitEmailAndRequestOTPForSignUp(is_resubmit=false) : Promise<void> {

                //no need to proceed if error on validating email
                //no need to proceed if email from step 1 to 2 has no change
                if(this.email_is_ok === false || (this.email_has_change === false && is_resubmit === false)){

                    return;
                }

                //reset step 2 if validateEmail() detects email change
                this.resetOTPRelatedValues();

                //set cooldown
                this.otp_request_cooldown_s = this.otp_request_cooldown_duration_s;

                this.otp_request_cooldown_interval = window.setInterval(()=>{

                    if(this.otp_request_cooldown_s === 0 && this.otp_request_cooldown_interval !== null){

                        window.clearInterval(this.otp_request_cooldown_interval);
                        this.otp_request_cooldown_interval = null;
                        this.otp_request_status_text = "Didn't receive code?";
                        return;
                    }

                    if(this.otp_request_cooldown_s === 1){
                        this.otp_request_status_text = "Code should arrive in " +
                            this.otp_request_cooldown_s.toString() +
                            " second...";
                    }else{
                        this.otp_request_status_text = "Code should arrive in " +
                            this.otp_request_cooldown_s.toString() +
                            " seconds...";
                    }

                    this.otp_request_cooldown_s -= 1;

                }, 1000);

                this.is_loading = true;

                let data = new FormData();
                data.append("email", this.email_string);
                data.append("is_requesting_new_otp", JSON.stringify(true));

                await axios.post(window.location.origin + "/api/users/sign-up", data)
                .then((response:any) => {

                    console.log(response.data['message']);
                    this.is_loading = false;

                })
                .catch((error: any) => {

                    console.log(error);

                    //unexpected error
                    if(this.otp_request_cooldown_interval !== null){

                        window.clearInterval(this.otp_request_cooldown_interval);
                        this.otp_request_cooldown_interval = null;
                    }
                    
                    this.otp_request_status_text = "Oops! Could not send code.";

                    this.is_loading = false;
                });
            },
            validateOTP(new_value:string) : void {

                //no need validation here, since we either only get "" or full OTP
                //we use computed function do validate it for us
                this.otp = new_value;
            },
            validateEmail(new_value:string) : void {

                //reset everything on any change
                this.resetEmailRelatedValues();

                this.email_has_change = true;
                
                //do nothing if there is no text
                if(new_value.length === 0){

                    return;
                }

                //has text
                this.email_check_timeout = window.setTimeout(() => {

                    //must not have any whitespace, must have "@" and ".", must have char before "@"
                    //do not make this too complicated, it is easier to just send email and see if user receives it
                    if(/^\S+@\S+\.\S+$/.test(new_value) === true){

                        this.email_string = new_value;
                        this.email_is_ok = true;
                        this.email_validation_has_error = false;
                        this.email_validation_status_text = "All good!";

                    }else if(/\s+/g.test(new_value) === true){

                        this.email_string = "";
                        this.email_is_ok = false;
                        this.email_validation_has_error = true;
                        this.email_validation_status_text = "Please remove all spaces.";

                    }else{

                        this.email_string = "";
                        this.email_is_ok = false;
                        this.email_validation_has_error = true;
                        this.email_validation_status_text = "Does not look like a proper email.";
                    }

                    //maximum 254 characters for email
                    //since email path has 256 limit and needs to add "<" and ">"
                    //https://stackoverflow.com/questions/386294/what-is-the-maximum-length-of-a-valid-email-address

                }, 400);
            },
        },
        beforeMount(){

            this.current_section = this.sections[0];
            this.current_step = this.steps[0][1];
        },

    });
</script>