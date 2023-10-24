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
                <span class="sr-only">audio tones are loading</span>
                <div
                    class="col-span-1 w-10 h-10 flex items-center"
                    v-for="x in 24" :key="x"
                >
                    <div class="w-8 h-8 mx-auto rounded-full skeleton">
                    </div>
                </div>
            </div>

            <!--could not get tones-->
            <div
                v-else-if="hasAudioClipTones === false && has_error === true"
                class="h-full flex items-center"
            >
                <VDialogPlain
                    :propHasBorder="false"
                    class="mx-auto"
                >
                    <template #title>
                        Oops, unable to load the audio tones!
                    </template>
                    <template #content>
                        Try refreshing this page.
                    </template>
                </VDialogPlain>
            </div>

            <!--has tones-->
            <div
                v-else-if="hasAudioClipTones === true"
                class="items-center place-items-center grid grid-flow-row grid-cols-4 gap-y-1 relative"
            >
                <!--this is for deselect-->
                <div
                    v-if="propHasDeselectOption === true"
                    class="col-span-1"                    
                >
                    <!--text-black has great contrast for bg-theme-dark-gray, whereas text-theme-black has bad contrast-->
                    <button
                        @click="handleAudioClipToneSelected(null)"
                        type="button"
                        :class="[
                            isSelected(null) === true ? 'bg-theme-dark-gray text-black' : 'text-theme-black',
                            'w-10 h-10 pb-0.5 flex items-center border border-transparent shade-border-when-hover rounded-md transition-colors   focus:outline-none focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-theme-outline'
                        ]"
                    >
                        <span class="text-sm font-medium mx-auto">Any</span>
                    </button>
                </div>

                <!--tones-->
                <div
                    class="col-span-1"
                    v-for="(audio_clip_tone, index) in audio_clip_tones" :key="audio_clip_tone.id"
                >
                    <button
                        @click="handleAudioClipToneSelected(index)"
                        type="button"
                        :class="[
                            isSelected(index) === true ? 'bg-theme-dark-gray' : '',
                            'w-10 h-10 pb-0.5 border border-transparent shade-border-when-hover rounded-md transition-colors   focus:outline-none focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-theme-outline'
                        ]"
                    >
                        <span class="has-emoji" aria-hidden="true">{{audio_clip_tone.audio_clip_tone_symbol}}</span>
                        <span class="sr-only">{{audio_clip_tone.audio_clip_tone_name}}</span>
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
    import { PropType, defineComponent } from 'vue';
    import AudioClipTonesTypes from '@/types/AudioClipTones.interface';
    import { notify } from 'notiwind';
    import axios from 'axios';
    import { useFilteredEventsStore } from '@/stores/FilteredEventsStore';

    export default defineComponent({
        data(){
            return{
                audio_clip_tones: [] as AudioClipTonesTypes[],
                selected_audio_clip_tone_index: null as number|null,
                is_open: false,     //need this for "close after select"
                is_loading: false,
                has_error: false,
            };
        },
        computed: {
            hasAudioClipTones() : boolean {

                return this.audio_clip_tones !== null && this.audio_clip_tones.length > 0;
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
            propInitialAudioClipTone: {
                type: Object as PropType<AudioClipTonesTypes|null>,
                default: null
            },
            propFilteredEventsStore: {
                type: Object as PropType<ReturnType<typeof useFilteredEventsStore>>,
                default: null
            }
        },
        watch: {
            propIsOpen(new_value){

                this.is_open = new_value;
            },
        },
        emits: [
            'audio_clipToneSelected',
        ],
        methods: {
            async getAudioClipTonesData(){

                this.is_loading = true;

                await axios.get(window.location.origin + '/api/audio-clip-tones/list')
                .then((result:any) => {

                    this.audio_clip_tones = result.data['data'];
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
            isSelected(audio_clip_tone_index:number|null) : boolean {

                if(this.propMustTrackSelectedOption === false){

                    return false;
                }

                return this.selected_audio_clip_tone_index === audio_clip_tone_index;
            },
            async handleAudioClipToneSelected(audio_clip_tone_index:number|null) : Promise<void> {

                if(this.propCloseWhenSelected === true){

                    this.is_open = false;
                }

                if(audio_clip_tone_index === this.selected_audio_clip_tone_index){

                    return;
                }

                //update selected index
                this.selected_audio_clip_tone_index = audio_clip_tone_index;

                //emit
                this.$emit(
                    'audio_clipToneSelected',
                    audio_clip_tone_index === null ? null : this.audio_clip_tones![audio_clip_tone_index]
                );
            },
        },
        beforeMount(){

            this.is_open = this.propIsOpen;

            (async ()=>{

                await this.getAudioClipTonesData();

                //find index if we have preselected audio_clip_tone
                if(this.propInitialAudioClipTone !== null){

                    const audio_clip_tone_index = this.audio_clip_tones.findIndex((element:AudioClipTonesTypes)=>{

                        return element.id === this.propInitialAudioClipTone!.id;
                    });

                    if(audio_clip_tone_index !== -1){

                        this.selected_audio_clip_tone_index = audio_clip_tone_index;

                    }else if(this.propFilteredEventsStore !== null && audio_clip_tone_index === -1){

                        //remove data from store if audio_clip_tone no longer exists
                        this.propFilteredEventsStore.destroySelectedAudioClipToneData(this.propInitialAudioClipTone);
                        this.propFilteredEventsStore.updateSelectedAudioClipTone(null);
                    }
                }
            })();
        },
    });
</script>