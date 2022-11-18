<template>
    <div class="text-left">
        <div>
            <VInputLabel :for="propElementId">{{propLabel}}</VInputLabel>
            <div v-if="propHasTextCounter" class="float-right pr-0.5">
                <VInputLabel><!--for text baseline alignment--></VInputLabel>
                <span class="w-fit text-base">{{current_length}}/{{propMaxLength}}</span>
            </div>
        </div>
        <div class="text-xl">
            <input
                :required="propIsRequired"
                type="text"
                :id="propElementId"
                v-model="input_value"
                class="w-full h-10 p-2 pr-10 bg-theme-light border-2 border-theme-black rounded-lg
                    focus:outline-double focus:outline-theme-black focus:outline-2
                "
                :placeholder="propPlaceholder"
                autocomplete="off"
                :maxlength="propMaxLength"
            >
            <i v-if="propIsOk" class="w-0 h-0 fas fa-check relative py-2 right-7 text-theme-ok"></i>
            <i v-if="propIsWarning" class="w-0 h-0 fas fa-triangle-exclamation relative py-2 right-7 text-theme-warning"></i>
            <i v-if="propIsError" class="w-0 h-0 fas fa-exclamation relative py-2 right-6 text-theme-danger"></i>
        </div>
        <div v-show="propHasStatusText" class="h-5 text-base px-2">
            <span v-if="propIsOk" class="text-theme-ok">{{propStatusText}}</span>
            <span v-if="propIsWarning" class="text-theme-warning">{{propStatusText}}</span>
            <span v-if="propIsError" class="text-theme-danger">{{propStatusText}}</span>
            <span v-if="propIsRequired && !propIsOk && !propIsWarning && !propIsError" class="text-theme-danger">required</span>
        </div>
    </div>
</template>


<script setup>

    import VInputLabel from './VInputLabel.vue';
</script>

<script>
    export default {
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

                this.input_value = new_value;
                this.current_length = new_value.length;
                this.$emit('hasNewValue', this.input_value);
            },
        },
        components: {
            VInputLabel,
        }
    };
</script>