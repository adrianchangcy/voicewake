<template>
    <div class="text-left text-lg">
        <label :for="propElementId" class="text-xl">{{propLabel}}</label>
        <div v-if="propHasTextCounter" class="float-right">
            <span><!--for text baseline alignment--></span>
            <span class="w-fit text-sm">{{current_length}}/{{propMaxLength}}</span>
        </div>
    </div>
    <div class="text-left text-lg">
        <input
            :required="propIsRequired"
            type="text"
            :id="propElementId"
            v-model="input_value"
            class="w-full h-10 p-2 pr-10 bg-theme-light rounded-lg border-2 border-theme-black"
            :placeholder="propPlaceholder"
            autocomplete="off"
            :maxlength="propMaxLength"
        >
        <i v-if="propIsOk" class="w-0 h-0 fas fa-check relative py-2 right-7 text-theme-ok"></i>
        <i v-if="propIsWarning" class="w-0 h-0 fas fa-triangle-exclamation relative py-2 right-7 text-theme-warning"></i>
        <i v-if="propIsError" class="w-0 h-0 fas fa-exclamation relative py-2 right-7 text-theme-danger"></i>
    </div>
    <div class="h-2 text-sm">
        <span v-if="propIsOk" class="text-theme-ok">{{propStatusText}}</span>
        <span v-if="propIsWarning" class="text-theme-warning">{{propStatusText}}</span>
        <span v-if="propIsError" class="text-theme-danger">{{propStatusText}}</span>
    </div>
</template>


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
            propStatusText: String,
            propIsOk: Boolean,
            propIsWarning: Boolean,
            propIsError: Boolean,
        },
        emits: ['hasNewValue'],
        watch: {
            input_value(new_value){
                this.current_length = new_value.length;
                this.$emit('hasNewValue', this.input_value);
            },
            propStatusText(new_value){
                this.status_text = new_value;
            },
            propIsOk(new_value){
                this.is_ok = new_value;
            },
            propIsWarning(new_value){
                this.is_warning = new_value;
            },
            propIsError(new_value){
                this.is_error = new_value;
            },
        },
    };
</script>