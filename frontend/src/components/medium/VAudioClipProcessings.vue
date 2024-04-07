<template>
    <!--follow VNotiwind for design choices-->
    <Teleport to="#audio-clip-processings-target">
        <div
            v-if="canPoll"
            class="w-full flex flex-col"
        >
            <TransitionGroup
                name="audio-clip-processings-transition-group"
                enter-from-class="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-4"
                enter-active-class="transform ease-out duration-300 transition"
                enter-to-class="translate-y-0 opacity-100 sm:translate-x-0"
                leave-from-class="opacity-100"
                leave-active-class="transition ease-in duration-150"
                leave-to-class="opacity-0"
            >
                <div
                    v-for="(processing, audio_clip_id) in audio_clip_processings_store.getAudioClipProcessings"
                    :key="audio_clip_id"
                    class="flex w-full mx-auto mb-4 overflow-hidden backdrop-blur bg-white/60 rounded-lg shadow-xl"
                >
                    <!--left panel-->
                    <div
                        :class="[
                            isStatusOk(processing) ? 'bg-green-500' : '',
                            isStatusGeneric(processing) ? 'bg-theme-black' : '',
                            isStatusError(processing) ? 'bg-red-500' : '',
                            'w-10 shrink-0 flex flex-col items-center justify-center text-xl text-white'
                        ]"
                    >
                        <div
                            v-show="isStatusOk(processing) || isStatusGeneric(processing)"
                        >
                            <span class="sr-only">{{ processing.audio_clip_tone.audio_clip_tone_name }}</span>
                            <span>{{ processing.audio_clip_tone.audio_clip_tone_symbol }}</span>
                        </div>
                        <div
                            v-show="isStatusError(processing)"
                        >
                            <span>
                                <FontAwesomeIcon icon="fas fa-exclamation"/>
                            </span>
                        </div>
                    </div>

                    <!--middle panel-->
                    <div
                        :class="[
                            processing.status === 'processing' || hasActions(processing) ? 'pb-4' : 'pb-0.5',
                            'flex-1 pl-4'
                        ]"
                    >
                        <!--title, aligning to 'close' button-->
                        <div class="w-full h-10 flex items-center">
                            <span
                                :class="[
                                    isStatusOk(processing) ? 'text-green-700' : '',
                                    isStatusGeneric(processing) ? '' : '',
                                    isStatusError(processing) ? 'text-red-700' : '',
                                    'text-base font-semibold pb-0.5 break-words'
                                ]"
                            >
                                {{ processing.title }}
                            </span>
                        </div>

                        <!--text and actions-->
                        <!--translate back into title's space-->
                        <!--translate conveniently lets us skip padding-top on actions-->
                        <span class="block text-sm -translate-y-2 break-words">
                            {{ processing.main_text }}
                        </span>

                        <!--progress bar, actions-->

                        <!--progress bar-->
                        <div
                            v-if="processing.status === 'processing'"
                            class="h-10 flex items-center"
                        >
                            <VProgressBar
                                :prop-timestamps-ms="processing_timestamps_ms"
                                :prop-start-on-mounted="true"
                                :prop-step="determineVProgressBarStep(processing)"
                                class="w-full"
                            />
                        </div>

                        <!--actions-->
                        <div
                            v-else-if="hasActions(processing)"
                            class="flex flex-row w-full h-10 gap-1"
                        >
                            <div
                                v-for="(action, action_index) in processing.actions!"
                                :key="action_index"
                                class="flex-1"
                            >
                                <a
                                    v-if="action.type === 'url'"
                                    :href="action.url"
                                    class="w-full h-full flex flex-row items-center rounded-full transition       border border-theme-gray-2 shade-border-when-hover active:bg-theme-gray-1       focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline"
                                >
                                    <span class="px-4 pb-0.5 mx-auto text-sm font-medium">
                                        {{ action.text }}
                                    </span>
                                </a>
                                <button
                                    v-else
                                    @click="audio_clip_processings_store.getActionButtonCallback(audio_clip_id, action_index)"
                                    type="button"
                                    class="w-full h-full flex flex-row items-center rounded-full transition       border border-theme-gray-2 shade-border-when-hover active:bg-theme-gray-1       focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline"
                                >
                                    <span class="px-4 pb-0.5 mx-auto text-sm font-medium">
                                        {{ action.text }}
                                    </span>
                                </button>
                            </div>
                        </div>
                    </div>

                    <!--right panel-->
                    <div class="w-10 shrink-0">
                        <VActionText
                            v-if="hasCloseButton(processing)"
                            @click="audio_clip_processings_store.deleteProcessing(audio_clip_id)"
                            prop-element="button"
                            prop-element-size="s"
                            :prop-is-icon-only="true"
                            class="w-10 h-10 shrink-0 flex items-center justify-center focus-visible:-outline-offset-4"
                        >
                            <FontAwesomeIcon icon="fas fa-xmark" class="text-xl mx-auto"/>
                        </VActionText>
                    </div>
                </div>
            </TransitionGroup>
        </div>
    </Teleport>
