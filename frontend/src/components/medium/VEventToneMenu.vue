<template>
    <div
        v-show="is_open"
        class="p-4 w-full h-fit"
    >
        <div
            :class="[
                hasEventTones === true ? 'overflow-y-scroll' : 'overflow-y-hidden',
                'h-40 p-1 box-content overflow-x-hidden text-2xl'
            ]"
        >

            <!--loading-->
            <!--relative fixes the problem where the child buttons overall overflow beyond <html>, causing whitespace-->
            <div
                v-if="is_loading === true"
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

            <!--could not get tags-->
            <div
                v-else-if="hasEventTones === false || has_error === true"
                class="h-full flex items-center"
            >
                <VDialogPlain
                    :propHasBorder="false"
                    class="mx-auto"
                >
                    <template #title>
                        Oops, unable to load the tags!
                    </template>
                    <template #content>
                        Try refreshing this page.
                    </template>
                </VDialogPlain>
            </div>

            <!--has tags-->
            <div
                v-else-if="hasEventTones === true"
                class="items-center place-items-center grid grid-flow-row grid-cols-4 relative"
            >
                <div
                    class="col-span-1"
                    v-for="event_tone in event_tones" :key="event_tone.id"
                >
                    <button
                        @click.prevent="handleEventToneSelected(event_tone)"
                        :disabled="!is_open"
                        class="w-10 h-10 pb-0.5 border border-transparent shade-border-when-hover rounded-md transition-colors   focus:outline-none focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-theme-outline"
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
    import VDialogPlain from '../small/VDialogPlain.vue';
</script>

<script lang="ts">
    //this depends on main.js clickOutside custom directive
    import { defineComponent } from 'vue';
    import EventTonesTypes from '@/types/EventTones.interface';
    import { notify } from 'notiwind';
    import axios from 'axios';

    export default defineComponent({
        data(){
            return{
                event_tones: null as EventTonesTypes[] | null,
                is_open: false,
                is_loading: false,
                has_error: false,
            };
        },
        computed: {
            hasEventTones() : boolean {

                return this.event_tones !== null && this.event_tones.length > 0;
            },
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

                this.is_loading = true;

                await axios.get(window.location.origin + '/api/event-tones/list')
                .then((results) => {

                    this.event_tones = results.data['data'];
                    this.is_loading = false;

                }).catch(() => {

                    this.is_loading = false;
                    this.has_error = true;

                    notify({
                        title: "Error",
                        text: 'Could not get the tags. Try refreshing the page.',
                        type: "error"
                    }, 5000);
                });
            },
            handleEventToneSelected(event_tone_choice:EventTonesTypes) : void {

                this.is_open = false;
                this.$emit('eventToneSelected', event_tone_choice);
            },
        },
        beforeMount(){

            this.getEventTonesData();
        },
    });
</script>