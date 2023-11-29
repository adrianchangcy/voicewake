<template>
    <div
        :class="[
            propHasBorder === true ? 'px-2 sm:px-4 pt-8 pb-10      border border-theme-light-gray rounded-lg shade-border-when-hover transition-colors' : '',
            'flex flex-col'
        ]"
    >

        <!--title and datetime-->
        <div
            v-if="propShowTitle === true"
            class="pb-10"
        >
            <!--ugc tells crawlers that it is user-generated content-->
            <VActionText
                prop-element="a"
                :href="getEventURL"
                rel="ugc"
                class="w-full h-fit"
            >
                <VTitle
                    propFontSize="s"
                    class="w-full"
                >
                    <template #title>
                        <span
                            v-if="propEvent.event.generic_status.generic_status_name !== 'cancelled'"
                        >
                            {{ propEvent.event.event_name }}
                        </span>
                        <span v-else
                            class="italic"
                        >
                            Event and original recording cancelled.
                        </span>
                    </template>
                    <template v-if="propEvent.event.generic_status.generic_status_name !== 'cancelled'" #titleDescription>
                        <span>{{ prettyWhenCreated }}</span>
                    </template>
                </VTitle>
            </VActionText>
        </div>

        <!--if events are always completed, use this-->
        <!--child components are never re-rendered-->
        <div v-if="propIsEventAlwaysCompleted">
            <div
                v-if="propLoadVAudioClipCardsOnly"
                class="flex flex-col gap-10"
            >

                <!--originator-->
                <div
                    class="flex flex-col gap-2"
                >
                    <VUsernameURL
                        :propUsername="propEvent.originator[0]!.user.username"
                    />
                    <VAudioClipCard
                        :prop-audio-clip="propEvent.originator[0]!"
                        :prop-selected-audio-clip="currently_playing_audio_clip_store.getPlayingAudioClip"
                        @selectedAudioClip="handleSelectedAudioClip($event)"
                        @newVPlaybackTeleportId="emitNewVPlaybackTeleportId($event)"
                    />
                    <VAudioClipTools
                        :prop-audio-clip="propEvent.originator[0]!"
                        :prop-event-id="propEvent.event.id"
                        :prop-has-virtual-scroll="propHasVirtualScroll"
                        @newIsLiked="emitNewIsLiked($event)"
                    />
                </div>

                <!--responder-->
                <div
                    class="flex flex-col gap-2"
                >
                    <VUsernameURL
                        :propUsername="propEvent.responder[0]!.user.username"
                    />
                    <VAudioClipCard
                        :prop-audio-clip="propEvent.responder[0]!"
                        :prop-selected-audio-clip="currently_playing_audio_clip_store.getPlayingAudioClip"
                        @selectedAudioClip="handleSelectedAudioClip($event)"
                        @newVPlaybackTeleportId="emitNewVPlaybackTeleportId($event)"
                    />
                    <VAudioClipTools
                        :prop-audio-clip="propEvent.responder[0]!"
                        :prop-event-id="propEvent.event.id"
                        :prop-has-virtual-scroll="propHasVirtualScroll"
                        @newIsLiked="emitNewIsLiked($event)"
                    />
                </div>
            </div>

            <div
                v-else
                class="flex flex-col gap-10"
            >

                <!--originator-->
                <div
                    class="flex flex-col gap-2"
                >
                    <VUsernameURL
                        :propUsername="propEvent.responder[0]!.user.username"
                    />
                    <VPlayback
                        :prop-audio-clip="propEvent.responder[0]!"
                        :prop-audio-volume-peaks="propEvent.responder[0]!.audio_volume_peaks"
                        :prop-bucket-quantity="propEvent.responder[0]!.audio_volume_peaks.length"
                        :prop-is-open="true"
                    />
                    <VAudioClipTools
                        :prop-audio-clip="propEvent.responder[0]!"
                        :prop-event-id="propEvent.event.id"
                        :prop-has-virtual-scroll="propHasVirtualScroll"
                        @newIsLiked="emitNewIsLiked($event)"
                    />
                </div>

                <!--responder-->
                <div
                    class="flex flex-col gap-2"
                >
                    <VUsernameURL
                        :propUsername="propEvent.responder[0]!.user.username"
                    />
                    <VPlayback
                        :prop-audio-clip="propEvent.responder[0]!"
                        :prop-audio-volume-peaks="propEvent.responder[0]!.audio_volume_peaks"
                        :prop-bucket-quantity="propEvent.responder[0]!.audio_volume_peaks.length"
                        :prop-is-open="true"
                    />
                    <VAudioClipTools
                        :prop-audio-clip="propEvent.responder[0]!"
                        :prop-event-id="propEvent.event.id"
                        :prop-has-virtual-scroll="propHasVirtualScroll"
                        @newIsLiked="emitNewIsLiked($event)"
                    />
                </div>
            </div>
        </div>


        <!--if events are not guaranteed to be completed, use this-->
        <!--disadvantage is that v-for is always re-rendered-->
        <div v-else>
            <div
                v-if="propLoadVAudioClipCardsOnly"
                class="flex flex-col gap-10"
            >
        
                <!--originator-->
                <div
                    v-for="audio_clip in propEvent.originator" :key="audio_clip.id"
                    class="flex flex-col gap-2"
                >
                    <VUsernameURL
                        :propUsername="audio_clip.user.username"
                    />
                    <VAudioClipCard
                        :prop-audio-clip="audio_clip"
                        :prop-selected-audio-clip="currently_playing_audio_clip_store.getPlayingAudioClip"
                        @selectedAudioClip="handleSelectedAudioClip($event)"
                        @newVPlaybackTeleportId="emitNewVPlaybackTeleportId($event)"
                    />
                    <VAudioClipTools
                        :prop-audio-clip="audio_clip"
                        :prop-event-id="propEvent.event.id"
                        :prop-has-virtual-scroll="propHasVirtualScroll"
                        @newIsLiked="emitNewIsLiked($event)"
                    />
                </div>
            
                <!--responder-->
                <div
                    v-for="audio_clip in propEvent.responder" :key="audio_clip.id"
                    class="flex flex-col gap-2"
                >
                    <VUsernameURL
                        :propUsername="audio_clip.user.username"
                    />
                    <VAudioClipCard
                        :prop-audio-clip="audio_clip"
                        :prop-selected-audio-clip="currently_playing_audio_clip_store.getPlayingAudioClip"
                        @selectedAudioClip="handleSelectedAudioClip($event)"
                        @newVPlaybackTeleportId="emitNewVPlaybackTeleportId($event)"
                    />
                    <VAudioClipTools
                        :prop-audio-clip="audio_clip"
                        :prop-event-id="propEvent.event.id"
                        :prop-has-virtual-scroll="propHasVirtualScroll"
                        @newIsLiked="emitNewIsLiked($event)"
                    />
                </div>
            </div>
        
            <div
                v-else
                class="flex flex-col gap-10"
            >
        
                <!--originator-->
                <div
                    v-for="audio_clip in propEvent.originator" :key="audio_clip.id"
                    class="flex flex-col gap-2"
                >
                    <VUsernameURL
                        :propUsername="audio_clip.user.username"
                    />
                    <VPlayback
                        :prop-audio-clip="audio_clip"
                        :prop-audio-volume-peaks="audio_clip.audio_volume_peaks"
                        :prop-bucket-quantity="audio_clip.audio_volume_peaks.length"
                        :prop-is-open="true"
                    />
                    <VAudioClipTools
                        :prop-audio-clip="audio_clip"
                        :prop-event-id="propEvent.event.id"
                        :prop-has-virtual-scroll="propHasVirtualScroll"
                        @newIsLiked="emitNewIsLiked($event)"
                    />
                </div>
            
                <!--responder-->
                <div
                    v-for="audio_clip in propEvent.responder" :key="audio_clip.id"
                    class="flex flex-col gap-2"
                >
                    <VUsernameURL
                        :propUsername="audio_clip.user.username"
                    />
                    <VPlayback
                        :prop-audio-clip="audio_clip"
                        :prop-audio-volume-peaks="audio_clip.audio_volume_peaks"
                        :prop-bucket-quantity="audio_clip.audio_volume_peaks.length"
                        :prop-is-open="true"
                    />
                    <VAudioClipTools
                        :prop-audio-clip="audio_clip"
                        :prop-event-id="propEvent.event.id"
                        :prop-has-virtual-scroll="propHasVirtualScroll"
                        @newIsLiked="emitNewIsLiked($event)"
                    />
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
    import VActionText from '/src/components/small/VActionText.vue';
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import { prettyTimePassed } from '@/helper_functions';
    import EventsAndAudioClipsTypes from '@/types/EventsAndAudioClips.interface';
    import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';
    import { useCurrentlyPlayingAudioClipStore } from '@/stores/CurrentlyPlayingAudioClipStore';
    import AudioClipsTypes from '@/types/AudioClips.interface';

    export default defineComponent({
        data() {
            return {
                currently_playing_audio_clip_store: useCurrentlyPlayingAudioClipStore(),
            };
        },
        props: {
            propEvent: {
                type: Object as PropType<EventsAndAudioClipsTypes>,
                required: true,
            },
            propIsEventAlwaysCompleted: {
                type: Boolean,
                default: false,
            },
            propShowTitle: {
                type: Boolean,
                default: true,
            },
            propHasBorder: {
                type: Boolean,
                default: false,
            },
            propLoadVAudioClipCardsOnly: {
                type: Boolean,
                default: false,
            },
            propHasVirtualScroll: {
                type: Boolean,
                default: false,
            },
        },
        computed: {
            getEventURL() : string {

                return window.location.origin + "/event/" + this.propEvent.event.id;
            },
            prettyWhenCreated() : string {

                return prettyTimePassed(new Date(this.propEvent.event.when_created));
            },
        },
        emits: [
            'newIsLiked', 'newVPlaybackTeleportId',
        ],
        methods: {
            async emitNewVPlaybackTeleportId(teleport_id:string) : Promise<void> {

                this.$emit('newVPlaybackTeleportId', teleport_id);
            },
            async handleSelectedAudioClip(audio_clip:AudioClipsTypes|AudioClipsAndLikeDetailsTypes) : Promise<void> {

                this.currently_playing_audio_clip_store.$patch({
                    playing_audio_clip: audio_clip
                });
            },
            async emitNewIsLiked(
                new_value:{audio_clip:AudioClipsTypes|AudioClipsAndLikeDetailsTypes, new_is_liked:boolean|null}
            ) : Promise<void> {

                this.$emit('newIsLiked', new_value);
            },
        },
    });
</script>