</template>


<script setup lang="ts">
    // import VActionText from '../small/VActionText.vue';
    import VProgressBar from '../small/VProgressBar.vue';
    import VActionText from '../small/VActionText.vue';

    import { AudioClipProcessingDetailsTypes } from '@/types/AudioClipProcessingDetails.interface';

    //this is for notify({icon: "..."}) when allowed to specify
    //search for "icon: ..." folder-wide and import all of it here in advance
    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faExclamation } from '@fortawesome/free-solid-svg-icons/faExclamation';
    import { faCheck } from '@fortawesome/free-solid-svg-icons/faCheck';
    import { faCookieBite } from '@fortawesome/free-solid-svg-icons/faCookieBite';
    import { faBatteryEmpty } from '@fortawesome/free-solid-svg-icons/faBatteryEmpty';
    import { faFlag } from '@fortawesome/free-solid-svg-icons/faFlag';
    import { faFaceMehBlank } from '@fortawesome/free-regular-svg-icons/faFaceMehBlank';
    import { faXmark } from '@fortawesome/free-solid-svg-icons/faXmark';

    //remember to update Notifications.interface.ts
    library.add(
        faExclamation, faCheck, faCookieBite,
        faBatteryEmpty, faFlag, faFaceMehBlank, faXmark,
    );

    function hasActions(processing:AudioClipProcessingDetailsTypes) : boolean {

        return Object.hasOwn(processing, "actions") && processing.actions!.length > 0;
    }

    function hasCloseButton(processing:AudioClipProcessingDetailsTypes) : boolean {

        return processing['can_close'];
    }

    function isStatusError(processing:AudioClipProcessingDetailsTypes) : boolean {

        return (
            processing.status === 'lambda_error' ||
            processing.status === 'not_found'
        );
    }

    function isStatusOk(processing:AudioClipProcessingDetailsTypes) : boolean {

        return (
            processing.status === 'processed'
        );
    }

    function isStatusGeneric(processing:AudioClipProcessingDetailsTypes) : boolean {

        return (
            processing.status === 'processing'
        );
    }

    function determineVProgressBarStep(processing:AudioClipProcessingDetailsTypes) : number|null {

        if(processing.status === 'processing'){

            return 0;

        }else{

            //end
            return null;
        }
    }

</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { useAudioClipProcessingsStore } from '@/stores/AudioClipProcessingsStore';

    export default defineComponent({
        data(){
            return {
                audio_clip_processings_store: useAudioClipProcessingsStore(),

                processing_timestamps_ms: {
                    scales: [1],
                    durations: [40000],
                },
            };
        },
        computed: {
            canPoll() : boolean {

                const current_url = window.location.href;

                return (
                    current_url.includes("login") === false &&
                    current_url.includes("signup") === false &&
                    current_url.includes("start") === false &&
                    current_url.includes("event") === false
                );
            },
        },
        methods: {
        },
        beforeMount(){

            if(this.canPoll){

                this.audio_clip_processings_store.startPollingProcessings();
            }
        },
        beforeUnmount(){

            this.audio_clip_processings_store.stopPollingProcessings();
        },
    });

</script>