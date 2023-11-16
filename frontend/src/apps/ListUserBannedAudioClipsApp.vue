<template>
    <div>

        <AudioClipsCard
            :prop-audio-clips="audio_clips"
            :prop-is-fetching="is_fetching"
        />

        <TransitionFade>
            <VDialogPlain
                v-show="has_no_audio_clips_left_to_fetch"
                :prop-has-border="false"
                :prop-has-auto-space-logo="false"
                :prop-has-auto-space-title="false"
                :prop-has-auto-space-content="false"
                class="w-full py-8"
            >
                <template #title>
                    <span>You've reached the end of this page.</span>
                </template>
            </VDialogPlain>
        </TransitionFade>

        <div id="load-more-user-banned-audio-clips-observer-target"></div>

        <!--VAudioClipCard emits selection, which triggers :to, thus teleporting-->
        <!--presence of VAudioClipCard depends on VEventCard-->
        <div v-if="selected_audio_clip !== null">
            <Teleport :to="getVPlaybackTeleportId">
                <VPlayback
                    :propAudioClip="selected_audio_clip"
                    :propIsOpen="true"
                    :propAudioVolumePeaks="selected_audio_clip.audio_volume_peaks"
                    :propBucketQuantity="selected_audio_clip.audio_volume_peaks.length"
                    :propAutoPlayOnSourceChange="true"
                />
            </Teleport>
        </div>
    </div>
</template>


<script setup lang="ts">
    import AudioClipsCard from '@/components/main/AudioClipsCard.vue';
    import VPlayback from '@/components/medium/VPlayback.vue';
    import VDialogPlain from '@/components/small/VDialogPlain.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { prettyTimeRemaining } from '@/helper_functions';
    import AudioClipsTypes from '@/types/AudioClips.interface';
    import { useCurrentlyPlayingAudioClipStore } from '@/stores/CurrentlyPlayingAudioClipStore';
    import { notify } from 'notiwind';
    const axios = require('axios');

    export default defineComponent({
        name: 'ListUserBannedAudioClipsApp',
        data(){
            return {
                audio_clips: [] as AudioClipsTypes[],
                currently_playing_audio_clip_store: useCurrentlyPlayingAudioClipStore(),
                selected_audio_clip: null as AudioClipsTypes|null,

                is_fetching: false,
                can_observer_fetch: false,
                has_no_audio_clips_left_to_fetch: false,
                current_page: 1,
            };
        },
        computed: {
            getVPlaybackTeleportId() : string {

                if(this.selected_audio_clip === null){

                    return '';
                }

                return '#playback-teleport-audio-clip-id-' + this.selected_audio_clip.id;
            },
        },
        methods: {
            async getUserBannedAudioClips() : Promise<void> {

                this.is_fetching = true;
                this.can_observer_fetch = false;
                this.has_no_audio_clips_left_to_fetch = false;

                await axios.get(window.location.origin + '/api/users/banned-audio_clips/get/' + this.current_page.toString())
                .then((result:any) => {

                    console.log(result.data['data'].length);

                    result.data['data'].forEach((audio_clip:AudioClipsTypes)=>{

                        this.audio_clips.push(audio_clip);
                    });

                    if(result.data['data'].length > 0){

                        this.current_page += 1;

                    }else{

                        this.has_no_audio_clips_left_to_fetch = true;

                    }

                    this.can_observer_fetch = true;

                }).catch(() => {

                    notify({
                        title: 'Error',
                        text: 'Unable to retrieve your banned recordings.',
                        type: 'error'
                    });

                }).finally(() => {

                    this.is_fetching = false;
                });
            },
            handleNewSelectedAudioClip(audio_clip:AudioClipsTypes|null) : void {

                this.selected_audio_clip = audio_clip;
            },
            setUpObserver() : void {

                //set up observer for infinite scroll
                const observer_target = document.querySelector('#load-more-user-banned-audio-clips-observer-target');

                const observer = new IntersectionObserver(()=>{

                    if(
                        this.can_observer_fetch === false ||
                        this.has_no_audio_clips_left_to_fetch === true
                    ){

                        return;
                    }

                    this.getUserBannedAudioClips();
                }, {
                    threshold: 1,
                });

                if(observer_target !== null){

                    observer.observe(observer_target);
                }
            },
        },
        beforeMount(){

            this.getUserBannedAudioClips();

            //listen to store
            this.currently_playing_audio_clip_store.$subscribe((mutation, state)=>{

                this.handleNewSelectedAudioClip(state.playing_audio_clip as AudioClipsTypes|null);
            });

            //make ban duration pretty
            const container = (document.getElementById('data-container-user-banned-audio_clips') as HTMLElement);

            //change '1 Jan 2023' to '1 century left'
            //we are passing 'YYYY-MM-DD HH:mm:ss' from template
            //for best reliability, Date() expects 'YYYY-MM-DDTHH:mm:ssZ'
            if(container.getElementsByClassName('banned-until').length === 1){

                const banned_until_element = container.getElementsByClassName('banned-until')[0];
                const banned_until = (container.getAttribute('data-banned-until') as string).replace(/ /g, 'T') + 'Z';
                banned_until_element.textContent = 'for ' + prettyTimeRemaining(
                    new Date().getTime(),
                    new Date(banned_until).getTime()
                );
            }

        },
        mounted(){

            this.setUpObserver();
        }
    });
</script>