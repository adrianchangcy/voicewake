<template>
    <div
        v-show="is_open"
        class="p-2 w-full h-fit"
    >
        <div class="h-40 p-1 box-content overflow-x-hidden overflow-y-scroll text-2xl">
            <!--relative fixes the problem where the child buttons overall overflow beyond <html>, causing whitespace-->
            <div
                v-if="event_tones === null"
                class="items-center place-items-center grid grid-flow-row grid-cols-4 relative"
            >
                <span class="sr-only">tags are loading</span>
                <div
                    class="col-span-1 h-10 flex items-center"
                    v-for="x in 30" :key="x"
                >
                    <div class="w-8 h-8 mx-auto rounded-full skeleton">
                    </div>
                </div>
            </div>
            
            <div
                v-else
                class="items-center place-items-center grid grid-flow-row grid-cols-4 relative"
            >
                <div
                    class="col-span-1"
                    v-for="event_tone in event_tones" :key="event_tone.id"
                >
                    <button
                        @click.prevent="handleEventToneSelected(event_tone)"
                        :disabled="!is_open"
                        class="w-10 h-10 pb-0.5 shade-background-when-hover rounded-md transition-colors duration-100 ease-in-out   focus:outline-1 focus-visible:outline-1 focus:outline-theme-accent focus-visible:outline-theme-accent"
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
    import { notify } from 'notiwind';
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
                }).catch((error:any) => {
                    notify({
                        title: "Listing tags failed",
                        text: error.response.data['message'],
                        type: "error"
                    }, 3000);
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