<template>
    <div class="text-left">
        <div class="w-full grid grid-cols-4">
            <VInputLabel
                :for="propElementId"
                class="col-span-3 w-fit"
            >
                {{propLabel}}
            </VInputLabel>
        </div>
        <div class="text-xl relative">
            <input
                ref="yolo"
                :required="propIsRequired"
                :type="inputTypeForPassword"
                :id="propElementId"
                v-model="input_value"
                class="w-full h-10 p-2 pr-11 bg-theme-light border-2 border-theme-medium-gray shade-border-when-hover rounded-lg    focus:outline-1 focus-visible:outline-1 focus:outline-offset-2 focus-visible:outline-offset-2 focus:outline-theme-accent focus-visible:outline-theme-accent focus:border-theme-black"
                :placeholder="propPlaceholder"
                autocomplete="off"
                spellcheck="false"
                :maxlength="propMaxLength"
            >
            <button
                @click.stop="togglePasswordShow()"
                class="w-12 h-full rounded-lg absolute right-0 top-0 bottom-0 m-auto flex items-center text-theme-black shade-text-when-hover transition-colors"
                type="button"
            >
                <i
                    class="fas text-xl mx-auto"
                    :class="show_password ? 'fa-eye' : 'fa-eye-slash'"
                ></i>
                <span v-show="show_password" class="sr-only">hide password</span>
                <span v-show="!show_password" class="sr-only">show password</span>
            </button>
        </div>
        <div v-show="propHasStatusText" class="h-6 text-base px-2">
            <span v-show="is_success" class="text-theme-toast-success">{{ status_text }}</span>
            <span v-show="is_warning" class="text-theme-toast-warning-2">{{ status_text }}</span>
            <span v-show="is_error" class="text-theme-toast-danger">{{ status_text }}</span>
        </div>

        <!--help-->
        <VActionButtonTextOnly
            class="mt-4"
        >
            <span>Password help?</span>
        </VActionButtonTextOnly>
    </div>
</template>


<script setup lang="ts">
    import VInputLabel from './VInputLabel.vue';
    import VActionButtonTextOnly from './VActionButtonTextOnly.vue';
</script>

<script lang="ts">

    //warning
    //when browser detects input + password, autofill occurs
    //there is no reliable way to capture the autofill

    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return {
                input_value: '',
                current_length: 0,
                show_password: false,
                validate_timeout: null as number|null,
                
                status_text: '',
                is_success: false,
                is_warning: false,
                is_error: false,
            };
        },
        props: {
            propIsRequired: Boolean,
            propElementId: String,
            propLabel: String,
            propPlaceholder: String,
            propMaxLength: Number,
            propHasStatusText: Boolean,
            propIsOk: Boolean,
            propIsWarning: Boolean,
            propIsError: Boolean,
        },
        emits: ['hasNewValue'],
        watch: {
            input_value(new_value){

                this.current_length = new_value.length;

                //reset
                this.status_text = "";
                this.validate_timeout !== null ? clearTimeout(this.validate_timeout) : null;
                this.$emit("hasNewValue", "");

                this.validate_timeout = window.setTimeout(() => {

                    //validate and emit
                    if(this.validateNewPassword(this.input_value) === true){

                        this.$emit("hasNewValue", this.input_value);
                    }
                }, 600);
            },
        },
        computed: {
            inputTypeForPassword() : string {

                if(this.show_password === true){

                    return "text";
                }

                return "password";
            },
        },
        methods: {
            validateNewPassword(new_value:string, minimum_passed:number=2) : boolean {

                let passed_count = 0;
                this.is_success = false;
                this.is_warning = false;
                this.is_error = false;

                //length
                if(new_value.length < 8){

                    this.status_text = "Password must have at least 8 characters.";
                    this.is_error = true;
                    return false;
                }

                //has >= 1 uppercase
                if(/(?=.*[A-Z])/.test(new_value) === true){

                    passed_count += 1;
                }

                //has >= 1 number
                if(/(?=.*[0-9])/.test(new_value) === true){

                    passed_count += 1;
                }

                //has >= 1 non-letter and non-number (space, etc.)
                if(/([^0-9a-zA-Z])/.test(new_value) === true){

                    passed_count += 1;
                }

                //very strong requires >= 14
                if(new_value.length >= 14){

                    passed_count += 1;
                }

                switch(passed_count){

                    case 0:
                        this.status_text = "Weak. Too easy to hack!";
                        this.is_error = true;
                        break;

                    case 1:
                        this.status_text = "Weak. Too easy to hack!";
                        this.is_error = true;
                        break;

                    case 2:
                        this.status_text = "Decent.";
                        this.is_warning = true;
                        break;

                    case 3:
                        this.status_text = "Strong!";
                        this.is_success = true;
                        break;

                    case 4:
                        this.status_text ="Extra strong!";
                        this.is_success = true;
                        break;

                    default:
                        break;
                }

                //follows guide below
                //https://auth0.com/blog/dont-pass-on-the-new-nist-password-guidelines/
                //https://www.section.io/engineering-education/password-strength-checker-javascript/
                
                if(passed_count >= minimum_passed){

                    return true;
                }

                return false;
            },
            togglePasswordShow() : void {

                this.show_password = !this.show_password;
            }

        },
    });
</script>