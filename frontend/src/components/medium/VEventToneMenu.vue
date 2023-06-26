<template>
    <div
        v-show="is_open"
        class="p-3 w-full h-fit"
    >
        <div class="h-40 p-1 box-content overflow-x-hidden overflow-y-scroll text-2xl">
            <div class="items-center place-items-center grid grid-flow-row grid-cols-4">
                <div
                    class="col-span-1"
                    v-for="event_tone in event_tones" :key="event_tone.id"
                >
                    <button
                        @click.prevent="handleEventToneSelected(event_tone)"
                        :disabled="!is_open"
                        class="w-10 h-10 pb-0.5 shade-when-hover rounded-md transition-colors duration-100 ease-in-out"
                        type="button"
                    >
                        <span class="has-emoji">{{event_tone.event_tone_symbol}}</span>
                        <span class="sr-only">{{event_tone.event_tone_name}}</span>
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

                await axios.get(window.location.origin + '/api/event-tones')
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