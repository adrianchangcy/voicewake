<template>
    <!--follow VNotiwind for design choices-->
    <Teleport to="#audio-clip-processings-target">
        <div
            v-if="canShowNotifications"
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
                    class="flex w-full mx-auto mb-4 overflow-hidden bg-white dark:bg-dark-theme-black-2 rounded-lg shadow-xl dark:shadow-none"
                >
                    <!--left panel-->
                    <div
                        :class="[
                            isStatusOk(processing) ? 'bg-green-500 dark:text-dark-theme-black-2' : '',
                            isStatusError(processing) ? 'bg-red-500 dark:text-dark-theme-black-2' : '',
                            isStatusGeneric(processing) ? 'bg-theme-black dark:text-dark-theme-white-1' : '',
                            'w-10 shrink-0 flex flex-col items-center justify-center text-white text-xl'
                        ]"
                    >
                        <div
                            v-show="isStatusOk(processing) || isStatusGeneric(processing)"
                        >
                            <span class="sr-only">{{ processing.audio_clip_tone.audio_clip_tone_name }}</span>
                            <span class="has-emoji">{{ processing.audio_clip_tone.audio_clip_tone_symbol }}</span>
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
                            isStatusGeneric(processing) || hasActions(processing) ? 'pb-4' : 'pb-0.5',
                            hasCloseButton(processing) ? 'pl-4' : 'px-4',
                            'flex-1'
                        ]"
                    >
                        <!--title, aligning to 'close' button-->
                        <div class="w-full h-10 flex items-center">
                            <span
                                :class="[
                                    isStatusOk(processing) ? 'text-green-700 dark:text-green-400' : '',
                                    isStatusError(processing) ? 'text-red-700 dark:text-red-400' : '',
                                    isStatusGeneric(processing) ? 'text-theme-black dark:text-dark-theme-white-1' : '',
                                    'text-base font-semibold break-words'
                                ]"
                            >
                                {{ processing.title }}
                            </span>
                        </div>

                        <!--text and actions-->
                        <!--translate back into title's space-->
                        <!--translate conveniently lets us skip padding-top on actions-->
                        <span class="block text-sm -translate-y-2 break-words text-theme-black dark:text-dark-theme-white-2">
                            {{ processing.main_text }}
                        </span>

                        <!--progress bar, actions-->

                        <!--progress bar-->
                        <div
                            v-if="isStatusGeneric(processing)"
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

                                <VActionBorder
                                    v-if="action.type === 'url'"
                                    :href="action.url"
                                    prop-element="a"
                                    prop-element-size="s"
                                    prop-font-size="s"
                                    class="w-full"
                                >
                                    <span class="mx-auto px-2">
                                        {{ action.text }}
                                    </span>
                                </VActionBorder>

                                <VActionBorder
                                    v-else-if="action.type === 'button'"
                                    @click="audio_clip_processings_store.getActionButtonCallback(audio_clip_id, action_index)"
                                    :prop-is-enabled="!isClosing(processing)"
                                    prop-element="button"
                                    prop-element-size="s"
                                    prop-font-size="s"
                                    type="button"
                                    class="w-full"
                                >
                                    <span class="mx-auto px-2">
                                        {{ action.text }}
                                    </span>
                                </VActionBorder>
                            </div>
                        </div>
                    </div>

                    <!--right panel-->
                    <VActionText
                        v-if="hasCloseButton(processing)"
                        @click="audio_clip_processings_store.deleteAudioClipProcessing(audio_clip_id)"
                        :prop-is-enabled="!isClosing(processing)"
                        prop-element="button"
                        prop-element-size="s"
                        
                        class="w-10 h-10 flex items-center focus-visible:-outline-offset-4"
                    >
                        <VLoading
                            v-show="isClosing(processing)"
                            prop-element-size="s"
                            class="mx-auto"
                        >
                            <span class="sr-only">Deleting reupload message.</span>
                        </VLoading>
                        <FontAwesomeIcon
                            v-show="!isClosing(processing)"
                            icon="fas fa-xmark" class="text-xl mx-auto"
                        />
                    </VActionText>
                </div>
            </TransitionGroup>
        </div>
    </Teleport>
</template>


<script setup lang="ts">
    // import VActionText from '@/components/small/VActionText.vue';
    import VProgressBar from '@/components/small/VProgressBar.vue';
    import VActionText from '@/components/small/VActionText.vue';
    import VActionBorder from '@/components/small/VActionBorder.vue';
    import VLoading from '@/components/small/VLoading.vue';

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
            processing.frontend_processing_state === 'processing_failed' ||
            processing.frontend_processing_state === 'not_found'
        );
    }

    function isStatusOk(processing:AudioClipProcessingDetailsTypes) : boolean {

        return (
            processing.frontend_processing_state === 'ok'
        );
    }

    function isStatusGeneric(processing:AudioClipProcessingDetailsTypes) : boolean {

        return (
            processing.frontend_processing_state === 'processing_pending' ||
            processing.frontend_processing_state === 'processing'
        );
    }

    function determineVProgressBarStep(processing:AudioClipProcessingDetailsTypes) : number|null {

        if(
            processing.frontend_processing_state === 'processing_pending' ||
            processing.frontend_processing_state === 'processing'
        ){

            return 0;

        }else{

            //end
            return null;
        }
    }

    function isClosing(processing:AudioClipProcessingDetailsTypes) : boolean {

        return processing.is_closing;
    }

</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { useAudioClipProcessingsStore } from '@/stores/AudioClipProcessingsStore';
    import { useEventReplyChoicesStore } from '@/stores/EventReplyChoicesStore';
    import { isLoggedIn } from '@/helper_functions';

    export default defineComponent({
        data(){
            return {
                audio_clip_processings_store: useAudioClipProcessingsStore(),
                event_reply_choices_store: useEventReplyChoicesStore(),

                is_logged_in: false,

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
            canShowNotifications() : boolean {

                const current_url = window.location.href;

                return (
                    current_url.includes("login") === false &&
                    current_url.includes("signup") === false &&
                    current_url.includes("start") === false &&
                    current_url.includes("reply") === false &&
                    current_url.includes("event") === false
                );
            },
        },
        methods: {
        },
        beforeMount(){

            this.is_logged_in = isLoggedIn();

            if(this.is_logged_in === true && this.canPoll === true){

                window.setTimeout(async ()=>{

                    //sync store before polling
                    //we use .finally() as we do not prioritise sync's success

                    await this.audio_clip_processings_store.syncProcessingsAPI().finally(()=>{

                        this.audio_clip_processings_store.startPollingProcessings();
                    });

                }, 1000);
            }

            this.audio_clip_processings_store.$onAction(
                ({
                    name, // name of the action
                    args, // array of parameters passed to the action
                    after, // hook after the action returns or resolves
                }) => {

                    if(name === 'updateLastRemovableAudioClipId'){

                        //on every processed audio clip, check if it matches replying event
                        //if true, do softReset()

                        after(()=>{

                            const processed_audio_clip_id = args[0];

                            const processed_audio_clip = this.audio_clip_processings_store.getAudioClipProcessing(
                                processed_audio_clip_id
                            );

                            if(
                                processed_audio_clip === null ||
                                this.event_reply_choices_store.getReplyingEvent === null
                            ){

                                return;
                            }

                            if(processed_audio_clip.event.id === this.event_reply_choices_store.getReplyingEvent.event.id){

                                this.event_reply_choices_store.softReset();
                            }
                        });
                    }
                }
            );
        },
        beforeUnmount(){

            this.audio_clip_processings_store.stopPollingProcessings();
        },
    });

</script>