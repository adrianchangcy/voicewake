<template>
    <div
        :class="[
            propHasBorder === true ? 'px-4 pt-8 pb-12      border border-theme-light-gray rounded-lg' : '',
            'flex flex-col'
        ]"
    >

        <!--title and datetime-->
        <div
            v-if="propShowTitle === true"
            class="pb-10"
        >

            <VTitle
                propFontSize="s"
                class="w-full"
            >

                <template #title>
                    <span
                        v-if="propEvent.event.generic_status.generic_status_name === 'deleted'"
                        class="italic"
                    >
                        AudioClip and original recording deleted.
                    </span>
                    <span v-else>
                        {{ propEvent.event.event_name }}
                    </span>
                </template>
                <template v-if="propEvent.event.generic_status.generic_status_name !== 'deleted'" #titleDescription>
                    <span>{{ pretty_when_created }}</span>
                </template>
            </VTitle>
        </div>

        <!--more than 1 audio_clip each-->
        <div v-if="originatorCount > 0 && responderCount > 0" class="flex flex-col gap-10">

            <!--originator-->
            <div
                v-show="originatorCount > 0"
                class="flex flex-col gap-2"
            >
                <VUsernameURL
                    :propUsername="propEvent.originator!.user.username"
                />
                <VAudioClipCard
                    :propAudioClip="propEvent.originator"
                    :propIsSelected="checkIsSelected(propEvent.originator!.id)"
                    @isSelected="handleNewSelectedAudioClip($event)"
                />
                <VAudioClipTools
                    :propAudioClip="propEvent.originator"
                    :propEventId="propEvent.event.id"
                />
            </div>

            <!--responders-->
            <div
                v-for="audio_clip in propEvent.responder" :key="audio_clip.id"
                class="flex flex-col gap-2"
            >
                <VUsernameURL
                    :propUsername="audio_clip.user.username"
                />
                <VAudioClipCard
                    :propAudioClip="audio_clip"
                    :propIsSelected="checkIsSelected(audio_clip.id)"
                    @isSelected="handleNewSelectedAudioClip($event)"
                />
                <VAudioClipTools
                    :propAudioClip="audio_clip"
                    :propEventId="propEvent.event.id"
                />
            </div>
        </div>

        <!--only 1 audio_clip total-->
        <!--must use v-if here, else VPlayback error, unsure why its code runs when it's using v-else and not v-show-->
        <div v-else class="flex flex-col gap-10">

            <!--originator-->
            <div
                v-show="originatorCount > 0"
                class="flex flex-col gap-2"
            >
                <VUsernameURL
                    :propUsername="propEvent.originator!.user.username"
                />
                <VAudioClipCard
                    v-if="propLoadVAudioClipCardsOnly"
                    :propAudioClip="propEvent.originator"
                    :propIsSelected="checkIsSelected(propEvent.originator!.id)"
                    @isSelected="handleNewSelectedAudioClip($event)"
                />
                <VPlayback
                    v-else
                    :propAudioClip="propEvent.originator"
                    :propAudioVolumePeaks="propEvent.originator!.audio_volume_peaks"
                    :propBucketQuantity="propEvent.originator!.audio_volume_peaks.length"
                />
                <VAudioClipTools
                    :propAudioClip="propEvent.originator"
                    :propEventId="propEvent.event.id"
                />
            </div>

            <!--responders-->
            <div v-show="responderCount > 0">
                <div v-if="propLoadVAudioClipCardsOnly">
                    <div
                        v-for="audio_clip in propEvent.responder" :key="audio_clip.id"
                        class="flex flex-col gap-2"
                    >
                        <VUsernameURL
                            :propUsername="audio_clip.user.username"
                        />
                        <VAudioClipCard
                            :propAudioClip="audio_clip"
                            :propIsSelected="checkIsSelected(audio_clip.id)"
                            @isSelected="handleNewSelectedAudioClip($event)"
                        />
                        <VAudioClipTools
                            :propAudioClip="audio_clip"
                            :propEventId="propEvent.event.id"
                        />
                    </div>
                </div>
                <div v-else>
                    <div
                        v-for="audio_clip in propEvent.responder" :key="audio_clip.id"
                        class="flex flex-col gap-2"
                    >
                        <VUsernameURL
                            :propUsername="audio_clip.user.username"
                        />
                        <VPlayback
                            :propAudioClip="audio_clip"
                            :propAudioVolumePeaks="audio_clip.audio_volume_peaks"
                            :propBucketQuantity="audio_clip.audio_volume_peaks.length"
                        />
                        <VAudioClipTools
                            :propAudioClip="audio_clip"
                            :propEventId="propEvent.event.id"
                        />
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    import VTitle from '../small/VTitle.vue';
    import VPlayback from '/src/components/medium/VPlayback.vue';
    import VAudioClipCard from '/src/components/medium/VAudioClipCard.vue';
    import VAudioClipTools from '/src/components/medium/VAudioClipTools.vue';
    import VUsernameURL from '/src/components/small/VUsernameURL.vue';
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import { prettyTimePassed } from '@/helper_functions';
    import EventsAndAudioClipsTypes from '@/types/EventsAndAudioClips.interface';
    import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';
    import { useCurrentlyPlayingAudioClipStore } from '@/stores/CurrentlyPlayingAudioClipStore';

    export default defineComponent({
        data() {
            return {
                currently_playing_audio_clip_store: useCurrentlyPlayingAudioClipStore(),
                pretty_when_created: '',
            };
        },
        props: {
            propEvent: {
                type: Object as PropType<EventsAndAudioClipsTypes>,
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
            propLoadVAudioClipCardsOnly: {
                type: Boolean,
                default: false
            },
        },
        computed: {
            originatorCount() : number {

                if(this.propEvent === null || this.propEvent.originator === null){

                    return 0;
                }

                return 1;
            },
            responderCount() : number {

                if(this.propEvent === null){

                    return 0;
                }

                return this.propEvent.responder.length;
            },
        },
        watch: {

        },
        methods: {
            checkIsSelected(audio_clip_id:number) : boolean {

                const playing_audio_clip = this.currently_playing_audio_clip_store.getPlayingAudioClip;

                return (
                    playing_audio_clip !== null &&
                    playing_audio_clip.id === audio_clip_id
                );
            },
            handleNewSelectedAudioClip(audio_clip:AudioClipsAndLikeDetailsTypes) : void {

                this.currently_playing_audio_clip_store.$patch({
                    playing_audio_clip: audio_clip
                });
            },
        },
        beforeMount(){

            this.pretty_when_created = prettyTimePassed(new Date(this.propEvent.event.when_created));
        },
    });
</script>