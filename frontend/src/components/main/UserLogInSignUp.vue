<template>
    <div
        class="text-theme-black"
    >

        <!--close button-->
        <div
            v-if="propIsForStaticPage === false"
            class="h-10 relative"
        >
            <VActionTextOnly
                :propIsIconOnly="true"
                @click.stop="emitIsClosed()"
                propElement="button"
                propElementSize="s"
                type="button"
                class="w-10 absolute top-1 -right-3 m-auto"
            >
                <i class="fas fa-xmark mx-auto text-xl"></i>
            </VActionTextOnly>
        </div>

        <!--title-->
        <VTitle
            v-if="propIsForStaticPage === false"
            propFontSize="l"
            class="pb-6"
        >
            <template #title>
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
        </VTitle>

        <!--adjust height until it covers nicely the largest step-->
        <!--so that when transitioning from largest to smaller, largest's content doesn't get cut off (it will if h-fit)-->
        <div class="h-[26.5rem]">

            <TransitionFade>

                <!--log in-->
                <div
                    v-if="current_section === 'log-in-section'"
                    class="h-full flex flex-col relative overflow-hidden"
                >

                    <TransitionGroupSlide
                        :prop-is-forward="transition_slide_is_forward"
                    >
                        <!--step 0-->
                        <div
                            class="w-full h-full flex flex-col p-2"
                            v-show="current_step === 'log-in-step-0'"
                        >

                            <!--choices-->
                            <div class="flex flex-col">

                                <div class="flex flex-col gap-4 mt-6">
                                    <VAction
                                        @click.stop="doNavigation('log-in-section', 'log-in-step-1')"
                                        propElement="button"
                                        type="button"
                                        propElementSize="s"
                                        propFontSize="s"
                                        class="w-full px-4 gap-4"
                                    >
                                        <i class="fas fa-hat-wizard text-2xl"></i>
                                        <span>Log in with email</span>
                                    </VAction>
                                </div>
                            </div>

                            <!--extra options-->
                            <div class="h-fit flex flex-col mt-2 gap-2">
                                <div class="mx-auto flex flex-row items-center">
                                    <span class="text-base block">Don't have an account?&nbsp;</span>
                                    <div v-if="propIsForStaticPage === true">
                                        <VActionTextOnly
                                            :propIsIconOnly="true"
                                            propElement="a"
                                            propElementSize="s"
                                            propFontSize="s"
                                            href="/signup"
                                        >
                                            <span class="font-bold">Sign up</span>
                                        </VActionTextOnly>
                                    </div>
                                    <div v-else>
                                        <VActionTextOnly
                                            :propIsIconOnly="true"
                                            @click.stop="doNavigation('sign-up-section', 'sign-up-step-0', false)"
                                            propElement="button"
                                            propElementSize="s"
                                            propFontSize="s"
                                            type="button"
                                        >
                                            <span class="font-bold">Sign up</span>
                                        </VActionTextOnly>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!--step 1-->
                        <div
                            class="w-full h-full flex flex-col p-2"
                            v-show="current_step === 'log-in-step-1'"
                        >

                            <p class="text-xl font-medium block">
                                Log in and rejoin the fun!
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
                                @hasNewValue="handleNewEmail($event)"
                                class="mt-6"
                            />

                            <!--main action-->
                            <div class="mt-8 w-full h-fit">
                                <VActionSpecial
                                    @click.stop="submitStep1('log-in')"
                                    :propIsEnabled="!is_email_loading"
                                    propElement="button"
                                    type="button"
                                    propElementSize="m"
                                    propFontSize="m"
                                    class="w-full"
                                >
                                    <span class="mx-auto">Next</span>
                                </VActionSpecial>
                            </div>

                            <!--extra options-->
                            <div class="h-fit flex flex-col mt-2">
                                <div class="mx-auto flex flex-row items-center">
                                    <span class="text-base block">Don't have an account?&nbsp;</span>
                                    <div v-if="propIsForStaticPage === true">
                                        <VActionTextOnly
                                            :propIsIconOnly="true"
                                            propElement="a"
                                            propElementSize="s"
                                            propFontSize="s"
                                            href="/signup"
                                        >
                                            <span class="font-bold">Sign up</span>
                                        </VActionTextOnly>
                                    </div>
                                    <div v-else>
                                        <VActionTextOnly
                                            :propIsIconOnly="true"
                                            @click.stop="doNavigation('sign-up-section', 'sign-up-step-1', false)"
                                            propElement="button"
                                            propElementSize="s"
                                            propFontSize="s"
                                            type="button"
                                        >
                                            <span class="font-bold">Sign up</span>
                                        </VActionTextOnly>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!--step 2-->
                        <div
                            class="w-full h-full flex flex-col p-2"
                            v-show="current_step === 'log-in-step-2'"
                        >

                            <VActionTextOnly
                                :propIsIconOnly="true"
                                @click.stop="[doNavigation('log-in-section', 'log-in-step-1', false)]"
                                propElement="button"
                                propElementSize="s"
                                propFontSize="s"
                                type="button"
                                class="w-fit"
                            >
                                <div class="flex items-center">
                                    <i class="fas fa-arrow-left w-fit h-fit text-2xl block pr-2"></i>
                                    <span class="font-bold break-words">Back to email</span>
                                </div>
                            </VActionTextOnly>

                            <p class="text-xl font-medium block">
                                Enter the login code.
                            </p>
                            <p class="text-base block">
                                <span class="break-words">{{ email_string }}</span> 
                            </p>

                            <VNumberSlots
                                @hasNewValue="handleNewOTP($event)"
                                prop-element-id="log-in-otp"
                                prop-label-text="Login code"
                                :prop-extra-slots="calcExtraVNumberSlots"
                                :prop-trigger-reset="email_has_change"
                                :prop-is-error="otp_validation_has_error"
                                :prop-status-text="otp_validation_status_text"
                                class="mt-6"
                            />

                            <!--resend OTP-->
                            <div class="h-10 flex flex-row items-center">
                                <span class="text-base">{{ otp_request_status_text }}&nbsp;</span>
                                <VActionTextOnly
                                    :propIsIconOnly="true"
                                    v-show="canSubmitEmailAndRequestOTP"
                                    @click.stop="submitEmailAndRequestOTP('log-in', true)"
                                    propElement="button"
                                    propElementSize="s"
                                    propFontSize="s"
                                    type="button"
                                >
                                    <span class="font-bold">Resend</span>
                                </VActionTextOnly>
                            </div>

                            <!--main action-->
                            <div class="mt-8 h-fit">
                                <VActionSpecial
                                    @click.stop="submitStep2('log-in')"
                                    :propIsEnabled="!is_main_action_loading"
                                    propElement="button"
                                    type="button"
                                    propElementSize="m"
                                    propFontSize="m"
                                    class="w-full"
                                >
                                    <span class="mx-auto">Log in</span>
                                </VActionSpecial>
                            </div>

                            <!--extra options-->
                            <div class="h-fit flex flex-col mt-2 gap-2">
                                <div class="mx-auto flex flex-row items-center">
                                    <span class="text-base block">Don't have an account?&nbsp;</span>
                                    <div v-if="propIsForStaticPage === true">
                                        <VActionTextOnly
                                            :propIsIconOnly="true"
                                            propElement="a"
                                            propElementSize="s"
                                            propFontSize="s"
                                            href="/signup"
                                        >
                                            <span class="font-bold">Sign up</span>
                                        </VActionTextOnly>
                                    </div>
                                    <div v-else>
                                        <VActionTextOnly
                                            :propIsIconOnly="true"
                                            @click.stop="doNavigation('sign-up-section', 'sign-up-step-1', false)"
                                            propElement="button"
                                            propElementSize="s"
                                            propFontSize="s"
                                            type="button"
                                        >
                                            <span class="font-bold">Sign up</span>
                                        </VActionTextOnly>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </TransitionGroupSlide>
                </div>

                <!--signup-->
                <div
                    v-else-if="current_section === 'sign-up-section'"
                    class="h-full flex flex-col relative overflow-hidden"
                >

                    <TransitionGroupSlide
                        :prop-is-forward="transition_slide_is_forward"
                    >
                        <!--step 0-->
                        <div
                            class="w-full h-full flex flex-col p-2"
                            v-show="current_step === 'sign-up-step-0'"
                        >

                            <!--choices-->
                            <div class="flex flex-col">

                                <div class="flex flex-col gap-4 mt-6">
                                    <VAction
                                        @click.stop="doNavigation('sign-up-section', 'sign-up-step-1')"
                                        propElement="button"
                                        type="button"
                                        propElementSize="s"
                                        propFontSize="s"
                                        class="w-full px-4 gap-4"
                                    >
                                        <i class="fas fa-hat-wizard text-2xl"></i>
                                        <span>Sign in with email</span>
                                    </VAction>
                                </div>
                            </div>

                            <!--extra options-->
                            <div class="h-fit flex flex-col mt-2 gap-2">
                                <div class="mx-auto flex flex-row items-center">
                                    <span class="text-base block">Already have an account?&nbsp;</span>
                                    <div v-if="propIsForStaticPage === true">
                                        <VActionTextOnly
                                            :propIsIconOnly="true"
                                            propElement="a"
                                            propElementSize="s"
                                            propFontSize="s"
                                            href="/login"
                                        >
                                            <span class="font-bold">Log in</span>
                                        </VActionTextOnly>
                                    </div>
                                    <div v-else>
                                        <VActionTextOnly
                                            :propIsIconOnly="true"
                                            @click.stop="doNavigation('log-in-section', 'log-in-step-0', false)"
                                            propElement="button"
                                            propElementSize="s"
                                            propFontSize="s"
                                            type="button"
                                        >
                                            <span class="font-bold">Log in</span>
                                        </VActionTextOnly>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!--step 1-->
                        <div
                            class="w-full h-full flex flex-col p-2"
                            v-show="current_step === 'sign-up-step-1'"
                        >

                            <p class="text-xl font-medium block">
                                Sign up and chat with others!
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
                                @hasNewValue="handleNewEmail($event)"
                                class="mt-6"
                            />

                            <!--main action-->
                            <div class="mt-8 w-full h-fit">
                                <VActionSpecial
                                    @click.stop="submitStep1('sign-up')"
                                    :propIsEnabled="!is_email_loading"
                                    propElement="button"
                                    type="button"
                                    propElementSize="m"
                                    propFontSize="m"
                                    class="w-full"
                                >
                                    <span class="mx-auto">Next</span>
                                </VActionSpecial>
                            </div>

                            <!--extra options-->
                            <div class="h-fit flex flex-col mt-2">
                                <div class="mx-auto flex flex-row items-center">
                                    <span class="text-base block">Already have an account?&nbsp;</span>
                                    <div v-if="propIsForStaticPage === true">
                                        <VActionTextOnly
                                            :propIsIconOnly="true"
                                            propElement="a"
                                            propElementSize="s"
                                            propFontSize="s"
                                            href="/login"
                                        >
                                            <span class="font-bold">Log in</span>
                                        </VActionTextOnly>
                                    </div>
                                    <div v-else>
                                        <VActionTextOnly
                                            :propIsIconOnly="true"
                                            @click.stop="doNavigation('log-in-section', 'log-in-step-1', false)"
                                            propElement="button"
                                            propElementSize="s"
                                            propFontSize="s"
                                            type="button"
                                        >
                                            <span class="font-bold">Log in</span>
                                        </VActionTextOnly>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!--step 2-->
                        <div
                            class="w-full h-full flex flex-col p-2"
                            v-show="current_step === 'sign-up-step-2'"
                        >

                            <VActionTextOnly
                                :propIsIconOnly="true"
                                @click.stop="[doNavigation('sign-up-section', 'sign-up-step-1', false)]"
                                propElement="button"
                                propElementSize="s"
                                propFontSize="s"
                                type="button"
                                class="w-fit"
                            >
                                <div class="flex items-center">
                                    <i class="fas fa-arrow-left w-fit h-fit text-2xl block pr-2"></i>
                                    <span class="font-bold break-words">Back to email</span>
                                </div>
                            </VActionTextOnly>

                            <p class="text-xl font-medium block">
                                Enter the sign-up code.
                            </p>
                            <p class="text-base block">
                                <span class="break-words">{{ email_string }}</span>
                            </p>

                            <VNumberSlots
                                @hasNewValue="handleNewOTP($event)"
                                prop-element-id="sign-up-otp"
                                prop-label-text="Sign-up code"
                                :prop-extra-slots="calcExtraVNumberSlots"
                                :prop-trigger-reset="email_has_change"
                                :prop-is-error="otp_validation_has_error"
                                :prop-status-text="otp_validation_status_text"
                                class="mt-6"
                            />

                            <!--resend OTP-->
                            <div class="h-10 flex flex-row items-center">
                                <span class="text-base">{{ otp_request_status_text }}&nbsp;</span>
                                <VActionTextOnly
                                    :propIsIconOnly="true"
                                    v-show="canSubmitEmailAndRequestOTP"
                                    @click.stop="submitEmailAndRequestOTP('sign-up', true)"
                                    propElement="button"
                                    propElementSize="s"
                                    propFontSize="s"
                                    type="button"
                                >
                                    <span class="font-bold">Resend</span>
                                </VActionTextOnly>
                            </div>

                            <!--main action-->
                            <div class="mt-8 h-fit">
                                <VActionSpecial
                                    @click.stop="submitStep2('sign-up')"
                                    :propIsEnabled="!is_main_action_loading"
                                    propElement="button"
                                    type="button"
                                    propElementSize="m"
                                    propFontSize="m"
                                    class="w-full"
                                >
                                    <span class="mx-auto">Sign up</span>
                                </VActionSpecial>
                            </div>

                            <!--extra options-->
                            <div class="h-fit flex flex-col mt-2">
                                <div class="mx-auto flex flex-row items-center">
                                    <span class="text-base block">Already have an account?&nbsp;</span>
                                    <div v-if="propIsForStaticPage === true">
                                        <VActionTextOnly
                                            :propIsIconOnly="true"
                                            propElement="a"
                                            propElementSize="s"
                                            propFontSize="s"
                                            href="/login"
                                        >
                                            <span class="font-bold">Log in</span>
                                        </VActionTextOnly>
                                    </div>
                                    <div v-else>
                                        <VActionTextOnly
                                            :propIsIconOnly="true"
                                            @click.stop="doNavigation('log-in-section', 'log-in-step-1', false)"
                                            propElement="button"
                                            propElementSize="s"
                                            propFontSize="s"
                                            type="button"
                                        >
                                            <span class="font-bold">Log in</span>
                                        </VActionTextOnly>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </TransitionGroupSlide>
                </div>
            </TransitionFade>
        </div>
    </div>

