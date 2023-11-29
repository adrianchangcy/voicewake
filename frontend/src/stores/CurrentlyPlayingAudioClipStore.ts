import { defineStore } from 'pinia';
import AudioClipsTypes from '@/types/AudioClips.interface';
import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';

export const useCurrentlyPlayingAudioClipStore = defineStore('currently_playing_audio_clip_store', {
    state: ()=>({
        playing_audio_clip: null as AudioClipsTypes|AudioClipsAndLikeDetailsTypes|null,
    }),
    getters: {
        getPlayingAudioClip: (state)=>{

            return state.playing_audio_clip;
        },
    },
    actions: {
    },
    persist: false
});