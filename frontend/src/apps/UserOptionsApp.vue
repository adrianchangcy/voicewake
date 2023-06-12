<template>
    <div class="w-full text-theme-black">
        <!--test-->
        <VTitleXL class="py-8">
            <template #title>
                <span class="block text-center">Create Account</span>
            </template>
        </VTitleXL>
        <p class="text-lg">Start with an email address.</p>
        <div class="mt-4 flex flex-col gap-10">
            <!--step 1, insert email-->
            <div>
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
                    ref="yolo"
                />

                <div class="h-fit flex flex-col items-end">
                    <VActionSpecialM
                        :propIsEnabled="can_send_email === true"
                        propElement="button"
                        :propIsRound="true"
                        type="button"
                        class="mt-8 flex items-center"
                    >
                        <i class="fas fa-arrow-right w-fit h-fit mx-auto"></i>
                        <span class="sr-only">continue</span>
                    </VActionSpecialM>
                </div>
            </div>

            <!--step 2, insert verification code and proceed, or resend-->
            <div>

                <!--email info-->
                <div class="flex flex-col">
                    <p class="text-lg text-theme-black block">
                        Verification code has been sent!
                    </p>
                    <span class="text-base font-light block break-words">adrianchangcy@gmail.com</span>
                </div>

                <!--verification code-->
                <div class="mt-8 flex flex-col">
                    <VNumberSlots
                        propLabelText="Enter 6-digit verification code"
                        propElementId="email-verification-code-input"
                        @hasNewValue="handleNewPIN($event)"
                    />

                    <VActionButtonTextOnly
                        class="mt-4"
                        :propIsEnabled="false"
                    >
                        <span>Resend code? Can resend in 27s</span>
                    </VActionButtonTextOnly>
                    <!--implement hidden logic to limit attempts, only showing when limit has been reached-->
                </div>

                <!--continue-->
                <div class="h-fit flex flex-col items-end">
                    <VActionSpecialM
                        :propIsEnabled="canSubmitVerificationCode"
                        propElement="button"
                        :propIsRound="true"
                        type="button"
                        class="mt-8 flex items-center"
                    >
                        <i class="fas fa-arrow-right w-fit h-fit mx-auto"></i>
                        <span class="sr-only">continue</span>
                    </VActionSpecialM>
                </div>
            </div>

            <!--step 3, confirm password-->
            <div>
                <VPassword
                    prop-element-id="new-password"
                    prop-label="New password"
                    :prop-has-status-text="true"
                    :prop-max-length="20"
                    @has-new-value="handleNewPassword($event)"
                />
                <div class="h-fit flex flex-col items-end">
                    <VActionButtonSpecialL
                        :propIsEnabled="canSignUpAndLogIn"
                        propElement="button"
                        :propIsRound="false"
                        type="button"
                        class="w-full mt-8 flex items-center"
                    >
                        <span class="mx-auto">Create Account</span>
                    </VActionButtonSpecialL>
                </div>
                <!--put password help/guide-->
                <!--allow browser to save password-->
            </div>

            <!--perhaps once process starts, show X button to exit and go back to main sign up page-->
        </div>
    </div>

</template>

<style scoped>
</style>


<script setup lang="ts">
    import VInput from '@/components/small/VInput.vue';
    import VTitleXL from '@/components/small/VTitleXL.vue';
    import VNumberSlots from '@/components/small/VNumberSlots.vue';
    import VActionSpecialM from '@/components/small/VActionSpecialM.vue';
    import VActionButtonSpecialL from '@/components/small/VActionButtonSpecialL.vue';
    import VPassword from '@/components/small/VPassword.vue';
    import VActionButtonTextOnly from '@/components/small/VActionButtonTextOnly.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';

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

                new_password: "",
                yolo: true,

            };
        },
        computed: {
            canSubmitVerificationCode() : boolean {

                return this.verification_code !== "";
            },
            canSignUpAndLogIn() : boolean {

                return this.new_password !== "";
            },
        },
        methods: {
            proceedWithEmail() : void {

                console.log('');
            },
            sendVerificationCodeToEmail() : void {

                console.log('');
            },
            handleNewPassword(new_value:string) : void {

                this.new_password = new_value;
            },
            handleNewPIN(new_value:string) : void {

                //when VNumberSlots is not successful, always expect ""
                if(new_value.length > 0){

                    this.verification_code = new_value;

                }else{

                    this.verification_code = "";
                }
            },
            validateEmail(new_email:string) : void {

                this.can_send_email = null;
                this.email_string = "";

                //clear timeout
                if(this.email_check_timeout !== null){

                    clearTimeout(this.email_check_timeout);
                }
                
                //do nothing if there is no text
                if(new_email.length === 0){

                    return;
                }

                //has text
                this.email_check_timeout = window.setTimeout(() => {

                    //must not have any whitespace, must have "@" and ".", must have char before "@"
                    //do not make this too complicated, it is easier to just send email and see if user receives it
                    if(/^\S+@\S+\.\S+$/.test(new_email) === true) {

                        this.email_validation_status_text = "All good!";
                        this.email_string = new_email;
                        this.can_send_email = true;

                    }else{

                        this.email_validation_status_text = "That does not look like a proper email.";
                        this.can_send_email = false;
                    }

                    //maximum 254 characters for email
                    //since email path has 256 limit and needs to add "<" and ">"
                    //https://stackoverflow.com/questions/386294/what-is-the-maximum-length-of-a-valid-email-address

                }, 1000);
            },
        },
        mounted(){
            setTimeout(()=>{this.yolo = false;}, 1000);
        }
    });
</script>