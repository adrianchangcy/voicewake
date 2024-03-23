<template>
    <!--follow VNotiwind for design choices-->
    <Teleport to="#audio-clip-processings-target">
        <div class="w-full flex flex-col">
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
                    v-for="(processing, key) in ding_dong_store.getProcessings"
                    :key="key"
                    class="flex w-full mx-auto mb-4 overflow-hidden backdrop-blur bg-white/60 rounded-lg shadow-xl"
                >
                    <!--left panel-->
                    <div
                        :class="[
                            isStatusOk(processing.status) ? 'bg-green-500' : '',
                            isStatusGeneric(processing.status) ? 'bg-theme-black' : '',
                            isStatusError(processing.status) ? 'bg-red-500' : '',
                            'w-10 shrink-0 flex flex-col items-center justify-center text-xl text-white'
                        ]"
                    >
                        <div
                            v-show="isStatusOk || isStatusGeneric"
                        >
                            <span class="sr-only">{{ processing.audio_clip_tone.audio_clip_tone_name }}</span>
                            <span>{{ processing.audio_clip_tone.audio_clip_tone_symbol }}</span>
                        </div>
                        <div
                            v-show="isStatusError(processing.status)"
                        >
                            <span>
                                <FontAwesomeIcon icon="fas fa-exclamation"/>
                            </span>
                        </div>
                    </div>

                    <!--middle panel-->
                    <div
                        :class="[
                            processing.status === 'processing' || hasActions(processing.status) ? 'pb-4' : 'pb-0.5',
                            'flex-1 pl-4'
                        ]"
                    >
                        <!--title, aligning to 'close' button-->
                        <div class="w-full h-10 flex items-center">
                            <span
                                :class="[
                                    isStatusOk(processing.status) ? 'text-green-700' : '',
                                    isStatusGeneric(processing.status) ? '' : '',
                                    isStatusError(processing.status) ? 'text-red-700' : '',
                                    'text-base font-semibold pb-0.5 break-words'
                                ]"
                            >
                                {{ getPrettyStatus(processing.status) }}
                            </span>
                        </div>

                        <!--text and actions-->
                        <!--translate back into title's space-->
                        <!--translate conveniently lets us skip padding-top on actions-->
                        <span class="block text-sm -translate-y-2 break-words">
                            Event: "{{ getShortenedString(processing.event.event_name, 10) }}"
                        </span>

                        <!--progress bar, action-->
                        <div class="h-10 flex items-center">

                            <!--progress bar-->
                            <VProgressBar
                                v-if="processing.status === 'processing'"
                                :prop-timestamps-ms="processing_timestamps_ms"
                                :prop-start-on-mounted="true"
                                :prop-step="determineVProgressBarStep(processing.status)"
                                class="w-full"
                            />

                            <!--action-->
                            <a
                                v-else-if="hasActions(processing.status)"
                                :href="processing.action_url!.url"
                                class="w-full h-full flex flex-row items-center rounded-full transition       border border-theme-gray-2 shade-border-when-hover active:bg-theme-gray-1       focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline"
                            >
                                <span class="px-4 pb-0.5 mx-auto text-sm font-medium">
                                    {{ processing.action_url!.text }}
                                </span>
                            </a>
                        </div>
                    </div>

                    <!--right panel-->
                    <div class="w-10 shrink-0">
                        <VActionText
                            v-if="hasCloseButton(processing.status)"
                            @click="processing.close_callback()"
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

    import AudioClipProcessingStatusesTypes from '@/types/values/AudioClipProcessingStatuses';

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

    function hasActions(status:AudioClipProcessingStatusesTypes) : boolean {

        return (
            status === 'processed' ||
            status === 'lambda_error'
        );
    }

    function hasCloseButton(status:AudioClipProcessingStatusesTypes) : boolean {

        return (
            status === 'processed' ||
            status === 'lambda_error' ||
            status === 'not_found'
        );
    }

    function getPrettyStatus(status:AudioClipProcessingStatusesTypes) : string {

        switch(status){

            case 'processing':
                return 'Processing recording';

            case 'processed':
                return 'Recording processed';

            case 'error':
                return 'Recording error';

            case 'lambda_error':
                return 'Recording error';

            case 'not_found':
                return 'Recording removed';

            default:
                throw new Error('Unrecognised.');
        }
    }

    function isStatusError(status:AudioClipProcessingStatusesTypes) : boolean {

        return (
            status === 'error' ||
            status === 'lambda_error' ||
            status === 'not_found'
        );
    }

    function isStatusOk(status:AudioClipProcessingStatusesTypes) : boolean {

        return (
            status === 'processed'
        );
    }

    function isStatusGeneric(status:AudioClipProcessingStatusesTypes) : boolean {

        return (
            status === 'processing'
        );
    }

    function determineVProgressBarStep(status:AudioClipProcessingStatusesTypes) : number|null {

        if(status === 'processing'){

            return 0;

        }else{

            //end
            return null;
        }
    }

</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { useDingDongStore } from '@/stores/DingDongStore';
    import { getShortenedString } from '@/helper_functions';


    export default defineComponent({
        data(){
            return {
                ding_dong_store: useDingDongStore(),

                processing_timestamps_ms: {
                    scales: [1],
                    durations: [40000],
                },
            };
        },
        methods: {
        },
    });

</script>