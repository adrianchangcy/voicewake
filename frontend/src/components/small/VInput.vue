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
        <div class="text-xl">
            <input
                :required="propIsRequired"
                type="text"
                :id="propElementId"
                :placeholder="propPlaceholder"
                autocomplete="off"
                spellcheck="false"
                :maxlength="propMaxLength"
                :class="[
                    propHasStatusText ? 'pr-10' : '',
                    'w-full h-10 p-2 pr-10 bg-theme-light border-2 border-theme-medium-gray shade-border-when-hover focus:border-theme-black rounded-lg'
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
                regexp: null as RegExp|null,
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
            propStatusText: String,
            propRegex: {
                type: String,
                default: ''
            },
        },
        emits: ['hasNewValue'],
        methods: {
            validateInputWithRegex(event:InputEvent, input_field:HTMLInputElement) : void {

                if(this.propRegex !== null && event.data !== null && this.regexp.test(event.data) === true){
                    
                    //undo to previous regex success string
                    input_field.value = this.input_value;
                    return;
                }

                //put this here instead of using watcher, since it clashes
                this.current_length = input_field.value.length;
                this.$emit('hasNewValue', input_field.value);
                this.input_value = input_field.value;
            },
        },
        mounted(){

            if(this.propRegex !== ''){

                this.regexp = new RegExp(this.propRegex, 'm');
            }

            const input_field = document.querySelector("#"+this.propElementId);

            //we need input listener to validate before the input actually shows up
            input_field.addEventListener("input", (e) => {
                    e.stopPropagation();
                    this.validateInputWithRegex(e as InputEvent, input_field as HTMLInputElement);
            });
        },
        beforeUnmount(){

            const input_field = document.querySelector("#"+this.propElementId);
            
            //we need input listener to validate before the input actually shows up
            input_field.removeEventListener("input", (e) => {
                    e.stopPropagation();
                    this.validateInputWithRegex(e as InputEvent, input_field as HTMLInputElement);
            });
        }
    });
</script>