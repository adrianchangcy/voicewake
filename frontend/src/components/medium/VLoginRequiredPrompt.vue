<template>
    <div class="">

        <div class="relative h-10">
            <VActionTextOnly
                @click="emitIsOpen()"
                prop-element="button"
                type="button"
                prop-element-size="s"
                prop-font-size="s"
                :prop-is-icon-only="true"
                class="absolute w-10 -right-4"
            >
                <i class="fas fa-xmark mx-auto"></i>
            </VActionTextOnly>
        </div>

        <div class="pt-4 flex flex-col gap-1">
            <VTitle propFontSize="l" class="text-center">
                <template #titleDescription>
                    <span>Log in to perform that action.</span>
                </template>
            </VTitle>
            <VAction
                prop-element="a"
                href="login"
                prop-element-size="s"
                prop-font-size="s"
                :prop-is-icon-only="false"
                class="w-full"
            >
                <div class="w-full h-full flex items-center">
                    <span class="mx-auto">Log in</span>
                </div>
            </VAction>
        </div>

        <div class="flex flex-col gap-1 text-center pt-6">
            <span>Don't have an account?</span>
            <VActionSpecial
                prop-element="a"
                href="signup"
                prop-element-size="s"
                prop-font-size="s"
                :prop-is-icon-only="false"
                class="w-full"
            >
                <div class="w-full h-full flex items-center">
                    <span class="mx-auto">Sign up</span>
                </div>
            </VActionSpecial>
        </div>
    </div>
</template>

<script setup lang="ts">
    import VAction from '../small/VAction.vue';
    import VActionTextOnly from '../small/VActionTextOnly.vue';
    import VActionSpecial from '../small/VActionSpecial.vue';
    import VTitle from '../small/VTitle.vue';
</script>

<script lang="ts">
    //we don't keep VEventToneMenu in this component due to the inflexibility of button size =/= menu size
    import { defineComponent, PropType } from 'vue';
    import EventToneTypes from '@/types/EventTones.interface';

    export default defineComponent({
        data(){
            return{
            };
        },
        emits: ['isOpen'],
        props: {
            propLabel: String,
            propEventToneChoice: {
                type: Object as PropType<EventToneTypes> | null,
                default: null,
            },
            propIsOpen: {
                type: Boolean,
                default: false
            },
        },
        computed: {

        },
        watch: {

        },
        methods: {
            emitIsOpen() : void {
                this.$emit('isOpen', false);
            },
        },
    });
</script>