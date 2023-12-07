<template>
    <div class="text-center">
        <div ref="audio_clip_tone_choice_label" class="w-fit h-fit">
            <VInputLabel for="audio-clip-tone-picker">{{propLabelText}}</VInputLabel>
        </div>
        <div>
            <div ref="audio_clip_tone_choice_opener">
                <button
                    id="audio-clip-tone-picker"
                    aria-label="select an emotion"
                    @click.prevent="toggleAudioClipTonePicker()"
                    class="w-full h-20 relative pb-3 border-2 rounded-lg border-theme-gray-4 text-3xl text-theme-black"
                    type="button"
                >
                    <i
                        v-if="audio_clip_tone_choice === null"
                        class="far fa-face-meh-blank absolute w-fit h-fit left-0 right-0 top-0 bottom-0 m-auto"
                    ></i>
                    <span
                        v-else
                        :aria-label="'Current choice is '+audio_clip_tone_choice.audio_clip_tone_name"
                        class="absolute w-fit h-fit left-0 right-0 top-0 bottom-0 m-auto"
                    >
                        {{audio_clip_tone_choice.audio_clip_tone_symbol}}
                    </span>
                </button>
            </div>
            <div class="relative w-full">
                <TransitionFade>
                    <VBox
                        v-show="is_audio_clip_tone_picker_open"
                        v-click-outside="{
                            bool_status_variable_or_callback: 'is_audio_clip_tone_picker_open',
                            refs_to_exclude: ['audio_clip_tone_choice_label', 'audio_clip_tone_choice_opener']
                        }"
                        class="top-2 p-2 absolute z-10 w-full left-0 right-0 mx-auto"
                    >
                        <VInputLabel>Pick one!</VInputLabel>
                        <div class="h-40 box-content has-emoji overflow-x-hidden overflow-y-auto text-2xl">
                            <div class="items-center place-items-center grid grid-flow-row grid-cols-4">
                                <div
                                    class="col-span-1"
                                    v-for="audio_clip_tone in audio_clip_tones" :key="audio_clip_tone.id"
                                >
                                    <button
                                        @click.prevent="handleAudioClipToneSelected(audio_clip_tone)"
                                        :aria-label="audio_clip_tone.audio_clip_tone_name"
                                        :disabled="!is_audio_clip_tone_picker_open"
                                        class="w-10 h-10 shade-when-hover rounded-md transition-colors duration-100 ease-in-out"
                                        type="button"
                                    >
                                        {{audio_clip_tone.audio_clip_tone_symbol}}
                                    </button>

                                </div>
                            </div>
                        </div>
                    </VBox>
                </TransitionFade>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    import TransitionFade from '/src/transitions/TransitionFade.vue';
    import VInputLabel from '/src/components/small/VInputLabel.vue';
    import VBox from '/src/components/small/VBox.vue';
</script>

<script lang="ts">
    //this depends on main.js clickOutside custom directive
    import { defineComponent } from 'vue';
    import AudioClipToneTypes from '@/types/AudioClipTones.interface';
    import axios from 'axios';

    export default defineComponent({
        data(){
            return{
                audio_clip_tones: null as AudioClipToneTypes[] | null,
                audio_clip_tone_choice: null as AudioClipToneTypes | null,
                is_audio_clip_tone_picker_open: false,
            };
        },
        props: {
            propLabelText: String,
        },
        computed: {
        },
        watch: {
        },
        methods: {
            async getAudioClipTonesData() : Promise<void> {

                await axios.get(window.location.origin + '/api/audio-clips/tones')
                .then((result:any) => {
                    this.audio_clip_tones = result.data['data'];
                })
                .catch((error:any) => {
                    console.log(error);
                });
            },
            toggleAudioClipTonePicker(){

                this.is_audio_clip_tone_picker_open = !this.is_audio_clip_tone_picker_open;
            },
            handleAudioClipToneSelected(audio_clip_tone_choice:AudioClipToneTypes) : void {

                this.toggleAudioClipTonePicker();
                this.audio_clip_tone_choice = audio_clip_tone_choice;
                this.$emit('audioClipToneSelected', this.audio_clip_tone_choice);
            },
        },
        mounted(){

            this.getAudioClipTonesData();
        },
    });
</script>