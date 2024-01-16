<template>
    <div
        class="text-theme-black pb-10"
    >

        <!--close button, also functioning as pt-10-->
        <div
            v-if="propIsForStaticPage === false"
            class="h-10 relative"
        >
            <VActionText
                :propIsIconOnly="true"
                @click="forceClose()"
                propElement="button"
                propElementSize="s"
                type="button"
                class="w-10 absolute top-1 -right-3 m-auto"
            >
                <FontAwesomeIcon icon="fas fa-xmark" class="mx-auto text-xl"/>
                <span v-show="current_section === 'log-in-section'" class="sr-only">close login menu</span>
                <span v-show="current_section === 'sign-up-section'" class="sr-only">close sign-up menu</span>
            </VActionText>
        </div>

        <!--
            currently, title has pb-2, and the steps have pt-6
            the steps have pt-6 so the "back" button can do -top-4 without its outline being clipped
            these are ultimately to space "back" button more appropriately, while keeping overall height constraint
        -->

        <!--title-->
        <VTitle
            v-if="propIsForStaticPage === false"
            propFontSize="l"
            class="pb-2"
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
                            class="w-full h-full flex flex-col p-2 pt-6"
                            v-show="current_step === 'log-in-step-0'"
                        >

                            <!--choices-->
                            <div class="flex flex-col">

                                <div class="flex flex-col gap-4 mt-6">
                                    <VAction
                                        @click="doNavigation('log-in-section', 'log-in-step-1')"
                                        propElement="button"
                                        type="button"
                                        propElementSize="s"
                                        propFontSize="s"
                                        class="w-full px-4 gap-4"
                                    >
                                        <FontAwesomeIcon icon="fas fa-hat-wizard" class="text-2xl"/>
                                        <span>Log in with email</span>
                                    </VAction>
                                </div>
                            </div>

                            <!--extra options-->
                            <div class="h-fit flex flex-col mt-2 gap-2">
                                <div class="mx-auto flex flex-row items-center">
                                    <span class="text-base block">Don't have an account?&nbsp;</span>
                                    <div v-if="propIsForStaticPage === true">
                                        <VActionText
                                            :propIsIconOnly="true"
                                            propElement="a"
                                            propElementSize="s"
                                            propFontSize="s"
                                            href="/signup"
                                        >
                                            <span class="font-bold">Sign up</span>
                                        </VActionText>
                                    </div>
                                    <div v-else>
                                        <VActionText
                                            :propIsIconOnly="true"
                                            @click="switchContextInstance('sign-up-section')"
                                            propElement="button"
                                            propElementSize="s"
                                            propFontSize="s"
                                            type="button"
                                        >
                                            <span class="font-bold">Sign up</span>
                                        </VActionText>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!--step 1-->
                        <div
                            class="w-full h-full flex flex-col p-2 pt-6"
                            v-show="current_step === 'log-in-step-1'"
                        >

                            <VTitle propFontSize="l">
                                <template #titleDescription>
                                    <span>Log in and rejoin the fun!</span>
                                </template>
                            </VTitle>

                            <VInput
                                propElementId="user-log-in-email-input"
                                propLabel="Email"
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
                                    @click="submitStep1('log-in')"
                                    :propIsEnabled="!is_email_loading"
                                    propElement="button"
                                    type="button"
                                    propElementSize="m"
                                    propFontSize="l"
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
                                        <VActionText
                                            :propIsIconOnly="true"
                                            propElement="a"
                                            propElementSize="s"
                                            propFontSize="s"
                                            href="/signup"
                                        >
                                            <span class="font-bold">Sign up</span>
                                        </VActionText>
                                    </div>
                                    <div v-else>
                                        <VActionText
                                            :propIsIconOnly="true"
                                            @click="switchContextInstance('sign-up-section')"
                                            propElement="button"
                                            propElementSize="s"
                                            propFontSize="s"
                                            type="button"
                                        >
                                            <span class="font-bold">Sign up</span>
                                        </VActionText>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!--step 2-->
                        <div
                            class="w-full h-full flex flex-col p-2 pt-6"
                            v-show="current_step === 'log-in-step-2'"
                        >

                            <div class="h-10 relative">
                                <VActionText
                                    :propIsIconOnly="true"
                                    @click="doNavigation('log-in-section', 'log-in-step-1', false)"
                                    propElement="button"
                                    propElementSize="s"
                                    propFontSize="s"
                                    type="button"
                                    class="w-fit absolute -top-4"
                                >
                                    <div class="flex items-center">
                                        <FontAwesomeIcon icon="fas fa-arrow-left" class="text-lg pr-2"/>
                                        <span class="font-bold break-words">Back</span>
                                    </div>
                                </VActionText>
                            </div>

                            <VTitle propFontSize="l">
                                <template #titleDescription>
                                    <span>Enter the login code.</span>
                                </template>
                            </VTitle>
                            <p class="text-base block">
                                <span class="break-words">{{ email_string }}</span> 
                            </p>

                            <VNumberSlots
                                @hasNewValue="handleNewOTP($event)"
                                prop-element-id="log-in-otp"
                                prop-label-text="Login code"
                                :prop-extra-slots="calcExtraVNumberSlots"
                                :prop-trigger-reset="otp_fields_reset_trigger"
                                :prop-is-error="otp_validation_has_error"
                                :prop-status-text="otp_validation_status_text"
                                class="mt-6"
                            />

                            <!--resend OTP-->
                            <div class="h-10 flex flex-row items-center shrink-0 text-theme-black">

                                <div
                                    v-show="is_otp_request_loading"
                                    class="text-base"
                                >
                                    <VLoading propElementSize="s">
                                        <span class="pl-1">Sending login code...</span>
                                    </VLoading>
                                </div>

                                <span
                                    v-show="!is_otp_request_loading"
                                    class="text-base"
                                >
                                    {{ otp_request_status_text }}&nbsp;
                                </span>
                                <VActionText
                                    :propIsIconOnly="true"
                                    v-show="canSubmitEmailAndRequestOTP"
                                    @click="submitEmailAndRequestOTP('log-in', true)"
                                    propElement="button"
                                    propElementSize="s"
                                    propFontSize="s"
                                    type="button"
                                >
                                    <span class="font-bold">Resend</span>
                                </VActionText>
                            </div>

                            <!--main action-->
                            <div class="mt-8 h-fit">
                                <VActionSpecial
                                    @click="submitStep2('log-in')"
                                    :propIsEnabled="!is_main_action_loading"
                                    propElement="button"
                                    type="button"
                                    propElementSize="m"
                                    propFontSize="l"
                                    class="w-full"
                                >
                                    <!--putting TransitionFade here seems to break things-->
                                    <!--i.e. renders v-if and v-else once then permanently disappearing-->
                                    <VLoading
                                        v-if="is_main_action_loading"
                                        propElementSize="m"
                                        class="mx-auto"
                                    >
                                        <span class="pl-2">Logging in...</span>
                                    </VLoading>

                                    <span v-else class="mx-auto">
                                        Log in
                                    </span>
                                </VActionSpecial>
                            </div>

                            <!--extra options-->
                            <div class="h-fit flex flex-col mt-2 gap-2">
                                <div class="mx-auto flex flex-row items-center">
                                    <span class="text-base block">Don't have an account?&nbsp;</span>
                                    <div v-if="propIsForStaticPage === true">
                                        <VActionText
                                            :propIsIconOnly="true"
                                            propElement="a"
                                            propElementSize="s"
                                            propFontSize="s"
                                            href="/signup"
                                        >
                                            <span class="font-bold">Sign up</span>
                                        </VActionText>
                                    </div>
                                    <div v-else>
                                        <VActionText
                                            :propIsIconOnly="true"
                                            @click="switchContextInstance('sign-up-section')"
                                            propElement="button"
                                            propElementSize="s"
                                            propFontSize="s"
                                            type="button"
                                        >
                                            <span class="font-bold">Sign up</span>
                                        </VActionText>
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
                            class="w-full h-full flex flex-col p-2 pt-6"
                            v-show="current_step === 'sign-up-step-0'"
                        >

                            <!--choices-->
                            <div class="flex flex-col">

                                <div class="flex flex-col gap-4 mt-6">
                                    <VAction
                                        @click="doNavigation('sign-up-section', 'sign-up-step-1')"
                                        propElement="button"
                                        type="button"
                                        propElementSize="s"
                                        propFontSize="s"
                                        class="w-full px-4 gap-4"
                                    >
                                        <FontAwesomeIcon icon="fas fa-hat-wizard" class="text-2xl"/>
                                        <span>Sign in with email</span>
                                    </VAction>
                                </div>
                            </div>

                            <!--extra options-->
                            <div class="h-fit flex flex-col mt-2 gap-2">
                                <div class="mx-auto flex flex-row items-center">
                                    <span class="text-base block">Already have an account?&nbsp;</span>
                                    <div v-if="propIsForStaticPage === true">
                                        <VActionText
                                            :propIsIconOnly="true"
                                            propElement="a"
                                            propElementSize="s"
                                            propFontSize="s"
                                            href="/login"
                                        >
                                            <span class="font-bold">Log in</span>
                                        </VActionText>
                                    </div>
                                    <div v-else>
                                        <VActionText
                                            :propIsIconOnly="true"
                                            @click="switchContextInstance('log-in-section')"
                                            propElement="button"
                                            propElementSize="s"
                                            propFontSize="s"
                                            type="button"
                                        >
                                            <span class="font-bold">Log in</span>
                                        </VActionText>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!--step 1-->
                        <div
                            class="w-full h-full flex flex-col p-2 pt-6"
                            v-show="current_step === 'sign-up-step-1'"
                        >

                            <VTitle propFontSize="l">
                                <template #titleDescription>
                                    <span>Sign up and chat with others!</span>
                                </template>
                            </VTitle>

                            <VInput
                                propElementId="user-sign-up-email-input"
                                propLabel="Email"
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
                                    @click="submitStep1('sign-up')"
                                    :propIsEnabled="!is_email_loading"
                                    propElement="button"
                                    type="button"
                                    propElementSize="m"
                                    propFontSize="l"
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
                                        <VActionText
                                            :propIsIconOnly="true"
                                            propElement="a"
                                            propElementSize="s"
                                            propFontSize="s"
                                            href="/login"
                                        >
                                            <span class="font-bold">Log in</span>
                                        </VActionText>
                                    </div>
                                    <div v-else>
                                        <VActionText
                                            :propIsIconOnly="true"
                                            @click="switchContextInstance('log-in-section')"
                                            propElement="button"
                                            propElementSize="s"
                                            propFontSize="s"
                                            type="button"
                                        >
                                            <span class="font-bold">Log in</span>
                                        </VActionText>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!--step 2-->
                        <div
                            class="w-full h-full flex flex-col p-2 pt-6"
                            v-show="current_step === 'sign-up-step-2'"
                        >
                            <div class="h-10 relative">
                                <VActionText
                                    :propIsIconOnly="true"
                                    @click="[doNavigation('sign-up-section', 'sign-up-step-1', false)]"
                                    propElement="button"
                                    propElementSize="s"
                                    propFontSize="s"
                                    type="button"
                                    class="w-fit absolute -top-4"
                                >
                                    <div class="flex items-center">
                                        <FontAwesomeIcon icon="fas fa-arrow-left" class="text-lg pr-2"/>
                                        <span class="font-bold break-words">Back</span>
                                    </div>
                                </VActionText>
                            </div>

                            <VTitle propFontSize="l">
                                <template #titleDescription>
                                    <span>Enter the sign-up code.</span>
                                </template>
                            </VTitle>
                            <p class="text-base block">
                                <span class="break-words">{{ email_string }}</span>
                            </p>

                            <VNumberSlots
                                @hasNewValue="handleNewOTP($event)"
                                prop-element-id="sign-up-otp"
                                prop-label-text="Sign-up code"
                                :prop-extra-slots="calcExtraVNumberSlots"
                                :prop-trigger-reset="otp_fields_reset_trigger"
                                :prop-is-error="otp_validation_has_error"
                                :prop-status-text="otp_validation_status_text"
                                class="mt-6"
                            />

                            <!--resend OTP-->
                            <div class="h-10 flex flex-row items-center shrink-0 text-theme-black">

                                <div
                                    v-show="is_otp_request_loading"
                                    class="text-base"
                                >
                                    <VLoading propElementSize="s">
                                        <span class="pl-1">Sending sign-up code...</span>
                                    </VLoading>
                                </div>

                                <span
                                    v-show="!is_otp_request_loading"
                                    class="text-base"
                                >
                                    {{ otp_request_status_text }}&nbsp;
                                </span>
                                <VActionText
                                    :propIsIconOnly="true"
                                    v-show="canSubmitEmailAndRequestOTP"
                                    @click="submitEmailAndRequestOTP('log-in', true)"
                                    propElement="button"
                                    propElementSize="s"
                                    propFontSize="s"
                                    type="button"
                                >
                                    <span class="font-bold">Resend</span>
                                </VActionText>
                            </div>

                            <!--main action-->
                            <div class="mt-8 h-fit">
                                <VActionSpecial
                                    @click="submitStep2('sign-up')"
                                    :propIsEnabled="!is_main_action_loading"
                                    propElement="button"
                                    type="button"
                                    propElementSize="m"
                                    propFontSize="l"
                                    class="w-full"
                                >
                                    <VLoading
                                        v-if="is_main_action_loading"
                                        propElementSize="m"
                                        class="mx-auto"
                                    >
                                        <span class="pl-2">Signing up...</span>
                                    </VLoading>

                                    <span v-else class="mx-auto">
                                        Sign up
                                    </span>
                            </VActionSpecial>
                            </div>

                            <!--extra options-->
                            <div class="h-fit flex flex-col mt-2">
                                <div class="mx-auto flex flex-row items-center">
                                    <span class="text-base block">Already have an account?&nbsp;</span>
                                    <div v-if="propIsForStaticPage === true">
                                        <VActionText
                                            :propIsIconOnly="true"
                                            propElement="a"
                                            propElementSize="s"
                                            propFontSize="s"
                                            href="/login"
                                        >
                                            <span class="font-bold">Log in</span>
                                        </VActionText>
                                    </div>
                                    <div v-else>
                                        <VActionText
                                            :propIsIconOnly="true"
                                            @click="switchContextInstance('log-in-section')"
                                            propElement="button"
                                            propElementSize="s"
                                            propFontSize="s"
                                            type="button"
                                        >
                                            <span class="font-bold">Log in</span>
                                        </VActionText>
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
    import VActionText from '@/components/small/VActionText.vue';
    import TransitionGroupSlide from '@/transitions/TransitionGroupSlide.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VAction from '@/components/small/VAction.vue';
    import VActionSpecial from '@/components/small/VActionSpecial.vue';
    import VLoading from '../small/VLoading.vue';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faXmark } from '@fortawesome/free-solid-svg-icons/faXmark';
    import { faHatWizard } from '@fortawesome/free-solid-svg-icons/faHatWizard';
    import { faArrowLeft } from '@fortawesome/free-solid-svg-icons/faArrowLeft';

    library.add(faXmark, faHatWizard, faArrowLeft);
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import { emailValidatorDjango, prettyTimeRemaining } from '@/helper_functions';
    import { usePageRefreshTriggerStore } from '@/stores/PageRefreshTriggerStore';
    import { usePopUpManagerStore } from '@/stores/PopUpManagerStore';
    const axios = require('axios');

    interface StepsType {
        [key: number]: string[],
    }
    type SectionsValues = "log-in-section"|"sign-up-section"
    type SectionsArray = ["log-in-section", "sign-up-section"]

    export default defineComponent({
        name: "UserLogInSignUp",
        data() {
            return {
                page_refresh_trigger_store: usePageRefreshTriggerStore(),
                pop_up_manager_store: usePopUpManagerStore(),

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
                otp_can_auto_submit: true,  //auto-submit when OTP is fully entered, is false on error, true on code resend
                otp_fields_reset_trigger: false,    //toggle to trigger VNumberSlots reset

                otp_request_cooldown_interval: null as number|null,
                otp_request_cooldown_duration_s: 30,
                otp_request_cooldown_s: 0,
                otp_request_status_text: "",
                otp_request_is_first_time: true,
                email_has_change: false,

                //handle loading
                is_otp_request_loading: false,
                is_main_action_loading: false,
                is_email_loading: false,

                current_section: "" as SectionsValues,
                sections: ["log-in-section", "sign-up-section"] as SectionsArray,

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
                type: String as PropType<SectionsValues>,
                required: true,
                default: "log-in-section"
            },
        },
        watch: {
            propRequestedSection(new_value:SectionsValues){

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

                return (
                    this.email_is_ok === true &&
                    this.otp_request_cooldown_interval === null &&
                    this.is_otp_request_loading === false
                );
            }
        },
        methods: {
            async submitStep2(section_type:'log-in'|'sign-up') : Promise<void> {

                await this.validateOTP(this.otp_string);

                if(this.otp_is_ok === true){

                    this.submitOTPToGetNewSession(section_type);
                }
            },
            async submitStep1(section_type:'log-in'|'sign-up') : Promise<void> {

                //we need this because we no longer disable submit button on invalid
                //we let users freely click, and when trying to submit an invalid form, say what is wrong

                if(this.email_string.length === 0){

                    //use validateEmail() to raise empty email error
                    await this.validateEmail(this.email_string);
                    return;

                }else if(this.email_is_ok === false){

                    //already handled by handleNewEmail()
                    return;
                }

                this.doNavigation(
                    section_type+'-section' as SectionsValues,
                    section_type+'-step-2'
                );
                this.submitEmailAndRequestOTP(section_type);
            },
            async forceClose() : Promise<void> {

                this.pop_up_manager_store.toggleIsUserLogInOpen(false);
                this.pop_up_manager_store.toggleIsUserSignUpOpen(false);
            },
            async switchContextInstance(new_section:SectionsValues) : Promise<void> {

                //close current section, open new section

                if(new_section === 'log-in-section'){

                    await this.pop_up_manager_store.toggleIsUserLogInOpen(true);

                }else if(new_section === 'sign-up-section'){

                    await this.pop_up_manager_store.toggleIsUserSignUpOpen(true);
                }

            },
            async resetOTPRelatedValues() : Promise<void> {

                this.otp_string = "";
                this.otp_is_ok = false;
                this.otp_validation_has_error = false;
                this.otp_validation_status_text = "";
                this.otp_can_auto_submit = true;

                this.otp_request_cooldown_interval !== null ? window.clearTimeout(this.otp_request_cooldown_interval) : null;
                this.otp_request_cooldown_interval = null;
                this.otp_request_cooldown_s = 0;
                this.otp_request_status_text = "";
                this.email_has_change = false;

                this.resetOTPFields();
            },
            async resetEmailRelatedValues() : Promise<void> {

                this.email_string = "";
                this.email_check_timeout !== null ? window.clearTimeout(this.email_check_timeout) : null;
                this.email_is_ok = false;
                this.email_validation_has_error = false;
                this.email_validation_status_text = "";

                this.resetOTPFields();
            },
            doNavigation(section:SectionsValues, step:string="", transition_slide_is_forward=true) : void {

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
            async startRequestOTPCooldown(
                context:"sent"|"too_many_sent"="sent",
                timeout_s:number=0
            ) : Promise<void> {

                //reset
                this.otp_request_cooldown_interval !== null ? window.clearTimeout(this.otp_request_cooldown_interval) : null;
                this.otp_request_cooldown_interval = null;
                this.otp_request_cooldown_s = 0;
                this.otp_request_status_text = "";
                this.otp_can_auto_submit = true;

                //prepare values
                let status_text = "";

                if(context === "sent"){

                    status_text = "Code should arrive in ";
                    timeout_s = this.otp_request_cooldown_duration_s;

                }else if(context === "too_many_sent"){

                    status_text = "Too many codes sent. Retry in ";
                }

                //set cooldown seconds
                //-1 to account for setInterval() first-time delay
                this.otp_request_cooldown_s = timeout_s - 1;

                //have text already done during setInterval() first-time delay
                this.otp_request_status_text = status_text +
                    prettyTimeRemaining(0, ((this.otp_request_cooldown_s + 1) * 1000)) + '.';

                //interval itself for cooldown
                this.otp_request_cooldown_interval = window.setInterval(()=>{

                    if(this.otp_request_cooldown_s === 0 && this.otp_request_cooldown_interval !== null){

                        window.clearInterval(this.otp_request_cooldown_interval);
                        this.otp_request_cooldown_interval = null;
                        this.otp_request_status_text = "Didn't receive code?";
                        return;
                    }

                    if(this.otp_request_cooldown_s === 1){
                        this.otp_request_status_text = status_text +
                            prettyTimeRemaining(0, (this.otp_request_cooldown_s * 1000)) + '.';
                    }else{
                        this.otp_request_status_text = status_text +
                            prettyTimeRemaining(0, (this.otp_request_cooldown_s * 1000)) + '.';
                    }

                    this.otp_request_cooldown_s -= 1;

                }, 1000);
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
                .then(() => {

                    //doing this will refresh all open tabs/pages for us
                    this.page_refresh_trigger_store.$patch({
                        refresh_context: "logging_in"
                    });

                })
                .catch((error:any) => {

                    //400 when invalid
                    this.is_main_action_loading = false;
                    this.otp_validation_has_error = true;

                    if(error.request.status === 400){

                        this.otp_validation_status_text = "Incorrect code. Try again.";

                    }else{

                        this.otp_validation_status_text = "Something went wrong. Try again.";
                    }

                    //prevent auto-submit
                    this.otp_can_auto_submit = false;
                });
            },
            async submitEmailAndRequestOTP(procedure_url:"log-in"|"sign-up", is_resubmit=false) : Promise<void> {

                //no need to proceed if error on validating email
                //no need to proceed if email from step 1 to 2 has no change
                if(this.email_is_ok === false || (this.email_has_change === false && is_resubmit === false)){

                    return;
                }

                //reset step 2 if handleNewEmail() detects email change
                await this.resetOTPRelatedValues();

                this.is_otp_request_loading = true;

                let data = new FormData();
                data.append("email", this.email_string);
                data.append("is_requesting_new_otp", JSON.stringify(true));

                await axios.post(window.location.origin + "/api/users/" + procedure_url, data)
                .then(async () => {

                    await this.startRequestOTPCooldown();
                })
                .catch((error:any) => {

                    if(this.otp_request_cooldown_interval !== null){

                        window.clearInterval(this.otp_request_cooldown_interval);
                        this.otp_request_cooldown_interval = null;
                    }

                    //start cooldown when user has made too many otp requests

                    if(Object.hasOwn(error, 'request') === true && Object.hasOwn(error, 'response') === true){

                        if(
                            Object.hasOwn(error.response.data, 'error_code') &&
                            Object.hasOwn(error.response.data, 'timeout_s') &&
                            error.response.data['error_code'] === 'otp-creation-timeout'
                        ){

                            this.startRequestOTPCooldown("too_many_sent", error.response.data['timeout_s']);

                        }else{

                            this.otp_request_status_text = "Could not send code.";
                        }

                    }else{

                        this.otp_request_status_text = "Could not send code.";
                    }


                }).finally(()=>{

                    this.is_otp_request_loading = false;
                });
            },
            async validateOTP(new_value:string) : Promise<void> {

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
            async handleNewOTP(new_value:string) : Promise<void> {

                //no on-the-spot validation needed
                this.otp_string = new_value;

                //reset so that validateOTP() later can trigger watcher
                this.otp_validation_has_error = false;
                this.otp_validation_status_text = "";

                //handle auto-submit
                if(this.otp_can_auto_submit === true && new_value.length === this.otp_length){

                    const section_type = this.current_section.split("-section", 2)[0];

                    if(section_type === "log-in" || section_type === "sign-up"){

                        await this.submitStep2(section_type);
                    }
                }
            },
            async validateEmail(new_value:string) : Promise<void> {

                    //must not have any whitespace, must have "@" and ".", must have char before "@"
                    //do not make this too complicated, it is easier to just send email and see if user receives it
                    if(new_value.length === 0){

                        this.email_is_ok = false;
                        this.email_validation_has_error = true;
                        this.email_validation_status_text = "Please enter an email address.";

                    }else if(emailValidatorDjango(new_value) === true){

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
            async handleNewEmail(new_value:string) : Promise<void> {

                //reset everything on any change
                await this.resetEmailRelatedValues();

                this.email_has_change = true;
                this.email_string = new_value;
                
                //do nothing if there is no text
                if(new_value.length === 0){

                    return;
                }

                //has text

                this.is_email_loading = true;
                this.email_check_timeout !== null ? clearTimeout(this.email_check_timeout) : null;

                this.email_check_timeout = window.setTimeout(() => {

                    this.validateEmail(new_value);
                    this.is_email_loading = false;
                }, 400);
            },
            resetOTPFields() : void {

                this.otp_fields_reset_trigger = !this.otp_fields_reset_trigger;
            }
        },
        beforeMount(){

            //watcher does not check props on first time mounting
            //so we repeat the procedure here
            this.doNavigation(
                this.propRequestedSection,
                this.steps[this.sections.indexOf(this.propRequestedSection)][1]
            );
        },
    });
</script>