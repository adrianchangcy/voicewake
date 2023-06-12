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
                v-model="input_value"
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


<script setup>

    import VInputLabel from './VInputLabel.vue';
</script>

<script>
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
            propPlaceholder: String,
            propMaxLength: Number,
            propHasTextCounter: Boolean,
            propHasStatusText: Boolean,
            propIsOk: Boolean,
            propIsWarning: Boolean,
            propIsError: Boolean,
            propStatusText: String,
        },
        emits: ['hasNewValue'],
        watch: {
            input_value(new_value){

                this.current_length = new_value.length;
                this.$emit('hasNewValue', this.input_value);
            },
        },
        components: {
            VInputLabel,
        }
    });
</script>