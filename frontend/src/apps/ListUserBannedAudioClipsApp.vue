<template>
    <div class="border-x-2 border-red-500 px-1">

        <VAudioClipsCard
            :prop-audio-clips="audio_clips"
        />

        <div
            v-show="is_fetching"
            class="flex flex-col gap-4 px-1"
        >
            <div class="w-full h-20 rounded-lg skeleton"></div>
            <div class="w-full h-20 rounded-lg skeleton"></div>
        </div>

        <TransitionFade>
            <VDialogPlain
                v-if="canShowEmptyMessage || canShowEndOfPageMessage"
                :prop-has-border="false"
                :prop-has-auto-space-logo="false"
                :prop-has-auto-space-title="false"
                :prop-has-auto-space-content="false"
                class="w-full px-1 pt-8"
            >
                <template #title>
                    <span v-show="canShowEmptyMessage">No banned recordings.</span>
                    <span v-show="canShowEndOfPageMessage">You've reached the end of this page.</span>
                </template>
            </VDialogPlain>
        </TransitionFade>

        <div id="load-more-user-banned-audio-clips-observer-target"></div>


    </div>
</template>


<script setup lang="ts">
    import VDialogPlain from '../components/small/VDialogPlain.vue';
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VAudioClipsCard from '../components/main/VAudioClipsCard.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { prettyTimeRemaining } from '@/helper_functions';
    import AudioClipsTypes from '@/types/AudioClips.interface';
    import { useVPlaybackStore } from '@/stores/VPlaybackStore';
    import { notify } from '@/wrappers/notify_wrapper';
    import axios from 'axios';

    interface ScrollableAudioClipsTypes extends AudioClipsTypes {
        scroller_index_id: number,
    }

    export default defineComponent({
        name: 'ListUserBannedAudioClipsApp',
        data(){
            return {
                audio_clips: [] as ScrollableAudioClipsTypes[],
                vplayback_store: useVPlaybackStore(),

                next_url: window.location.origin + '/api/audio-clips/bans/list/next',
                back_url: window.location.origin + '/api/audio-clips/bans/list/back',

                is_fetching: false,
                can_observer_fetch: false,
                has_no_audio_clips_left_to_fetch: false,
            };
        },
        computed: {
            canShowEmptyMessage() : boolean {

                return (
                    this.is_fetching === false &&
                    this.audio_clips.length === 0 &&
                    this.has_no_audio_clips_left_to_fetch === true
                );
            },
            canShowEndOfPageMessage() : boolean {

                return (
                    this.is_fetching === false &&
                    this.audio_clips.length > 0 &&
                    this.has_no_audio_clips_left_to_fetch === true
                );
            },
        },
        methods: {
            async getUserBannedAudioClips() : Promise<void> {

                if(this.is_fetching === true){

                    return;
                }

                this.is_fetching = true;
                this.can_observer_fetch = false;
                this.has_no_audio_clips_left_to_fetch = false;

                await axios.get(this.next_url)
                .then((result:any) => {

                    if(result.data['data'].length === 0){

                        this.has_no_audio_clips_left_to_fetch = true;
                        return;
                    }

                    result.data['data'].forEach((audio_clip:AudioClipsTypes)=>{

                        (audio_clip as ScrollableAudioClipsTypes).scroller_index_id = this.audio_clips.length;

                        this.audio_clips.push(audio_clip as ScrollableAudioClipsTypes);
                    });

                    this.next_url = result.data['next_url'];
                    this.back_url = result.data['back_url'];

                }).catch(() => {

                    notify({
                        type: 'error',
                        title: 'Error',
                        text: 'Unable to retrieve your banned recordings',
                        icon: {'font_awesome': 'fas fa-exclamation'},
                    }, 4000);

                }).finally(() => {

                    this.is_fetching = false;
                    this.can_observer_fetch = true;
                });
            },
            checkIsSelected(audio_clip_id:number) : boolean {

                const playing_audio_clip = this.vplayback_store.getPlayingAudioClip;

                return (
                    playing_audio_clip !== null &&
                    playing_audio_clip.id === audio_clip_id
                );
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

            history.scrollRestoration = 'manual';

            this.getUserBannedAudioClips();

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
        },
    });
</script>