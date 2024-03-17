<template>
    <div class="text-left">
        <div class="w-full grid grid-cols-4">
            <VInputLabel
                class="col-span-3"
                :for="propElementId"
            >
                {{propLabel}}
            </VInputLabel>
            <div
                v-if="propHasTextCounter"
                class="col-span-1 relative"
            >
                <span class="absolute w-fit h-fit block text-base font-medium py-1 right-0 bottom-0 m-auto">
                    {{current_length}}/{{propMaxLength}}
                </span>
            </div>
        </div>
        <div class="text-lg">
            <!--default inline-block, changed to block to remove bottom spacing-->
            <textarea
                @click.stop="emitWasInteracted()"
                @input="resize()"
                ref="nice_textarea"
                :required="propIsRequired"
                :id="propElementId"
                v-model="input_value"
                :class="[
                    (propIsOk ? 'border-green-700' : 'focus:border-theme-black border-theme-gray-4'),
                    (propIsWarning ? 'border-yellow-700' : 'focus:border-theme-black border-theme-gray-4'),
                    (propIsError ? 'border-red-700' : 'focus:border-theme-black border-theme-gray-4'),
                    'block w-full h-10 bg-theme-light border-2 shade-border-when-hover rounded-lg overflow-hidden p-2 pt-1    focus:outline-none'
                ]"
                :placeholder="propPlaceholder"
                autocomplete="off"
                :maxlength="propMaxLength"
                title=""
            ></textarea>
        </div>
        <div v-show="propHasStatusText" class="h-5 text-base px-2">
            <span
                :class="[
                    (propIsOk ? 'text-green-700' : ''),
                    (propIsWarning ? 'text-yellow-700' : ''),
                    (propIsError || propIsRequired ? 'text-red-700' : ''),
                    ''
                ]"
            >
                <span v-show="propIsRequired">required</span>
                <span v-show="!propIsRequired">{{ propStatusText }}</span>
            </span>
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
            propPlaceholder: String,
            propMaxLength: Number,
            propHasTextCounter: Boolean,
            propHasStatusText: Boolean,
            propIsOk: Boolean,
            propIsWarning: Boolean,
            propIsError: Boolean,
            propStatusText: String,
        },
        emits: ['newValue', 'wasInteracted'],
        watch: {
            input_value(new_value){

                this.input_value = new_value;
                this.current_length = new_value.length;
                this.$emit('newValue', this.input_value);
                this.emitWasInteracted();
                //we do trim() validation outside of here instead
            },
        },
        methods: {
            emitWasInteracted(){

                this.$emit('wasInteracted', true);
            },
            resize(){

                const textarea = this.$refs.nice_textarea as HTMLTextAreaElement;

                //need 0 to make it snappy
                textarea.style.height = '0px';

                //must get scrollHeight after height 0
                textarea.style.height = textarea.scrollHeight.toString() + 'px';
            },
        },
    });
</script>