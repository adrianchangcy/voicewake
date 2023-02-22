<template>
    <div class="text-center">
        <div ref="event_tone_choice_label" class="w-fit h-fit">
            <VInputLabel for="event-tone-picker">{{propLabelText}}</VInputLabel>
        </div>
        <div>
            <div ref="event_tone_choice_opener">
                <button
                    id="event-tone-picker"
                    aria-label="select an emotion"
                    @click.prevent="toggleEventTonePicker()"
                    class="w-full h-20 relative pb-3 border-2 rounded-lg border-theme-medium-gray text-3xl text-theme-black"
                    type="button"
                >
                    <i
                        v-if="event_tone_choice === null"
                        class="far fa-face-meh-blank absolute w-fit h-fit left-0 right-0 top-0 bottom-0 m-auto"
                    ></i>
                    <span
                        v-else
                        :aria-label="'Current choice is '+event_tone_choice.event_tone_name"
                        class="absolute w-fit h-fit left-0 right-0 top-0 bottom-0 m-auto"
                    >
                        {{event_tone_choice.event_tone_symbol}}
                    </span>
                </button>
            </div>
            <div class="relative w-full">
                <TransitionFade>
                    <VBox
                        v-show="is_event_tone_picker_open"
                        v-click-outside="{
                            var_name_for_element_bool_status: 'is_event_tone_picker_open',
                            refs_to_exclude: ['event_tone_choice_label', 'event_tone_choice_opener']
                        }"
                        class="top-2 p-2 absolute z-10 w-full left-0 right-0 mx-auto"
                    >
                        <VInputLabel>Pick one!</VInputLabel>
                        <div class="h-40 box-content emojis-container overflow-x-hidden overflow-y-auto text-2xl">
                            <div class="items-center place-items-center grid grid-flow-row grid-cols-4">
                                <div
                                    class="col-span-1"
                                    v-for="event_tone in event_tones" :key="event_tone.id"
                                >
                                    <button
                                        @click.prevent="handleEventToneSelected(event_tone)"
                                        :aria-label="event_tone.event_tone_name"
                                        :disabled="!is_event_tone_picker_open"
                                        class="w-10 h-10 shade-when-hover rounded-md transition-colors duration-100 ease-in-out"
                                        type="button"
                                    >
                                        {{event_tone.event_tone_symbol}}
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
    import EventToneTypes from '@/types/EventTones.interface';
    import axios from 'axios';

    export default defineComponent({
        data(){
            return{
                event_tones: null as EventToneTypes[] | null,
                event_tone_choice: null as EventToneTypes | null,
                is_event_tone_picker_open: false,
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
            async getEventTonesData(){

                await axios.get('http://127.0.0.1:8000/api/event-tones')
                .then((results) => {
                    this.event_tones = results.data;
                });
            },
            toggleEventTonePicker(){

                this.is_event_tone_picker_open = !this.is_event_tone_picker_open;
            },
            handleEventToneSelected(event_tone_choice:EventToneTypes) : void {

                this.toggleEventTonePicker();
                this.event_tone_choice = event_tone_choice;
                this.$emit('eventToneSelected', this.event_tone_choice);
            },
        },
        mounted(){

            this.getEventTonesData();
        },
    });
</script>


<style scoped>

    /*
    use these fonts for emojis themselves to ensure proper rendering
    https://github.com/joeattardi/picmo/issues/242
    */
    .emojis-container{
        font-family: "Segoe UI Emoji", "Segoe UI Symbol", "Segoe UI", "Apple Color Emoji", "Twemoji Mozilla",
        "Noto Color Emoji", "EmojiOne Color", "Android Emoji"
    }


</style>