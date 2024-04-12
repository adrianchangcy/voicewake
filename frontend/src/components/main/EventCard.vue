<template>
    <div
        :class="[
            propHasBorder === true ? 'px-2 sm:px-4 pt-8 pb-12      border border-theme-gray-2 rounded-lg shade-border-when-hover transition-colors' : '',
            'flex flex-col'
        ]"
    >

        <!--title and datetime-->
        <div
            v-if="propShowTitle === true"
            class="pb-8"
        >
            <!--ugc tells crawlers that it is user-generated content-->
            <VActionText
                prop-element="a"
                :href="getEventURL"
                rel="ugc"
                class="w-fit"
            >
                <VTitle
                    prop-font-size="s"
                >
                    <template #title>
                        <span
                            v-if="!isEventDeleted"
                        >
                            {{ propEvent.event.event_name }}
                        </span>
                        <span
                            v-else
                            class="italic"
                        >
                            Event and original recording deleted.
                        </span>
                    </template>
                    <template #titleDescription>
                        <span v-if="!isEventDeleted">
                            {{ prettyWhenCreated }}
                        </span>
                    </template>
                </VTitle>
            </VActionText>
        </div>

        <div
            v-if="propGuaranteedEventGenericStatus === 'completed'"
            class="flex flex-col gap-8"
        >

            <!--originator-->
            <div
                class="flex flex-col"
            >
                <VUsernameURL
                    :propUsername="propEvent.originator[0]!.user.username"
                />
                <div class="flex flex-col gap-2">
                    <VAudioClipCard
                        v-if="propLoadVAudioClipCardsOnly === true"
                        :prop-audio-clip="propEvent.originator[0]!"
                        :prop-selected-audio-clip="vplayback_store.getPlayingAudioClip"
                        @selectedAudioClip="vplayback_store.updatePlayingAudioClip($event)"
                        @newVPlaybackTeleportId="emitNewVPlaybackTeleportId($event)"
                    />
                    <VPlayback
                        v-else
                        :prop-audio-clip="propEvent.originator[0]!"
                        :prop-audio-volume-peaks="propEvent.originator[0]!.audio_volume_peaks"
                        :prop-bucket-quantity="propEvent.originator[0]!.audio_volume_peaks.length"
                        :prop-is-open="propIsVPlaybackOpen"
                    />
                    <VAudioClipTools
                        :prop-audio-clip="propEvent.originator[0]!"
                        :prop-has-virtual-scroll="propHasVirtualScroll"
                        @new-is-liked="emitNewIsLiked($event)"
                    />
                </div>
            </div>

            <!--responder-->
            <div
                class="flex flex-col"
            >
                <VUsernameURL
                    :propUsername="propEvent.responder[0]!.user.username"
                />
                <div class="flex flex-col gap-2">
                    <VAudioClipCard
                        v-if="propLoadVAudioClipCardsOnly === true"
                        :prop-audio-clip="propEvent.responder[0]!"
                        :prop-selected-audio-clip="vplayback_store.getPlayingAudioClip"
                        @selectedAudioClip="vplayback_store.updatePlayingAudioClip($event)"
                        @newVPlaybackTeleportId="emitNewVPlaybackTeleportId($event)"
                    />
                    <VPlayback
                        v-else
                        :prop-audio-clip="propEvent.responder[0]!"
                        :prop-audio-volume-peaks="propEvent.responder[0]!.audio_volume_peaks"
                        :prop-bucket-quantity="propEvent.responder[0]!.audio_volume_peaks.length"
                        :prop-is-open="propIsVPlaybackOpen"
                    />
                    <VAudioClipTools
                        :prop-audio-clip="propEvent.responder[0]!"
                        :prop-has-virtual-scroll="propHasVirtualScroll"
                        @new-is-liked="emitNewIsLiked($event)"
                    />
                </div>
            </div>
        </div>

        <div
            v-else-if="propGuaranteedEventGenericStatus === 'incomplete'"
            class="flex flex-col gap-8"
        >
            <!--originator-->
            <div
                class="flex flex-col"
            >
                <VUsernameURL
                    :propUsername="propEvent.originator[0]!.user.username"
                />
                <div class="flex flex-col gap-2">
                    <VAudioClipCard
                        v-if="propLoadVAudioClipCardsOnly === true"
                        :prop-audio-clip="propEvent.originator[0]!"
                        :prop-selected-audio-clip="vplayback_store.getPlayingAudioClip"
                        @selectedAudioClip="vplayback_store.updatePlayingAudioClip($event)"
                        @newVPlaybackTeleportId="emitNewVPlaybackTeleportId($event)"
                    />
                    <VPlayback
                        v-else
                        :prop-audio-clip="propEvent.originator[0]!"
                        :prop-audio-volume-peaks="propEvent.originator[0]!.audio_volume_peaks"
                        :prop-bucket-quantity="propEvent.originator[0]!.audio_volume_peaks.length"
                        :prop-is-open="propIsVPlaybackOpen"
                    />
                    <VAudioClipTools
                        :prop-audio-clip="propEvent.originator[0]!"
                        :prop-has-virtual-scroll="propHasVirtualScroll"
                        @new-is-liked="emitNewIsLiked($event)"
                    />
                </div>
            </div>
        </div>


        <!--if events are not guaranteed to be completed, use this-->
        <!--disadvantage is that v-for is always re-rendered-->
        <div
            v-else
        >
            <div
                v-if="propLoadVAudioClipCardsOnly"
                class="flex flex-col gap-8"
            >
        
                <!--originator-->
                <div
                    v-for="audio_clip in propEvent.originator" :key="audio_clip.id"
                    class="flex flex-col"
                >
                    <VUsernameURL
                        :propUsername="audio_clip.user.username"
                    />
                    <div class="flex flex-col gap-2">
                        <VAudioClipCard
                            :prop-audio-clip="audio_clip"
                            :prop-selected-audio-clip="vplayback_store.getPlayingAudioClip"
                            @selectedAudioClip="vplayback_store.updatePlayingAudioClip($event)"
                            @newVPlaybackTeleportId="emitNewVPlaybackTeleportId($event)"
                        />
                        <VAudioClipTools
                            :prop-audio-clip="audio_clip"
                            :prop-has-virtual-scroll="propHasVirtualScroll"
                            @new-is-liked="emitNewIsLiked($event)"
                        />
                    </div>
                </div>
            
                <!--responder-->
                <div
                    v-for="audio_clip in propEvent.responder" :key="audio_clip.id"
                    class="flex flex-col"
                >
                    <VUsernameURL
                        :propUsername="audio_clip.user.username"
                    />
                    <div class="flex flex-col gap-2">
                        <VAudioClipCard
                            :prop-audio-clip="audio_clip"
                            :prop-selected-audio-clip="vplayback_store.getPlayingAudioClip"
                            @selectedAudioClip="vplayback_store.updatePlayingAudioClip($event)"
                            @newVPlaybackTeleportId="emitNewVPlaybackTeleportId($event)"
                        />
                        <VAudioClipTools
                            :prop-audio-clip="audio_clip"
                            :prop-has-virtual-scroll="propHasVirtualScroll"
                            @new-is-liked="emitNewIsLiked($event)"
                        />
                    </div>
                </div>
            </div>
        
            <div
                v-else
                class="flex flex-col gap-8"
            >
        
                <!--originator-->
                <div
                    v-for="audio_clip in propEvent.originator" :key="audio_clip.id"
                    class="flex flex-col"
                >
                    <VUsernameURL
                        :propUsername="audio_clip.user.username"
                    />
                    <div class="flex flex-col gap-2">
                        <VPlayback
                            :prop-audio-clip="audio_clip"
                            :prop-audio-volume-peaks="audio_clip.audio_volume_peaks"
                            :prop-bucket-quantity="audio_clip.audio_volume_peaks.length"
                            :prop-is-open="propIsVPlaybackOpen"
                        />
                        <VAudioClipTools
                            :prop-audio-clip="audio_clip"
                            :prop-has-virtual-scroll="propHasVirtualScroll"
                            @new-is-liked="emitNewIsLiked($event)"
                        />
                    </div>
                </div>
            
                <!--responder-->
                <div
                    v-for="audio_clip in propEvent.responder" :key="audio_clip.id"
                    class="flex flex-col"
                >
                    <VUsernameURL
                        :propUsername="audio_clip.user.username"
                    />
                    <div class="flex flex-col gap-2">
                        <VPlayback
                            :prop-audio-clip="audio_clip"
                            :prop-audio-volume-peaks="audio_clip.audio_volume_peaks"
                            :prop-bucket-quantity="audio_clip.audio_volume_peaks.length"
                            :prop-is-open="propIsVPlaybackOpen"
                        />
                        <VAudioClipTools
                            :prop-audio-clip="audio_clip"
                            :prop-has-virtual-scroll="propHasVirtualScroll"
                            @new-is-liked="emitNewIsLiked($event)"
                        />
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    import VTitle from '../small/VTitle.vue';
    import VPlayback from '../medium/VPlayback.vue';
    import VAudioClipCard from '../medium/VAudioClipCard.vue';
    import VAudioClipTools from '../medium/VAudioClipTools.vue';
    import VUsernameURL from '../small/VUsernameURL.vue';
    import VActionText from '../small/VActionText.vue';
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import { prettyTimePassed } from '@/helper_functions';
    import EventsAndAudioClipsTypes from '@/types/EventsAndAudioClips.interface';
    import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';
    import { useVPlaybackStore } from '@/stores/VPlaybackStore';
    import AudioClipsTypes from '@/types/AudioClips.interface';

    type GuaranteedEventGenericStatuses = "completed"|"incomplete"|"";

    export default defineComponent({
        data() {
            return {
                vplayback_store: useVPlaybackStore(),
            };
        },
        props: {
            propEvent: {
                type: Object as PropType<EventsAndAudioClipsTypes>,
                required: true,
            },
            propGuaranteedEventGenericStatus: {
                //this is useful for avoiding v-for, so child components are never unmounted
                type: String as PropType<GuaranteedEventGenericStatuses>,
                default: "",
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
            propIsVPlaybackOpen: {
                type: Boolean,
                default: true,
            },
        },
        computed: {
            getEventURL() : string {

                return window.location.origin + "/event/" + this.propEvent.event.id;
            },
            prettyWhenCreated() : string {

                return prettyTimePassed(new Date(this.propEvent.event.when_created));
            },
            isEventDeleted() : boolean {

                return this.propEvent.event.generic_status.generic_status_name === 'deleted';
            }
        },
        emits: [
            'newIsLiked', 'newVPlaybackTeleportId',
        ],
        methods: {
            emitNewVPlaybackTeleportId(teleport_id:string) : void {

                this.$emit('newVPlaybackTeleportId', teleport_id);
            },
            emitNewIsLiked(
                new_value:{audio_clip:AudioClipsTypes|AudioClipsAndLikeDetailsTypes, new_is_liked:boolean|null}
            ) : void {

                this.$emit('newIsLiked', new_value);
            },
        },
    });
</script>