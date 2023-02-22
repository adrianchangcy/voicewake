<template>
    <div
        v-show="is_open"
        class="p-4 w-full h-fit bg-theme-light"
    >
        <div class="h-40 box-content emojis-container overflow-x-hidden overflow-y-scroll text-2xl">
            <div class="items-center place-items-center grid grid-flow-row grid-cols-4">
                <div
                    class="col-span-1"
                    v-for="event_tone in event_tones" :key="event_tone.id"
                >
                    <button
                        @click.prevent="handleEventToneSelected(event_tone)"
                        :aria-label="event_tone.event_tone_name"
                        :disabled="!is_open"
                        class="w-10 h-10 shade-when-hover rounded-md transition-colors duration-100 ease-in-out"
                        type="button"
                    >
                        {{event_tone.event_tone_symbol}}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
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
                is_open: false,
            };
        },
        computed: {
        },
        props: {
            propIsOpen: {
                type: Boolean,
                default: false
            },
        },
        watch: {
            propIsOpen(new_value){

                this.is_open = new_value;
            },
        },
        methods: {
            async getEventTonesData(){

                await axios.get('http://127.0.0.1:8000/api/event-tones')
                .then((results) => {
                    this.event_tones = results.data;
                });
            },
            handleEventToneSelected(event_tone_choice:EventToneTypes) : void {

                this.is_open = false;
                this.$emit('eventToneSelected', event_tone_choice);
            },
        },
        async mounted(){

            await this.getEventTonesData();
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