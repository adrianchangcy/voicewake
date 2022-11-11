<template>
    <div class="text-left">
        <div>
            <label :for="propElementId" class="text-xl">{{propLabel}}</label>
            <div v-if="propHasTextCounter" class="float-right">
                <span><!--for text baseline alignment--></span>
                <span class="w-fit text-sm">{{current_length}}/{{propMaxLength}}</span>
            </div>
        </div>
        <div class="text-lg">
            <textarea
                v-model="input_value"
                :id="propElementId"
                class="w-full h-20 p-2 bg-theme-light rounded-lg border-2 border-theme-idle focus:outline-none focus:ring-1 focus:ring-theme-black focus:border-theme-black"
                :placeholder="propPlaceholder"
                autocomplete="off"
                :maxlength="propMaxLength"
            ></textarea>
        </div>
        <div class="h-5 text-sm px-2"></div>
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
            propElementId: String,
            propLabel: String,
            propPlaceholder: String,
            propMaxLength: Number,
            propHasTextCounter: Boolean,
        },
        emits: ['hasNewValue'],
        watch: {
            input_value(new_value){
                this.current_length = new_value.length;
                this.$emit('hasNewValue', this.input_value);
            },
        },
    };
</script>