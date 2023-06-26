<template>
    <div class="text-theme-black">

        <!--title-->
        <VTitleXL class="py-8">
            <template #title>
                <TransitionFade>
                    <span
                        v-if="current_section === 'sign-in-section'"
                        class="block text-center"
                    >
                        Sign In
                    </span>
                    <span
                        v-else-if="current_section === 'create-account-section'"
                        class="block text-center"
                    >
                        Create Account
                    </span>
                </TransitionFade>
            </template>
        </VTitleXL>

        <TransitionFade>

            <!--sign in-->
            <div
                v-if="current_section === 'sign-in-section'"
                class="flex flex-col relative overflow-hidden h-[30rem]"
            >

                <TransitionGroupSlide
                    :prop-is-forward="transition_slide_is_forward"
                >
                    <!--step 0-->
                    <div
                        class="w-full flex flex-col p-2 pt-0"
                        v-show="current_step === 'sign-in-step-0'"
                    >

                        <!--choices-->
                        <div class="flex flex-col">

                            <p class="text-2xl block">
                                Select a sign-in option.
                            </p>

                            <div class="flex flex-col gap-4 mt-6">
                                <VActionButtonS
                                    @click.stop="overrideNavigation('sign-in-section', 'sign-in-step-1')"
                                    class="w-full px-4 gap-4"
                                >
                                    <i class="fas fa-hat-wizard text-2xl"></i>
                                    <span>Sign in with email</span>
                                </VActionButtonS>
                                <VActionButtonS
                                    @click.stop="overrideNavigation('sign-in-section', 'sign-in-step-1')"
                                    class="w-full px-4 gap-4"
                                >
                                    <i class="fas fa-hat-wizard text-2xl"></i>
                                    <span>Sign in with Google</span>
                                </VActionButtonS>
                            </div>
                        </div>

                        <!--extra options-->
                        <div class="mt-8 h-fit flex flex-col">
                            <VActionButtonTextOnly
                                @click.stop="overrideNavigation('create-account-section', 'create-account-step-0')"
                            >
                                <span class="mx-auto font-bold">Don't have an account?</span>
                            </VActionButtonTextOnly>
                        </div>
                    </div>

                    <!--step 1-->
                    <div
                        class="w-full flex flex-col p-2 pt-0"
                        v-show="current_step === 'sign-in-step-1'"
                    >

                        <div class="flex flex-col">
                            <p class="text-2xl block">
                                Start with an email address.
                            </p>
                        </div>

                        <VInput
                            propElementId="email-address"
                            propLabel="Email address"
                            propPlaceholder=""
                            :propMaxLength="254"
                            :propIsRequired="true"
                            :propHasStatusText="true"
                            :propStatusText="email_validation_status_text"
                            :propIsError="email_validation_has_error"
                            :propIsOk="can_submit_email === true"
                            :propAllowWhitespace="false"
                            @hasNewValue="validateEmail($event)"
                            class="mt-6"
                        />

                        <!--navigation-->
                        <div class="mt-8 w-full h-fit flex">
                            <VActionSpecialM
                                @click.stop="[overrideNavigation('sign-in-section', 'sign-in-step-2')]"
                                :propIsEnabled="canSubmitEmailAndRequestOTP"
                                propElement="button"
                                :propIsRound="true"
                                type="button"
                                class="ml-auto"
                            >
                                <i class="fas fa-arrow-right text-2xl block mx-auto"></i>
                                <span class="sr-only">continue</span>
                            </VActionSpecialM>
                        </div>

                        <!--extra options-->
                        <div class="h-fit flex flex-col mt-6">
                            <VActionButtonTextOnly
                                @click.stop="overrideNavigation('create-account-section', 'create-account-step-0', false)"
                                :prop-is-enabled="true"
                            >
                                <span class="font-bold">Create account</span>
                            </VActionButtonTextOnly>
                            <VActionButtonTextOnly
                                @click.stop="overrideNavigation('sign-in-section', 'sign-in-step-0', false)"
                                :prop-is-enabled="true"
                            >
                                <span class="font-bold">Sign in with another method</span>
                            </VActionButtonTextOnly>
                        </div>
                    </div>

                    <!--step 2-->
                    <div
                        class="w-full flex flex-col p-2 pt-0"
                        v-show="current_step === 'sign-in-step-2'"
                    >

                        <div class="flex flex-col">
                            <p class="text-2xl block">
                                Enter the sign-in code.
                            </p>
                            <span class="text-base block break-words">{{ email_string }}</span>
                        </div>

                        <VNumberSlots
                            @hasNewValue="validateOTP($event)"
                            prop-element-id="sign-in-otp"
                            prop-label-text="6-digit code"
                            :prop-extra-slots="calcExtraVNumberSlots"
                            class="mt-6"
                        />

                        <!--resend OTP-->
                        <VActionButtonTextOnly
                            :prop-is-enabled="canSubmitEmailAndRequestOTP"
                            class="mt-8"
                        >
                            <span class="font-bold">{{ otp_request_status_text }}</span>
                        </VActionButtonTextOnly>

                        <!--navigation-->
                        <div class="mt-8 h-fit">
                            <div class="flex flex-row items-center">
                                <div class="w-full">
                                    <VActionButtonTextOnly
                                        @click.stop="overrideNavigation('sign-in-section', 'sign-in-step-1', false)"
                                        class="flex-row"
                                    >
                                        <i class="fas fa-arrow-left w-fit h-fit text-2xl block my-auto pr-2"></i>
                                        <span class="block my-auto">Change email</span>
                                    </VActionButtonTextOnly>
                                </div>
                                <div>
                                    <VActionSpecialM
                                        :propIsEnabled="canSubmitOTP"
                                        @click.stop="submitOTP()"
                                        propElement="button"
                                        :propIsRound="true"
                                        type="button"
                                        class="ml-auto"
                                    >
                                        <i class="fas fa-arrow-right text-2xl block mx-auto"></i>
                                        <span class="sr-only">continue</span>
                                    </VActionSpecialM>
                                </div>
                            </div>
                        </div>

                        <!--extra options-->
                        <div class="h-fit flex flex-col mt-6">
                            <VActionButtonTextOnly
                                @click.stop="overrideNavigation('create-account-section', 'create-account-step-0', false)"
                                :prop-is-enabled="true"
                            >
                                <span class="font-bold">Create account</span>
                            </VActionButtonTextOnly>
                            <VActionButtonTextOnly
                                @click.stop="overrideNavigation('sign-in-section', 'sign-in-step-0', false)"
                                :prop-is-enabled="true"
                            >
                                <span class="font-bold">Sign in with another method</span>
                            </VActionButtonTextOnly>
                        </div>
                    </div>
                </TransitionGroupSlide>
            </div>

            <!--create account-->
            <div
                v-else-if="current_section === 'create-account-section'"
                class="flex flex-col relative overflow-hidden h-[30rem]"
            >

                <TransitionGroupSlide
                    :prop-is-forward="true"
                >
                    <!--step 0-->
                    <div
                        class="w-full flex flex-col p-2 pt-0"
                        v-show="current_step === 'create-account-step-0'"
                    >

                        <p class="text-2xl block mx-auto">
                            Choose a method.
                        </p>

                        <!--choices-->

                        <!--extra options-->
                        <div class="mt-8 h-fit flex flex-col">
                            <VActionButtonTextOnly
                                @click.stop="overrideNavigation('sign-in-section', 'sign-in-step-0')"
                                :prop-is-enabled="true"
                                class="w-fit mx-auto"
                            >
                                <span class="font-bold">Sign in</span>
                            </VActionButtonTextOnly>
                        </div>
                    </div>

                    <!--step 1-->
                    <div
                        class="w-full flex flex-col p-2 pt-0"
                        v-show="current_step === 'create-account-step-1'"
                    >

                        <VInput
                            propElementId="email-address"
                            propLabel="Email address"
                            propPlaceholder=""
                            :propMaxLength="254"
                            :propIsRequired="true"
                            :propHasStatusText="true"
                            :propStatusText="email_validation_status_text"
                            :propIsError="can_submit_email === false"
                            :propIsOk="can_submit_email === true"
                            @hasNewValue="validateEmail($event)"
                        />

                        <!--navigation-->
                        <div class="mt-8 w-full h-fit flex">
                            <VActionSpecialM
                                :propIsEnabled="true"
                                propElement="button"
                                :propIsRound="true"
                                type="button"
                                class="flex items-center ml-auto"
                            >
                                <i class="fas fa-arrow-right text-2xl block mx-auto"></i>
                                <span class="sr-only">continue</span>
                            </VActionSpecialM>
                        </div>

                        <!--extra options-->
                        <div class="mt-2 h-fit flex flex-col">
                            <VActionButtonTextOnly
                                @click.stop="overrideNavigation('sign-in-section', 'sign-in-step-0')"
                                :prop-is-enabled="true"
                            >
                                <span class="font-bold">Sign in</span>
                            </VActionButtonTextOnly>
                        </div>
                    </div>

                    <!--step 2-->
                    <div
                        class="w-full flex flex-col p-2 pt-0"
                        v-show="current_step === 'create-account-step-2'"
                    >

                        <div class="flex flex-col">
                            <p class="text-2xl block">
                                Verification code sent!
                            </p>
                            <span class="text-base font-light block break-words">adrianchangcy@gmail.com</span>
                        </div>

                        <VNumberSlots
                            prop-element-id="create-account-otp"
                            prop-label-text="6-digit code"
                            :prop-extra-slots="calcExtraVNumberSlots"
                            class="mt-6"
                        />
                        <VActionButtonTextOnly
                            :prop-is-enabled="true"
                            class="mt-4"
                        >
                            <span class="font-bold">Can resend in 30s</span>
                        </VActionButtonTextOnly>

                        <!--navigation-->
                        <div class="mt-8 h-fit">
                            <div class="flex flex-row items-center">
                                <div class="w-full">
                                    <VActionButtonTextOnly
                                        @click.stop="overrideNavigation('create-account-section', 'sign-in-step-1')"
                                        :prop-is-enabled="true"
                                        class="flex-row"
                                    >
                                        <i class="fas fa-arrow-left text-2xl block my-auto pr-2"></i>
                                        <span class="block my-auto">Change email</span>
                                    </VActionButtonTextOnly>
                                </div>
                                <div class="w-full">
                                    <VActionSpecialM
                                        :propIsEnabled="true"
                                        propElement="button"
                                        :propIsRound="true"
                                        type="button"
                                        class="ml-auto"
                                    >
                                        <i class="fas fa-arrow-right block mx-auto"></i>
                                        <span class="sr-only">continue</span>
                                    </VActionSpecialM>
                                </div>
                            </div>
                        </div>

                        <!--extra options-->
                        <div class="mt-2 h-fit flex flex-col">
                            <VActionButtonTextOnly
                                @click.stop="overrideNavigation('sign-in-section', 'sign-in-step-0')"
                                :prop-is-enabled="true"
                            >
                                <span class="font-bold">Sign in</span>
                            </VActionButtonTextOnly>
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
    // import VActionButtonSpecialL from '@/components/small/VActionButtonSpecialL.vue';
    import VActionButtonTextOnly from '@/components/small/VActionButtonTextOnly.vue';
    import TransitionGroupSlide from '@/transitions/TransitionGroupSlide.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VActionButtonS from '@/components/small/VActionButtonS.vue';
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
                can_submit_email: false,
                email_validation_has_error: false,
                email_validation_status_text: "",

                otp: "",
                otp_length: 6,

                otp_status_text: "",
                otp_request_cooldown_interval: null as number|null,
                otp_request_cooldown_duration_s: 30,
                otp_request_cooldown_s: 0,
                otp_request_status_text: "",

                current_section: "",
                sections: ["sign-in-section", "create-account-section"] as string[],

                current_step: "",
                steps: {
                    0: ["sign-in-step-0", "sign-in-step-1", "sign-in-step-2"],
                    1: ["create-account-step-0", "create-account-step-0", "create-account-step-2"],
                } as StepsType,
                transition_slide_is_forward: true,
            };
        },
        watch: {
            current_section(){

                //when new section, always reset current section's data
                this.resetEmailRelatedValues();
            },
        },
        computed: {
            calcExtraVNumberSlots() : number {

                return this.otp_length - 1;
            },
            canSubmitOTP() : boolean {

                //VNumberSlots only returns full string when successful and valid
                return this.otp !== "" && this.otp.length === this.otp_length;
            },
            canSubmitEmailAndRequestOTP() : boolean {

                return this.can_submit_email &&
                    this.otp_request_cooldown_interval === null &&
                    this.otp_request_cooldown_s === 0;
            },
        },
        methods: {
            resetEmailRelatedValues() : void {

                this.email_string = "";
                this.email_check_timeout !== null ? window.clearTimeout(this.email_check_timeout) : null;
                this.can_submit_email = false;
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
            async submitOTP() : Promise<void> {

                if(this.canSubmitOTP === false){

                    return;
                }

                let data = new FormData();
                data.append("email", this.email_string);
                data.append("otp", this.otp);

                await axios.post(window.location.origin + "/api/users/create", data)
                .then((response:any) => {

                    console.log(response.data['message']);

                })
                .catch((error: any) => {

                    console.log(error.response.data['message']);
                });
            },
            async submitEmailAndRequestOTP() : Promise<void> {

                if(this.canSubmitEmailAndRequestOTP === false){

                    return;
                }

                let data = new FormData();
                data.append("email", this.email_string);
                data.append("is_requesting_new_otp", JSON.stringify(true));

                await axios.post(window.location.origin + "/api/users/create", data)
                .then((response:any) => {

                    console.log(response.data['message']);

                })
                .catch((error: any) => {

                    console.log(error.response.data['message']);
                });

                //set cooldown
                this.otp_request_cooldown_s = this.otp_request_cooldown_duration_s;

                this.otp_request_cooldown_interval = window.setInterval(()=>{

                    if(this.otp_request_cooldown_s === 0 && this.otp_request_cooldown_interval !== null){

                        window.clearInterval(this.otp_request_cooldown_interval);
                        this.otp_request_cooldown_interval = null;
                        this.otp_request_status_text = "Resend code?";
                        return;
                    }

                    this.otp_request_status_text = "Can resend in " + this.otp_request_cooldown_s.toString() + "s";
                    this.otp_request_cooldown_s -= 1;

                }, 1000);
            },
            validateOTP(new_value:string) : void {

                this.otp = new_value;
            },
            validateEmail(new_value:string) : void {

                this.resetEmailRelatedValues();
                
                //do nothing if there is no text
                if(new_value.length === 0){

                    return;
                }

                //has text
                this.email_check_timeout = window.setTimeout(() => {

                    //must not have any whitespace, must have "@" and ".", must have char before "@"
                    //do not make this too complicated, it is easier to just send email and see if user receives it
                    if(/^\S+@\S+\.\S+$/.test(new_value) === true) {

                        this.email_string = new_value;
                        this.can_submit_email = true;
                        this.email_validation_has_error = false;
                        this.email_validation_status_text = "All good!";

                    }else if(/\s+/g.test(new_value) === true){

                        this.email_string = "";
                        this.can_submit_email = false;
                        this.email_validation_has_error = true;
                        this.email_validation_status_text = "Spaces detected. Please remove them.";

                    }else{

                        this.email_string = "";
                        this.can_submit_email = false;
                        this.email_validation_has_error = true;
                        this.email_validation_status_text = "That does not look like a proper email.";
                    }

                    //maximum 254 characters for email
                    //since email path has 256 limit and needs to add "<" and ">"
                    //https://stackoverflow.com/questions/386294/what-is-the-maximum-length-of-a-valid-email-address

                }, 400);
            },
        },
        beforeMount(){

            this.current_section = this.sections[0];
            this.current_step = this.steps[0][0];
        },
    });
</script>