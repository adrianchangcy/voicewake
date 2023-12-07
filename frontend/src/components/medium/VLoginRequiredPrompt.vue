<template>
    <div class="">

        <div class="relative h-10">
            <VActionText
                @click="emitForceClose()"
                prop-element="button"
                type="button"
                prop-element-size="s"
                prop-font-size="s"
                :prop-is-icon-only="true"
                class="absolute w-10 -right-4"
            >
                <FontAwesomeIcon icon="fas fa-xmark" class="mx-auto"/>
            </VActionText>
        </div>

        <div class="pt-4 flex flex-col gap-1">
            <VTitle propFontSize="l" class="text-center">
                <template #titleDescription>
                    <span>{{ propPromptText }}</span>
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
    import VActionText from '../small/VActionText.vue';
    import VActionSpecial from '../small/VActionSpecial.vue';
    import VTitle from '../small/VTitle.vue';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faXmark } from '@fortawesome/free-solid-svg-icons/faXmark';

    library.add(faXmark);
</script>

<script lang="ts">
    //we don't keep VAudioClipToneMenu in this component due to the inflexibility of button size =/= menu size
    import { defineComponent, PropType } from 'vue';
    import AudioClipToneTypes from '@/types/AudioClipTones.interface';

    export default defineComponent({
        data(){
            return{
            };
        },
        emits: ['forceClose'],
        props: {
            propLabel: String,
            propAudioClipToneChoice: {
                type: Object as PropType<AudioClipToneTypes> | null,
                default: null,
            },
            propIsOpen: {
                type: Boolean,
                default: false
            },
            propPromptText: {
                type: String,
                default: ""
            },
        },
        computed: {

        },
        watch: {

        },
        methods: {
            emitForceClose() : void {
                this.$emit('forceClose', true);
            },
        },
    });
</script>