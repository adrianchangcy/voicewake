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
        <div class="text-xl">
            <!--default inline-block, changed to block to remove bottom spacing-->
            <textarea
                @click.stop="emitWasInteracted()"
                @input="resize()"
                ref="nice_textarea"
                :required="propIsRequired"
                :id="propElementId"
                v-model="input_value"
                :class="[
                    (propIsOk ? 'border-theme-ok' : ''),
                    (propIsWarning ? 'border-theme-warning' : ''),
                    (propIsError ? 'border-theme-danger' : ''),
                    'block w-full h-10 bg-theme-light border-2 focus:border-theme-black border-theme-medium-gray shade-border-when-hover rounded-lg overflow-hidden p-2 pt-1     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-theme-black'
                ]"
                :placeholder="propPlaceholder"
                autocomplete="off"
                :maxlength="propMaxLength"
                title=""
            ></textarea>
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
        components: {
            VInputLabel,
        },
        methods: {
            emitWasInteracted(){

                this.$emit('wasInteracted', true);
            },
            resize(){

                const textarea = this.$refs.nice_textarea;

                //need 0 to make it snappy
                textarea.style.height = '0px';

                //must get scrollHeight after height 0
                textarea.style.height = textarea.scrollHeight.toString() + 'px';
            },
        },
    });
</script>