</template>

<style scoped>
</style>


<script setup lang="ts">
    import VInput from '@/components/small/VInput.vue';
    import VTitle from '@/components/small/VTitle.vue';
    import VNumberSlots from '@/components/small/VNumberSlots.vue';
    import VActionTextOnly from '@/components/small/VActionTextOnly.vue';
    import TransitionGroupSlide from '@/transitions/TransitionGroupSlide.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VAction from '@/components/small/VAction.vue';
    import VActionSpecial from '@/components/small/VActionSpecial.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { notify } from 'notiwind';
    const axios = require('axios');

    interface StepsType {
        [key: number]: string[],
    }

    export default defineComponent({
        name: "UserLogInSignUp",
        data() {
            return {
                email_string: "",
                email_check_timeout: null as number|null,
                email_is_ok: false,
                email_validation_has_error: false,
                email_validation_status_text: "",

                otp_string: "",
                otp_length: 6,
                otp_is_ok: false,
                otp_validation_has_error: false,
                otp_validation_status_text: "",

                otp_request_cooldown_interval: null as number|null,
                otp_request_cooldown_duration_s: 30,
                otp_request_cooldown_s: 0,
                otp_request_status_text: "",
                otp_request_is_first_time: true,
                email_has_change: false,    //used to determine whether otp resets

                //handle loading
                is_loading: false,
                is_main_action_loading: false,
                is_email_loading: false,

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
        props: {
            //if for static page, title is removed, and sign up/log in toggles are replaced with URLs
            propIsForStaticPage: {
                type: Boolean,
                default: false
            },
            propRequestedSection: {
                type: String,
                required: true
            },
        },
        watch: {
            propRequestedSection(new_value:string){

                this.doNavigation(
                    new_value,
                    this.steps[this.sections.indexOf(new_value)][1]
                );
            },
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
            canSubmitEmailAndRequestOTP() : boolean {

                return this.email_is_ok === true && this.otp_request_cooldown_interval === null && this.is_loading === false;
            }
        },
        emits: [
            'isClosed',
        ],
        methods: {
            submitStep2(section_type:'log-in'|'sign-up') : void {

                this.validateOTP(this.otp_string);

                if(this.otp_is_ok === true){

                    this.submitOTPToGetNewSession(section_type);
                }
            },
            submitStep1(section_type:'log-in'|'sign-up') : void {

                //we need this because we no longer disable submit button on invalid
                //we let users freely click, and when trying to submit an invalid form, say what is wrong

                if(this.email_string.length === 0){

                    //use validateEmail() to raise empty email error
                    this.validateEmail(this.email_string);
                    return;

                }else if(this.email_is_ok === false){

                    //already handled by handleNewEmail()
                    return;
                }

                this.doNavigation(
                    section_type+'-section',
                    section_type+'-step-2'
                );
                this.submitEmailAndRequestOTP(section_type);
            },
            emitIsClosed() : void {

                //intentional ''
                this.$emit('isClosed', '');
            },
            resetOTPRelatedValues() : void {

                this.otp_string = "";
                this.otp_is_ok = false;
                this.otp_validation_has_error = false;
                this.otp_validation_status_text = "";

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
            doNavigation(section:string="", step:string="", transition_slide_is_forward=true) : void {

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
            async submitOTPToGetNewSession(procedure_url:"log-in"|"sign-up") : Promise<void> {

                if(this.otp_is_ok === false){

                    return;
                }

                this.is_main_action_loading = true;

                let data = new FormData();
                data.append("email", this.email_string);
                data.append("otp", this.otp_string);

                await axios.post(window.location.origin + "/api/users/" + procedure_url, data)
                .then((response:any) => {

                    //200 when ok
                    console.log(response.data['message']);
                    window.location.href = window.location.origin;

                })
                .catch((error: any) => {

                    //400 when invalid
                    this.is_main_action_loading = false;
                    notify({
                        title: procedure_url === "log-in" ? 'Login failed' : 'Sign-up failed',
                        text: error.response.data['message'],
                        type: "error"
                    }, 3000);
                });
            },
            async submitEmailAndRequestOTP(procedure_url:"log-in"|"sign-up", is_resubmit=false) : Promise<void> {

                //no need to proceed if error on validating email
                //no need to proceed if email from step 1 to 2 has no change
                if(this.email_is_ok === false || (this.email_has_change === false && is_resubmit === false)){

                    return;
                }

                //reset step 2 if handleNewEmail() detects email change
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

                await axios.post(window.location.origin + "/api/users/" + procedure_url, data)
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
                    notify({
                        title: "OTP request failed",
                        text: error.response.data['message'],
                        type: "error"
                    }, 3000);
                });
            },
            validateOTP(new_value:string) : void {

                //VNumberSlots only returns full string when successful and valid
                if(new_value.length < this.otp_length){

                    this.otp_is_ok = false;
                    this.otp_validation_has_error = true;
                    this.otp_validation_status_text = "Please enter the full code.";

                }else if(/^[0-9]+$/.test(new_value) === true && new_value.length === this.otp_length){

                    this.otp_is_ok = true;
                    this.otp_validation_has_error = false;
                    this.otp_validation_status_text = "";
                }
            },
            handleNewOTP(new_value:string) : void {

                //no on-the-spot validation needed
                this.otp_string = new_value;

                //reset so that validateOTP() later can trigger watch
                this.otp_validation_has_error = false;
                this.otp_validation_status_text = "";
            },
            validateEmail(new_value:string) : void {

                    //must not have any whitespace, must have "@" and ".", must have char before "@"
                    //do not make this too complicated, it is easier to just send email and see if user receives it
                    if(new_value.length === 0){

                        this.email_is_ok = false;
                        this.email_validation_has_error = true;
                        this.email_validation_status_text = "Please enter an email address.";

                    }else if(/^\S+@\S+\.\S+$/.test(new_value) === true){

                        this.email_is_ok = true;
                        this.email_validation_has_error = false;
                        this.email_validation_status_text = "All good!";

                    }else if(/\s+/g.test(new_value) === true){

                        this.email_is_ok = false;
                        this.email_validation_has_error = true;
                        this.email_validation_status_text = "Please remove all spaces.";

                    }else{

                        this.email_is_ok = false;
                        this.email_validation_has_error = true;
                        this.email_validation_status_text = "Does not look like a proper email.";
                    }

                    //maximum 254 characters for email
                    //since email path has 256 limit and needs to add "<" and ">"
                    //https://stackoverflow.com/questions/386294/what-is-the-maximum-length-of-a-valid-email-address
            },
            handleNewEmail(new_value:string) : void {

                //reset everything on any change
                this.resetEmailRelatedValues();

                this.email_has_change = true;
                this.email_string = new_value;
                
                //do nothing if there is no text
                if(new_value.length === 0){

                    return;
                }

                //has text
                this.is_email_loading = true;

                this.email_check_timeout = window.setTimeout(() => {

                    this.validateEmail(new_value);
                    this.is_email_loading = false;
                }, 400);
            },
        },
        beforeMount(){

            //watcher does not check props on first time mounting
            //so we repeat the procedure here
            this.doNavigation(
                    this.propRequestedSection,
                    this.steps[this.sections.indexOf(this.propRequestedSection)][1]
            );
        }
    });
</script>