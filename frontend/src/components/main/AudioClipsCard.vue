<template>
    <div
        :class="[
            propHasBorder === true ? 'px-4 pt-4 pb-14      border border-theme-light-gray rounded-lg' : '',
            'flex flex-col'
        ]"
    >

        <!--audio-clips-->
        <div
            class="flex flex-col gap-8"
        >
            <TransitionGroupFade>
                <div
                    v-for="audio_clip in propAudioClips" :key="audio_clip.id"
                >
                    <VAudioClipCard
                        :propAudioClip="audio_clip"
                        :propIsSelected="checkIsSelected(audio_clip.id)"
                        @isSelected="handleNewSelectedAudioClip($event)"
                    />
                </div>

                <div v-show="propIsFetching" class="flex flex-col gap-8">
                    <div class="w-full h-20 rounded-lg skeleton"></div>
                    <div class="w-full h-20 rounded-lg skeleton"></div>
                </div>
                
            </TransitionGroupFade>
        </div>
    </div>
</template>

<script setup lang="ts">
    import VAudioClipCard from '/src/components/medium/VAudioClipCard.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import AudioClipsTypes from '@/types/AudioClips.interface';
    import { useCurrentlyPlayingAudioClipStore } from '@/stores/CurrentlyPlayingAudioClipStore';

    export default defineComponent({
        data() {
            return {
                currently_playing_audio_clip_store: useCurrentlyPlayingAudioClipStore(),
                selected_audio_clip: null as AudioClipsTypes|null,
                pretty_when_created: '',
            };
        },
        props: {
            propAudioClips: {
                type: Object as PropType<AudioClipsTypes[]>,
                required: true,
            },
            propShowTitle: {
                type: Boolean,
                default: true
            },
            propHasBorder: {
                type: Boolean,
                default: false
            },
            propIsFetching: {
                type: Boolean,
                default: false
            },
        },
        computed: {
        },
        methods: {
            checkIsSelected(audio_clip_id:number) : boolean {

                return this.selected_audio_clip !== null && this.selected_audio_clip.id === audio_clip_id;
            },
            handleNewSelectedAudioClip(audio_clip:AudioClipsTypes) : void {

                this.currently_playing_audio_clip_store.$patch({
                    playing_audio_clip: audio_clip
                });
            },
        },
        mounted(){

            //listen to store
            this.currently_playing_audio_clip_store.$subscribe((mutation, state)=>{

                this.selected_audio_clip = state.playing_audio_clip as AudioClipsTypes|null;
            });
        },
    });
</script>