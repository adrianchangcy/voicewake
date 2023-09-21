<template>
    <div class="">

        <div class="flex flex-col gap-1">
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
                is_open: false,
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
            propIsOpen(new_value:boolean) : void {
                this.is_open = new_value;
            },
        },
        methods: {
            toggleMenu() : void {
                //this dictates whether VEventToneMenu is open
                this.is_open = !this.is_open;
                
            },
            emitIsOpen() : void {
                this.$emit('isOpen', this.is_open);
            }
        },
    });
</script>