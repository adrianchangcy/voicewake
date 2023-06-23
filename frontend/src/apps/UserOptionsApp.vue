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
                            :propIsError="can_send_email === false"
                            :propIsOk="can_send_email === true"
                            propRegex="\s+"
                            @hasNewValue="validateEmail($event)"
                            class="mt-6"
                        />

                        <!--navigation-->
                        <div class="mt-8 w-full h-fit flex">
                            <VActionSpecialM
                                @click.stop="overrideNavigation('sign-in-section', 'sign-in-step-2')"
                                :propIsEnabled="true"
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
                            <span class="text-base block break-words">adrianchangcy@gmail.com</span>
                        </div>

                        <VNumberSlots
                            prop-element-id="sign-in-otp"
                            prop-label-text="6-digit code"
                            class="mt-6"
                        />

                        <VActionButtonTextOnly
                            :prop-is-enabled="true"
                            class="mt-8"
                        >
                            <span class="font-bold">Can resend in 30s</span>
                        </VActionButtonTextOnly>

                        <!--navigation-->
                        <div class="mt-8 h-fit">
                            <div class="flex flex-row items-center">
                                <div class="w-full">
                                    <VActionButtonTextOnly
                                        @click.stop="overrideNavigation('sign-in-section', 'sign-in-step-1', false)"
                                        :prop-is-enabled="true"
                                        class="flex-row"
                                    >
                                        <i class="fas fa-arrow-left w-fit h-fit text-2xl block my-auto pr-2"></i>
                                        <span class="block my-auto">Change email</span>
                                    </VActionButtonTextOnly>
                                </div>
                                <div>
                                    <VActionSpecialM
                                        :propIsEnabled="true"
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
                            :propIsError="can_send_email === false"
                            :propIsOk="can_send_email === true"
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

    interface StepsType {
        [key: number]: string[],
    }

    export default defineComponent({
        name: "UserOptionsApp",
        data() {
            return {
                email_validation_status_text: "",
                email_check_timeout: null as number|null,
                can_send_email: null as boolean|null,
                email_string: "",

                verification_code: "",
                can_resend_verification_code: false,
                verification_code_status_text: "",

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
                this.email_validation_status_text = "";
                this.can_send_email = null;
                this.email_string = "";
            },
        },
        computed: {
            canSubmitVerificationCode() : boolean {

                return this.verification_code !== "";
            },
        },
        methods: {
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
            proceedWithEmail() : void {

                console.log('');
            },
            sendVerificationCodeToEmail() : void {

                console.log('');
            },
            handleNewPIN(new_value:string) : void {

                //when VNumberSlots is not successful, always expect ""
                if(new_value.length > 0){

                    this.verification_code = new_value;

                }else{

                    this.verification_code = "";
                }
            },
            validateEmail(new_value:string) : void {

                this.can_send_email = null;
                this.email_string = "";

                //clear timeout
                if(this.email_check_timeout !== null){

                    clearTimeout(this.email_check_timeout);
                }
                
                //do nothing if there is no text
                if(new_value.length === 0){

                    return;
                }

                //has text
                this.email_check_timeout = window.setTimeout(() => {

                    //must not have any whitespace, must have "@" and ".", must have char before "@"
                    //do not make this too complicated, it is easier to just send email and see if user receives it
                    if(/^\S+@\S+\.\S+$/.test(new_value) === true) {

                        this.email_validation_status_text = "All good!";
                        this.email_string = new_value;
                        this.can_send_email = true;

                    }else{

                        this.email_validation_status_text = "That does not look like a proper email.";
                        this.can_send_email = false;
                    }

                    //maximum 254 characters for email
                    //since email path has 256 limit and needs to add "<" and ">"
                    //https://stackoverflow.com/questions/386294/what-is-the-maximum-length-of-a-valid-email-address

                }, 600);
            },
        },
        beforeMount(){

            this.current_section = this.sections[0];
            this.current_step = this.steps[0][0];
        },
    });
</script>