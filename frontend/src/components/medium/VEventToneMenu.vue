<template>
    <div
        v-show="is_open"
        class="w-full h-fit"
    >
        <!--py-1 allows us to match VRecorderMenu.vue's size via its elements' border-->
        <div class="h-40 p-1 box-content overflow-x-hidden text-2xl overflow-y-scroll">

            <!--loading-->
            <!--relative fixes the problem where the child buttons overall overflow beyond <html>, causing whitespace-->
            <div
                v-if="is_loading === true"
                class="items-center place-items-center grid grid-flow-row grid-cols-4 gap-y-1 relative"
            >
                <span class="sr-only">tags are loading</span>
                <div
                    class="col-span-1 w-10 h-10 flex items-center"
                    v-for="x in 24" :key="x"
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
                class="items-center place-items-center grid grid-flow-row grid-cols-4 gap-y-1 relative"
            >
                <!--this is for deselect-->
                <div
                    v-if="propHasDeselectOption === true"
                    class="col-span-1"                    
                >
                    <!--text-black has great contrast for bg-theme-dark-gray, whereas text-theme-black has bad contrast-->
                    <button
                        @click="handleEventToneSelected(null)"
                        type="button"
                        :class="[
                            isSelected(null) === true ? 'bg-theme-dark-gray text-black' : 'text-theme-black',
                            'w-10 h-10 pb-0.5 flex items-center border border-transparent shade-border-when-hover rounded-md transition-colors   focus:outline-none focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-theme-outline'
                        ]"
                    >
                        <span class="text-sm font-medium mx-auto">Any</span>
                    </button>
                </div>

                <!--tags-->
                <div
                    class="col-span-1"
                    v-for="(event_tone, index) in event_tones" :key="event_tone.id"
                >
                    <button
                        @click="handleEventToneSelected(index)"
                        type="button"
                        :class="[
                            isSelected(index) === true ? 'bg-theme-dark-gray' : '',
                            'w-10 h-10 pb-0.5 border border-transparent shade-border-when-hover rounded-md transition-colors   focus:outline-none focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-theme-outline'
                        ]"
                    >
                        <span class="has-emoji" aria-hidden="true">{{event_tone.event_tone_symbol}}</span>
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
                selected_event_tone_index: null as number|null,
                is_open: false,     //need this for "close after select"
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
            propCloseWhenSelected: {
                type: Boolean,
                default: true
            },
            propHasDeselectOption: {
                type: Boolean,
                default: false
            },
            propMustTrackSelectedOption: {
                type: Boolean,
                default: false
            },
        },
        watch: {
            propIsOpen(new_value){

                this.is_open = new_value;
            },
        },
        emits: [
            'eventToneSelected'
        ],
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
            isSelected(event_tone_index:number|null) : boolean {

                if(this.propMustTrackSelectedOption === false){

                    return false;
                }

                return this.selected_event_tone_index === event_tone_index;
            },
            async handleEventToneSelected(event_tone_index:number|null) : Promise<void> {

                if(this.propCloseWhenSelected === true){

                    this.is_open = false;
                }

                if(event_tone_index === this.selected_event_tone_index){

                    return;
                }

                //update selected index
                this.selected_event_tone_index = event_tone_index;

                //emit
                this.$emit(
                    'eventToneSelected',
                    event_tone_index === null ? null : this.event_tones![event_tone_index]
                );
            },
        },
        beforeMount(){

            this.is_open = this.propIsOpen;

            this.getEventTonesData();
        },
    });
</script>