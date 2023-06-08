<template>
    <div class="text-left">
        <div class="w-full grid grid-cols-4">
            <VInputLabel
                class="col-span-3 w-fit"
                :for="propElementId"
            >
                {{propLabel}}
            </VInputLabel>
            <VInputLabel
                v-if="propHasTextCounter"
                class="col-span-1 w-full text-right"
            >
                {{current_length}}/{{propMaxLength}}
            </VInputLabel>
        </div>
        <div class="text-xl relative">
            <input
                :required="propIsRequired"
                :type="inputTypeForPassword"
                :id="propElementId"
                v-model="input_value"
                class="w-full h-10 p-2 pr-11 bg-theme-light border-2 border-theme-medium-gray shade-border-when-hover focus:border-theme-black rounded-lg"
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
        <p class="px-2">Password help?</p>
    </div>
</template>


<script setup lang="ts">

    import VInputLabel from './VInputLabel.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return {
                input_value: '',
                current_length: 0,
                show_password: false,
                
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
            propHasTextCounter: Boolean,
            propHasStatusText: Boolean,
            propIsOk: Boolean,
            propIsWarning: Boolean,
            propIsError: Boolean,
        },
        emits: ['hasNewValue'],
        watch: {
            input_value(new_value){

                this.input_value = new_value;
                this.current_length = new_value.length;

                //validate
                this.validateNewPassword();

                this.$emit('hasNewValue', this.input_value);
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
            validateNewPassword() : void {

                let passed_count = 0;
                this.is_success = false;
                this.is_warning = false;
                this.is_error = false;

                //length
                if(this.input_value.length < 8){

                    this.status_text = "Password must have a minimum of 8 characters.";
                    this.is_error = true;
                    return;
                }

                //has >= 1 uppercase
                if(/(?=.*[A-Z])/.test(this.input_value) === true){

                    passed_count += 1;
                }

                //has >= 1 number
                if(/(?=.*[0-9])/.test(this.input_value) === true){

                    passed_count += 1;
                }

                //has >= 1 non-letter and non-number (space, etc.)
                if(/([^0-9a-zA-Z])/.test(this.input_value) === true){

                    passed_count += 1;
                }

                //very strong requires >= 14
                if(this.input_value.length >= 14){

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
            },
            togglePasswordShow() : void {

                this.show_password = !this.show_password;
            }

        },
        components: {
            VInputLabel,
        }
    });
</script>