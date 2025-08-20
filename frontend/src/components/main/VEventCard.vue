<template>
    <div
        :class="[
            propHasBorder === true ? 'border-y border-theme-gray-1 dark:border-dark-theme-gray-1' : '',
            propHasPadding === true ? 'px-2 sm:px-4 pt-8 pb-12' : '',
            'flex flex-col'
        ]"
    >

        <!--title and datetime-->
        <div
            v-if="propShowTitle === true"
            class="pb-5"
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
                    class="dark:text-dark-theme-white-1"
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
                            Event deleted.
                        </span>
                    </template>
                </VTitle>
            </VActionText>
            <VTitle
                prop-font-size="s"
            >
                <template #titleDescription>
                    <span>
                        {{ prettyWhenCreated }}
                    </span>
                </template>
            </VTitle>
        </div>

        <!--originally completed-->
        <div
            v-if="propGuaranteedOriginatorCount === 1 && propGuaranteedResponderCount === 1"
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
                    <!--v-show because component can be reused by virtual scroll-->
                    <div
                        v-show="propEvent.originator[0]!.generic_status.generic_status_name === 'deleted'"
                        class="w-full h-20 flex items-center text-center border border-theme-gray-2 dark:border-dark-theme-gray-2 rounded-lg"
                    >
                        <span class="w-full h-fit text-base">Recording deleted.</span>
                    </div>
                    <div v-show="propEvent.originator[0]!.generic_status.generic_status_name === 'ok'">
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
                    </div>
                    <VAudioClipTools
                        :prop-audio-clip="propEvent.originator[0]!"
                        :prop-has-virtual-scroll="propHasVirtualScroll"
                        :prop-is-logged-in="propIsLoggedIn"
                        :prop-is-superuser="propIsSuperuser"
                        :prop-username="propUsername"
                        :prop-callable-popup-login-required="propCallablePopupLoginRequired"
                        @new-is-liked="emitNewIsLiked($event)"
                        @new-audio-clip-action="emitNewAudioClipAction($event)"
                    />
                </div>
            </div>

            <!--responder-->
            <div
                class="flex flex-col"
            >
                <span>
                    <VUsernameURL
                        :propUsername="propEvent.responder[0]!.user.username"
                        :propShowRepliedText="true"
                    />
                </span>
                <div class="flex flex-col gap-2">
                    <div
                        v-show="propEvent.responder[0]!.generic_status.generic_status_name === 'deleted'"
                        class="w-full h-20 flex items-center text-center border border-theme-gray-2 dark:border-dark-theme-gray-2 rounded-lg"
                    >
                        <span class="w-full h-fit text-base">Recording deleted.</span>
                    </div>
                    <div v-show="propEvent.responder[0]!.generic_status.generic_status_name === 'ok'">
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
                    </div>
                    <VAudioClipTools
                        :prop-audio-clip="propEvent.responder[0]!"
                        :prop-has-virtual-scroll="propHasVirtualScroll"
                        :prop-is-logged-in="propIsLoggedIn"
                        :prop-is-superuser="propIsSuperuser"
                        :prop-username="propUsername"
                        :prop-callable-popup-login-required="propCallablePopupLoginRequired"
                        @new-is-liked="emitNewIsLiked($event)"
                        @new-audio-clip-action="emitNewAudioClipAction($event)"
                    />
                </div>
            </div>
        </div>

        <!--originally incomplete-->
        <div
            v-else-if="propGuaranteedOriginatorCount === 1"
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
                    <div
                        v-show="propEvent.originator[0]!.generic_status.generic_status_name === 'deleted'"
                        class="w-full h-20 flex items-center text-center border border-theme-gray-2 dark:border-dark-theme-gray-2 rounded-lg"
                    >
                        <span class="w-full h-fit text-base">Recording deleted.</span>
                    </div>
                    <div v-show="propEvent.originator[0]!.generic_status.generic_status_name === 'ok'">
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
                    </div>
                    <VAudioClipTools
                        :prop-audio-clip="propEvent.originator[0]!"
                        :prop-has-virtual-scroll="propHasVirtualScroll"
                        :prop-is-logged-in="propIsLoggedIn"
                        :prop-is-superuser="propIsSuperuser"
                        :prop-username="propUsername"
                        :prop-callable-popup-login-required="propCallablePopupLoginRequired"
                        @new-is-liked="emitNewIsLiked($event)"
                        @new-audio-clip-action="emitNewAudioClipAction($event)"
                    />
                </div>
            </div>
        </div>


        <!--if events are not guaranteed to be completed, use this-->
        <!--disadvantage is that v-for is always re-rendered-->
        <div
            v-else
        >
            <!--use VAudioClipCard as first render-->
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
                        <div
                            v-show="audio_clip.generic_status.generic_status_name === 'deleted'"
                            class="w-full h-20 flex items-center text-center border border-theme-gray-2 dark:border-dark-theme-gray-2 rounded-lg"
                        >
                            <span class="w-full h-fit text-base">Recording deleted.</span>
                        </div>
                        <div v-show="audio_clip.generic_status.generic_status_name === 'ok'">
                            <VAudioClipCard
                                :prop-audio-clip="audio_clip"
                                :prop-selected-audio-clip="vplayback_store.getPlayingAudioClip"
                                @selectedAudioClip="vplayback_store.updatePlayingAudioClip($event)"
                                @newVPlaybackTeleportId="emitNewVPlaybackTeleportId($event)"
                            />
                        </div>
                        <VAudioClipTools
                            :prop-audio-clip="audio_clip"
                            :prop-has-virtual-scroll="propHasVirtualScroll"
                            :prop-is-logged-in="propIsLoggedIn"
                            :prop-is-superuser="propIsSuperuser"
                            :prop-username="propUsername"
                            :prop-callable-popup-login-required="propCallablePopupLoginRequired"
                            @new-is-liked="emitNewIsLiked($event)"
                            @new-audio-clip-action="emitNewAudioClipAction($event)"
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
                        :propShowRepliedText="true"
                    />
                    <div class="flex flex-col gap-2">
                        <div
                            v-show="audio_clip.generic_status.generic_status_name === 'deleted'"
                            class="w-full h-20 flex items-center text-center border border-theme-gray-2 dark:border-dark-theme-gray-2 rounded-lg"
                        >
                            <span class="w-full h-fit text-base">Recording deleted.</span>
                        </div>
                        <div v-show="audio_clip.generic_status.generic_status_name === 'ok'">
                            <VAudioClipCard
                                :prop-audio-clip="audio_clip"
                                :prop-selected-audio-clip="vplayback_store.getPlayingAudioClip"
                                @selectedAudioClip="vplayback_store.updatePlayingAudioClip($event)"
                                @newVPlaybackTeleportId="emitNewVPlaybackTeleportId($event)"
                            />
                        </div>
                        <VAudioClipTools
                            :prop-audio-clip="audio_clip"
                            :prop-has-virtual-scroll="propHasVirtualScroll"
                            :prop-is-logged-in="propIsLoggedIn"
                            :prop-is-superuser="propIsSuperuser"
                            :prop-username="propUsername"
                            :prop-callable-popup-login-required="propCallablePopupLoginRequired"
                            @new-is-liked="emitNewIsLiked($event)"
                            @new-audio-clip-action="emitNewAudioClipAction($event)"
                        />
                    </div>
                </div>
            </div>
        
            <!--use VPlayback as first render-->
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
                        <div
                            v-show="audio_clip.generic_status.generic_status_name === 'deleted'"
                            class="w-full h-20 flex items-center text-center border border-theme-gray-2 dark:border-dark-theme-gray-2 rounded-lg"
                        >
                            <span class="w-full h-fit text-base">Recording deleted.</span>
                        </div>
                        <div v-show="audio_clip.generic_status.generic_status_name === 'ok'">
                            <VPlayback
                                :prop-audio-clip="audio_clip"
                                :prop-audio-volume-peaks="audio_clip.audio_volume_peaks"
                                :prop-bucket-quantity="audio_clip.audio_volume_peaks.length"
                                :prop-is-open="propIsVPlaybackOpen"
                            />
                        </div>
                        <VAudioClipTools
                            :prop-audio-clip="audio_clip"
                            :prop-has-virtual-scroll="propHasVirtualScroll"
                            :prop-is-logged-in="propIsLoggedIn"
                            :prop-is-superuser="propIsSuperuser"
                            :prop-username="propUsername"
                            :prop-callable-popup-login-required="propCallablePopupLoginRequired"
                            @new-is-liked="emitNewIsLiked($event)"
                            @new-audio-clip-action="emitNewAudioClipAction($event)"
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
                        :propShowRepliedText="true"
                    />
                    <div class="flex flex-col gap-2">
                        <div
                            v-show="audio_clip.generic_status.generic_status_name === 'deleted'"
                            class="w-full h-20 flex items-center text-center border border-theme-gray-2 dark:border-dark-theme-gray-2 rounded-lg"
                        >
                            <span class="w-full h-fit text-base">Recording deleted.</span>
                        </div>
                        <div v-show="audio_clip.generic_status.generic_status_name === 'ok'">
                            <VPlayback
                                :prop-audio-clip="audio_clip"
                                :prop-audio-volume-peaks="audio_clip.audio_volume_peaks"
                                :prop-bucket-quantity="audio_clip.audio_volume_peaks.length"
                                :prop-is-open="propIsVPlaybackOpen"
                            />
                        </div>
                        <VAudioClipTools
                            :prop-audio-clip="audio_clip"
                            :prop-has-virtual-scroll="propHasVirtualScroll"
                            :prop-is-logged-in="propIsLoggedIn"
                            :prop-is-superuser="propIsSuperuser"
                            :prop-username="propUsername"
                            :prop-callable-popup-login-required="propCallablePopupLoginRequired"
                            @new-is-liked="emitNewIsLiked($event)"
                            @new-audio-clip-action="emitNewAudioClipAction($event)"
                        />
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    import VTitle from '@/components/small/VTitle.vue';
    import VPlayback from '@/components/medium/VPlayback.vue';
    import VAudioClipCard from '@/components/medium/VAudioClipCard.vue';
    import VAudioClipTools from '@/components/medium/VAudioClipTools.vue';
    import VUsernameURL from '@/components/small/VUsernameURL.vue';
    import VActionText from '@/components/small/VActionText.vue';
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import { prettyTimePassed } from '@/helper_functions';
    import EventsAndAudioClipsTypes from '@/types/EventsAndAudioClips.interface';
    import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';
    import { useVPlaybackStore } from '@/stores/VPlaybackStore';
    import AudioClipsTypes from '@/types/AudioClips.interface';
    import AudioClipActionsTypes from '@/types/AudioClipActions.interface';

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
            propEventListIndex: {
                //this is if VEventCard is used in for-loop of events []
                type: Number,
                default: null,
            },
            propGuaranteedOriginatorCount: {
                //this is useful for avoiding v-for, so child components are never unmounted
                type: Number,
                default: null,
            },
            propGuaranteedResponderCount: {
                //this is useful for avoiding v-for, so child components are never unmounted
                type: Number,
                default: null,
            },
            propShowTitle: {
                type: Boolean,
                default: true,
            },
            propHasBorder: {
                type: Boolean,
                default: false,
            },
            propHasPadding: {
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
            propIsLoggedIn: {
                type: Boolean,
                required: true,
            },
            propIsSuperuser: {
                type: Boolean,
                required: true,
            },
            propCallablePopupLoginRequired: {
                type: Function,
                required: true,
            },
            propUsername: {
                type: String,
                required: true,
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
            'newIsLiked', 'newVPlaybackTeleportId', 'newAudioClipAction',
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
            emitNewAudioClipAction(new_value:AudioClipActionsTypes) : void {

                if(this.propEventListIndex !== null){

                    new_value.event_list_index = this.propEventListIndex;
                }

                this.$emit('newAudioClipAction', new_value);
            },
        },
    });
</script>