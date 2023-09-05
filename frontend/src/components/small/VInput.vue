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
                :inputmode="propInputmode"
                :id="propElementId"
                :placeholder="propPlaceholder"
                :name="propName"
                :autocomplete="propAutocomplete"
                spellcheck="false"
                :maxlength="propMaxLength"
                :class="[
                    propHasStatusText ? 'pr-10' : '',
                    'w-full h-10 p-2 bg-theme-light border-2 focus:border-theme-black border-theme-medium-gray shade-border-when-hover rounded-lg transition-colors'
                ]"
            >
            <i v-show="propIsOk" class="w-0 h-0 fas fa-check relative py-2 right-8 text-theme-toast-success"></i>
            <i v-show="propIsWarning" class="w-0 h-0 fas fa-triangle-exclamation relative py-2 right-9 text-theme-toast-warning"></i>
            <i v-show="propIsError" class="w-0 h-0 fas fa-exclamation relative py-2 right-6 text-theme-toast-danger"></i>
        </div>
        <div v-show="propHasStatusText" class="h-6 text-base pl-2">
            <span v-show="propIsOk" class="text-theme-toast-success">{{ propStatusText }}</span>
            <span v-show="propIsWarning" class="text-theme-toast-warning-2">{{ propStatusText }}</span>
            <span v-show="propIsError" class="text-theme-toast-danger">{{ propStatusText }}</span>
            <span v-show="hasPlainStatusText" class="text-theme-black">{{ propStatusText }}</span>
        </div>
    </div>
</template>


<script setup lang="ts">

    import VInputLabel from './VInputLabel.vue';
</script>

<script lang="ts">
    import { defineComponent, HTMLAttributes, InputHTMLAttributes, PropType } from 'vue';

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
                type: Number as PropType<InputHTMLAttributes["maxlength"]>,
                required: true
            },
            propHasTextCounter: Boolean,
            propHasStatusText: Boolean,
            propIsOk: Boolean,
            propIsWarning: Boolean,
            propIsError: Boolean,
            propStatusText: {
                type: String,
                default: ""
            },
            propAllowWhitespace: {
                type: Boolean,
                default: true
            },
            propType: {
                type: String as PropType<InputHTMLAttributes["type"]>,
                default: 'text'
            },
            propInputmode: {
                type: String as PropType<HTMLAttributes["inputmode"]>,
                default: 'text'
            },
            propAutocomplete: {
                type: String as PropType<InputHTMLAttributes["autocomplete"]>,
                default: 'off'
            },
            propName: {     //you need name="email" and autocomplete="on" for drop-down menu of emails
                type: String as PropType<InputHTMLAttributes["name"]>,
                default: ''
            },
        },
        emits: ['hasNewValue'],
        computed: {

            hasPlainStatusText() : boolean {

                return this.propIsOk === false &&
                    this.propIsWarning === false &&
                    this.propIsError === false &&
                    this.propStatusText.length > 0
                ;
            },
        },
        methods: {
            handleNewInput(event:InputEvent|null, input_field:HTMLInputElement) : void {

                //we only run on manual input having whitespace, instead of entire input_field.value
                //because we don't want to block pasted values
                //this is to avoid the case of "99% valid paste input but has a space"
                //you should have another bigger-picture validator at the parent component

                //input event triggers on value change, including paste and voice-to-speech
                //hence, we can be rest assured that the emit always fires

                if(event === null){

                    this.current_length = input_field.value.length;
                    this.$emit('hasNewValue', input_field.value);
                    this.input_value = input_field.value;

                    return;
                }

                //event.data gives undefined on auto-complete
                const new_value = event.data === null || event.data === undefined ? '' : event.data!;

                //fine-tune caret behaviour
                if(this.propAllowWhitespace === false && /\s+/g.test(new_value) === true){

                    //get caret position
                    //since event.target is only a reference, any value change will change .selectionStart value immediately after
                    const current_caret_position = input_field.selectionStart as number - 1;

                    //user inserts whitespace, set input_field value to be of last regex success string
                    input_field.value = this.input_value;

                    //set caret position to the one before the value change
                    input_field.setSelectionRange(
                        current_caret_position,
                        current_caret_position
                    );

                    //stop here
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
                this.handleNewInput(e as InputEvent, input_field as HTMLInputElement);
            });

            //since browser saves copy of page on close, it will autocomplete on page reopen
            //we can reliably get autocompleted values via window.onload = (event)=>{}
            window.onload = ()=>{

                //update Vue from autocompleted value
                if(typeof input_field.value === 'string' && input_field.value.length > 0){

                    this.handleNewInput(null, input_field);
                }
            };
        },
        beforeUnmount(){

            const input_field = this.$refs.v_input_field as HTMLInputElement;

            input_field.removeEventListener("input", (e) => {
                e.stopPropagation();
                this.handleNewInput(e as InputEvent, input_field as HTMLInputElement);
            });
        }
    });
</script>