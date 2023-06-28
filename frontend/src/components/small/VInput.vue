<template>
    <div class="text-left">
        <div class="w-full grid grid-cols-4">
            <VInputLabel
                :for="propElementId"
                class="col-span-3 w-fit"
            >
                {{propLabel}}
            </VInputLabel>
            <VInputLabel
                v-if="propHasTextCounter"
                :for="propElementId"
                class="col-span-1 w-full text-right"
            >
                {{current_length}}/{{propMaxLength}}
            </VInputLabel>
        </div>
        <div class="text-lg">
            <input
                ref="v_input_field"
                :required="propIsRequired"
                :type="propType"
                :id="propElementId"
                :placeholder="propPlaceholder"
                :name="propName"
                :autocomplete="propAutocomplete"
                spellcheck="false"
                :maxlength="propMaxLength"
                :class="[
                    propHasStatusText ? 'pr-10' : '',
                    'w-full h-10 p-2 bg-theme-light border-2 border-theme-medium-gray shade-border-when-hover focus:border-theme-black rounded-lg'
                ]"
            >
            <i v-show="propIsOk" class="w-0 h-0 fas fa-check relative py-2 right-8 text-theme-toast-success"></i>
            <i v-show="propIsWarning" class="w-0 h-0 fas fa-triangle-exclamation relative py-2 right-9 text-theme-toast-warning"></i>
            <i v-show="propIsError" class="w-0 h-0 fas fa-exclamation relative py-2 right-6 text-theme-toast-danger"></i>
        </div>
        <div v-show="propHasStatusText" class="h-6 text-base px-2">
            <span v-show="propIsOk" class="text-theme-toast-success">{{propStatusText}}</span>
            <span v-show="propIsWarning" class="text-theme-toast-warning-2">{{propStatusText}}</span>
            <span v-show="propIsError" class="text-theme-toast-danger">{{propStatusText}}</span>
        </div>
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
            };
        },
        props: {
            propIsRequired: Boolean,
            propElementId: String,
            propLabel: String,
            propPlaceholder: {
                type: String,
                default: ''
            },
            propMaxLength: {
                type: Number,
                required: true
            },
            propHasTextCounter: Boolean,
            propHasStatusText: Boolean,
            propIsOk: Boolean,
            propIsWarning: Boolean,
            propIsError: Boolean,
            propStatusText: String,
            propAllowWhitespace: {
                type: Boolean,
                default: true
            },
            propType: {
                type: String,
                default: 'text'
            },
            propAutocomplete: {
                type: String,
                default: 'off'
            },
            propName: {     //you need name="email" and autocomplete="on" for drop-down menu of emails
                type: String,
                default: ''
            },
        },
        emits: ['hasNewValue'],
        methods: {
            validateInputWithRegex(new_value:string, input_field:HTMLInputElement) : void {

                if(this.propAllowWhitespace === false && /\s+/g.test(new_value) === true){

                    //user inserts whitespace, set input_field value to be of last regex success string
                    input_field.value = this.input_value;
                    return;
                }

                this.current_length = input_field.value.length;
                this.$emit('hasNewValue', input_field.value);
                this.input_value = input_field.value;
            },
        },
        mounted(){

            const input_field = this.$refs.v_input_field as HTMLInputElement;

            //we need input listener to validate before the input actually shows up
            //using watcher will not be as capable as this
            input_field.addEventListener("input", (e) => {
                e.stopPropagation();
                const new_value = (e as InputEvent).data === null ? '' : (e as InputEvent).data!;
                this.validateInputWithRegex(new_value, input_field as HTMLInputElement);
            });
        },
        beforeUnmount(){

            const input_field = this.$refs.v_input_field as HTMLInputElement;

            input_field.removeEventListener("input", (e) => {
                e.stopPropagation();
                const new_value = (e as InputEvent).data === null ? '' : (e as InputEvent).data!;
                this.validateInputWithRegex(new_value, input_field as HTMLInputElement);
            });
        }
    });
</script>