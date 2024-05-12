<template>
    <!--don't add extra border here like we used to, else it'll go out of sync with VRecorderMenu's height-->
    <div
        class="w-full h-fit"
    >
        <!--py-1 allows us to match VRecorderMenu.vue's size via its elements' border-->
        <div class="h-40 p-1 box-content overflow-x-hidden text-2xl overflow-y-scroll">

            <!--loading-->
            <!--relative fixes the problem where the child buttons overall overflow beyond <html>, causing whitespace-->
            <div
                v-if="is_loading === true"
                class="items-center place-items-center grid grid-flow-row grid-cols-4 relative"
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
                    :prop-has-auto-space-logo="false"
                    :prop-has-auto-space-title="false"
                    :prop-has-auto-space-content="false"
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
            <!--better to not have y-axis gap, otherwise scrolling the gap scrolls main body-->
            <!--use is-above-button and is-inner-button to know where to traverse for <button>, which has :data-index-->
            <div
                v-else-if="hasAudioClipTones === true"
                @click="handleAudioClipToneSelected($event)"
                class="is-audio-clip-tone-button-container   items-center place-items-center grid grid-flow-row grid-cols-4 relative"
            >
                <!--this is for deselect-->
                <div
                    v-if="propHasDeselectOption === true"
                    class="is-outer-audio-clip-tone-button  col-span-1"
                >
                    <!--must be "" else attribute wouldn't exist-->
                    <button
                        data-audio-clip-tone-index=""
                        type="button"
                        :class="[
                            isSelected(null) === true ? 'bg-theme-black text-theme-light dark:bg-dark-theme-white-2 dark:text-dark-theme-black-1' : 'action-hover active:bg-theme-gray-3 dark:active:bg-dark-theme-gray-3',
                            'is-audio-clip-tone-button      w-10 h-10 flex items-center border-2 border-transparent rounded-md transition-colors   focus:outline-none focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-theme-outline dark:focus-visible:outline-dark-theme-outline'
                        ]"
                    >
                        <span class="is-inner-audio-clip-tone-button   w-fit text-sm font-medium mx-auto">Any</span>
                    </button>
                </div>

                <!--tones-->
                <div
                    v-for="(audio_clip_tone, index) in audio_clip_tones" :key="audio_clip_tone.id"
                    class="is-outer-audio-clip-tone-button     col-span-1"
                >
                    <button
                        :data-audio-clip-tone-index="index"
                        type="button"
                        :class="[
                            isSelected(index) === true ? 'bg-theme-black text-theme-light dark:bg-dark-theme-white-2 dark:text-dark-theme-black-1' : 'action-hover active:bg-theme-gray-3 dark:active:bg-dark-theme-gray-3',
                            'is-audio-clip-tone-button      w-10 h-10 border-2 border-transparent rounded-md transition-colors   focus:outline-none focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-theme-outline dark:focus-visible:outline-dark-theme-outline'
                        ]"
                    >
                        <span class="is-inner-audio-clip-tone-button    has-emoji" aria-hidden="true">{{audio_clip_tone.audio_clip_tone_symbol}}</span>
                        <span class="is-inner-audio-clip-tone-button    sr-only">{{audio_clip_tone.audio_clip_tone_name}}</span>
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
            'audioClipToneSelected',
        ],
        methods: {
            async getAudioClipTonesData(){

                this.is_loading = true;

                await axios.get(window.location.origin + '/api/audio-clips/tones/list')
                .then((result:any) => {

                    this.audio_clip_tones = result.data['data'];
                    this.is_loading = false;

                }).catch(() => {

                    this.is_loading = false;
                    this.has_error = true;
                });
            },
            isSelected(audio_clip_tone_index:number|null) : boolean {

                if(this.propMustTrackSelectedOption === false){

                    return false;
                }

                return this.selected_audio_clip_tone_index === audio_clip_tone_index;
            },
            emitAudioClipToneSelected(passed_attribute:string|null) : void {

                let target_attribute = null;

                if(passed_attribute === "" || passed_attribute === null){

                    target_attribute = null;

                }else{

                    target_attribute = passed_attribute;
                }

                //do nothing if no change

                if(
                    (target_attribute === null && this.selected_audio_clip_tone_index === null) ||
                    (target_attribute !== null && this.selected_audio_clip_tone_index === Number(target_attribute))
                ){

                    return;
                }

                //has change

                if(target_attribute === null){

                    this.selected_audio_clip_tone_index = null;

                }else{

                    this.selected_audio_clip_tone_index = Number(target_attribute);
                }

                this.$emit(
                    'audioClipToneSelected',
                    target_attribute === null ? null : this.audio_clip_tones![Number(target_attribute)]
                );
            },
            handleAudioClipToneSelected(event:MouseEvent) : void {

                const current_element = event.target as HTMLElement;

                if(current_element.hasAttribute('data-audio-clip-tone-index') === true){

                    //element is target button

                    const target_attribute = current_element.getAttribute('data-audio-clip-tone-index');

                    this.emitAudioClipToneSelected(target_attribute);

                }else if(current_element.classList.contains('is-audio-clip-tone-button-container') === true){

                    //since this is just the full container that holds the actual smaller button, we ignore

                    return;

                }else if(current_element.classList.contains('is-outer-audio-clip-tone-button') === true){

                    //element is outside button, i.e. ancestor
                    //use querySelector to get nearest child that has our index, i.e. our button

                    const target_element = current_element.querySelector('.is-audio-clip-tone-button');

                    if(target_element === null){

                        throw new Error('Could not find target button from the "outside".');
                    }

                    const target_attribute = target_element.getAttribute('data-audio-clip-tone-index');

                    this.emitAudioClipToneSelected(target_attribute);

                }else if(current_element.classList.contains('is-inner-audio-clip-tone-button') === true){

                    //element is inside button, i.e. child
                    //use .closest() to get nearest ancestor

                    const target_element = current_element.closest('.is-audio-clip-tone-button');

                    if(target_element === null){

                        throw new Error('Could not find target button from the "inside".');
                    }

                    const target_attribute = target_element.getAttribute('data-audio-clip-tone-index');

                    this.emitAudioClipToneSelected(target_attribute);

                }else{

                    throw new Error('Element is not properly integrated with the classes.');
                }
            },
        },
        beforeMount(){

            this.is_open = this.propIsOpen;

            this.getAudioClipTonesData().then(()=>{

                //find index if we have preselected audio_clip_tone
                if(this.propInitialAudioClipTone !== null){

                    const audio_clip_tone_index = this.audio_clip_tones.findIndex((element:AudioClipTonesTypes)=>{

                        return element.id === this.propInitialAudioClipTone!.id;
                    });

                    if(audio_clip_tone_index !== -1){

                        this.selected_audio_clip_tone_index = audio_clip_tone_index;
                    }
                }
            });
        },
    });
</script>