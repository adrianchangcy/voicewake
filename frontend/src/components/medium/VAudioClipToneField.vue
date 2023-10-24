<template>
    <div>
        <VInputLabel for="audio-clip-tone-picker">
            {{propLabel}}
        </VInputLabel>
        <button
            id="audio-clip-tone-picker"
            @click.stop="[toggleMenu(), emitIsOpen()]"
            :class="[
                is_open ? 'border-theme-black      focus-visible:outline-offset-0' : 'border-theme-medium-gray shade-border-when-hover   focus-visible:-outline-offset-2',
                'w-full h-20 relative border-2 rounded-lg text-3xl text-theme-black text-center     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-theme-dark-gray'
            ]"
            type="button"
        >
            <span
                v-if="propAudioClipToneChoice !== null"
                class="absolute w-fit h-fit left-0 right-0 top-0 bottom-0.5 m-auto has-emoji"
            >
                <span aria-hidden="true">{{propAudioClipToneChoice.audio_clip_tone_symbol}}</span>
                <span class="sr-only">{{propAudioClipToneChoice.audio_clip_tone_name}}</span>
            </span>
            <span v-else class="sr-only">No audio tone selected</span>
            <span v-if="propIsOpen" class="sr-only">
                Close audio tone menu
            </span>
            <span v-else class="sr-only">
                Open audio tone menu
            </span>
        </button>
    </div>
</template>

<script setup lang="ts">
    import VInputLabel from '/src/components/small/VInputLabel.vue';
</script>

<script lang="ts">
    //we don't keep VAudioClipToneMenu in this component due to the inflexibility of button size =/= menu size
    import { defineComponent, PropType } from 'vue';
    import AudioClipToneTypes from '@/types/AudioClipTones.interface';

    export default defineComponent({
        data(){
            return{
                is_open: false,
            };
        },
        emits: ['isOpen'],
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
                //this dictates whether VAudioClipToneMenu is open
                this.is_open = !this.is_open;
                
            },
            emitIsOpen() : void {
                this.$emit('isOpen', this.is_open);
            }
        },
    });
</script>