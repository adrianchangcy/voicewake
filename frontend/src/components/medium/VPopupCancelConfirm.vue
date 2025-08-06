<template>
    <div class="px-4 py-8 border border-theme-gray-2 dark:border-dark-theme-gray-2 bg-theme-light dark:bg-theme-dark rounded-lg">

        <div class="flex flex-col">
            <VTitle propFontSize="m" class="text-left">
                <template #title>
                    <span>{{ propTitle }}</span>
                </template>
            </VTitle>
            <VTitle propFontSize="m" class="text-left pt-2">
                <template #titleDescription>
                    <span>{{ propDescription }}</span>
                </template>
            </VTitle>
        </div>

        <div class="pt-4 flex flex-row gap-2">
            <VAction
                @click="doCancel()"
                prop-element="button"
                type="button"
                href="login"
                prop-element-size="s"
                prop-font-size="s"
                class="w-full"
            >
                <div class="w-full h-full flex items-center">
                    <span class="mx-auto">{{ propCancellationTerm }}</span>
                </div>
            </VAction>

            <VActionDanger
                @click="doConfirm()"
                prop-element="button"
                type="button"
                href="signup"
                prop-element-size="s"
                prop-font-size="s"
                class="w-full"
            >
                <div class="w-full h-full flex items-center">
                    <span class="mx-auto">{{ propConfirmationTerm }}</span>
                </div>
            </VActionDanger>
        </div>
    </div>
</template>

<script setup lang="ts">
    import VAction from '@/components/small/VAction.vue';
    import VActionDanger from '@/components/small/VActionDanger.vue';
    import VTitle from '@/components/small/VTitle.vue';
</script>

<script lang="ts">
    //we don't keep VAudioClipToneMenu in this component due to the inflexibility of button size =/= menu size
    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return{
            };
        },
        emits: ['forceClose'],
        props: {
            propTitle: {
                type: String,
                required: true,
            },
            propDescription: {
                type: String,
                required: true,
            },
            propCancellationTerm: {
                type: String,
                required: true,
            },
            propCancellationCallback: {
                type: Function,
                required: true,
            },
            propConfirmationTerm: {
                type: String,
                required: true,
            },
            propConfirmationCallback: {
                type: Function,
                required: true,
            },
        },
        methods: {
            emitForceClose() : void {
                this.$emit('forceClose', true);
            },
            doCancel() : void {

                //must run callback before close, as kwargs are immediately deleted on close
                //also no await for async callback, just close immediately
                this.propCancellationCallback();
                this.emitForceClose();
            },
            doConfirm() : void {

                //must run callback before close, as kwargs are immediately deleted on close
                //also no await for async callback, just close immediately
                this.propConfirmationCallback();
                this.emitForceClose();
            },
        },
    });
</script>