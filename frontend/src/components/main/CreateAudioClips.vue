<template>
    <div class="w-full flex flex-col">

        <!--min-h allows content to grow, whereas simple h wouldn't, which also wouldn't play nicely with max-h-->
        <!--this is so that transitions don't cause malformed borders-->
        <!--height is sampled from 320px width mobile, with tallest container being the form fields-->
        <div class="w-full min-h-[14.75rem]">
            <TransitionGroupFadeSlow :prop-is-swapping="true">
                <div
                    v-show="canShowForm"
                    class="w-full"
                >
                    <!--fields-->
                    <div
                        spellcheck="false"
                        class="w-full flex flex-col gap-4"
                    >

                        <!--title-->
                        <VTextArea
                            v-if="propIsOriginator === true && isReupload === false"
                            :propIsEnabled="isFormEnabled"
                            :propIsRequired="true"
                            propElementId="audio-clip-name"
                            propLabel="Title"
                            propPlaceholder=""
                            :propMaxLength="40"
                            :propHasTextCounter="true"
                            :propHasStatusText="false"
                            @newValue="handleNewAudioClipName($event)"
                            @wasInteracted="closeAllMenu()"
                        />

                        <!--fields for open/close-->
                        <div class="grid grid-cols-8 gap-2">

                            <!--open/close VRecorderMenu-->
                            <div
                                :class="isReupload ? 'col-span-8' : 'col-span-6'"
                            >
                                <VRecorderField
                                    propLabel="Recording"
                                    :propIsEnabled="isFormEnabled"
                                    :propIsOpen="is_recorder_menu_open"
                                    :propBucketQuantity="bucket_quantity"
                                    :propIsRecording="is_recording"
                                    :propHasRecording="final_blob !== null"
                                    :propAudioVolumePeaks="blob_volume_peaks"
                                    @isOpen="handleIsRecorderMenuOpen($event)"
                                />
                            </div>

                            <!--open/close VAudioClipToneMenu-->
                            <div
                                v-if="isReupload === false"
                                class="col-span-2 relative"
                            >
                                <VAudioClipToneField
                                    propLabel="Tag"
                                    :propIsEnabled="isFormEnabled"
                                    :propAudioClipToneChoice="audio_clip_tone_choice"
                                    :propIsOpen="is_audio_clip_tone_menu_open"
                                    @isOpen="handleIsAudioClipToneMenuOpen($event)"
                                />
                            </div>
                        </div>
                    </div>

                    <!--menus-->
                    <!--must be here on its own, prevents unwanted top-and-bottom gaps if it were in the flexbox above-->
                    <div class="w-full h-fit relative pt-4">

                        <!--arrows, aesthetics only-->
                        <!--uses padding to represent gap above, because there is always only one element, so gap wouldn't work-->
                        <div class="w-full h-0 grid grid-cols-8">
                            <div
                                v-show="is_recorder_menu_open || is_audio_clip_tone_menu_open"
                                :class="[
                                    isReupload ? 'col-span-8' : '',
                                    !isReupload && is_recorder_menu_open ? 'col-span-6 col-start-1 pr-2' : '',
                                    !isReupload && is_audio_clip_tone_menu_open ? 'col-span-2 col-start-7 pl-2' : '',
                                    'relative'
                                ]"
                            >
                                <div
                                    class="z-10 w-2 h-2 absolute -top-1 left-0 right-0 m-auto bg-theme-light border-l-2 border-t-2 border-theme-black rotate-45"
                                ></div>
                            </div>
                        </div>

                        <!--recorder menu-->
                        <div>
                            <VRecorderMenu
                                :propIsOpen="is_recorder_menu_open"
                                :propBucketQuantity="bucket_quantity"
                                :propMaxDurationMs="max_duration_ms"
                                @isRecording="handleIsRecording($event)"
                                @newRecording="handleNewRecording($event)"
                                class="border-2 border-theme-black rounded-lg p-4"
                            />
                        </div>

                        <!--audio_clip_tone menu-->
                        <div :class="is_audio_clip_tone_menu_open ? 'border-2 border-theme-black rounded-lg p-4' : ''">
                            <VAudioClipToneMenu
                                :propIsOpen="is_audio_clip_tone_menu_open"
                                :propMustTrackSelectedOption="true"
                                @audioClipToneSelected="handleAudioClipToneSelected($event)"
                            />
                        </div>
                    </div>

                    <!--submit-->
                    <!--sibling above already has padding, so only need pt-4 here to achieve pt-8-->
                    <!--when sibling above is open, have full padding here-->
                    <div
                        :class="[
                            isAnyMenuOpen ? 'pt-8' : 'pt-4',
                            'w-full relative'
                        ]"
                    >
                        <div
                            class="w-full flex flex-col gap-2"
                        >
                            <VActionSpecial
                                @click.stop="doSubmit()"
                                :propIsEnabled="canSubmit || canReupload"
                                propElement="button"
                                type="button"
                                propElementSize="l"
                                propFontSize="l"
                                class="w-full"
                            >
                                <span class="mx-auto">
                                    {{ getIdleSubmitText }}
                                </span>
                            </VActionSpecial>
                        </div>
                    </div>
                </div>

                <!--submitting-->
                <div
                    v-show="canShowSubmitting"
                    class="w-full flex flex-col"
                >
                    <span class="mx-auto pb-1 text-xl font-medium">
                        {{ getSubmittingLoadingText }}
                    </span>
                    <VProgressBar
                        :prop-timestamps-ms="progress_bar_timestamps_ms"
                        :prop-step="progress_bar_step"
                        class="w-3/4 mx-auto"
                    />
                </div>

                <!--processing-->
                <VDialogPlain
                    v-show="canShowProcessingDialog"
                    :prop-has-border="false"
                    :prop-has-auto-space-logo="false"
                    :prop-has-auto-space-title="false"
                    :prop-has-auto-space-content="false"
                    class="w-full"
                >
                    <template #logo>
                        <span
                            v-if="audio_clip_tone_choice !== null"
                            class="text-xl animate-spin"
                        >
                            {{ audio_clip_tone_choice!.audio_clip_tone_symbol }}
                        </span>
                    </template>
                    <template #title>
                        <span>Processing recording...</span>
                    </template>
                    <template #content>
                        <span>
                            This may take a minute.
                            <br>
                            Explore other content while waiting!
                        </span>
                        <div class="pt-2">
                            <VActionBorder
                                prop-element="a"
                                prop-element-size="s"
                                prop-font-size="s"
                                :prop-is-icon-only="true"
                                href="/"
                                class="w-fit mx-auto"
                            >
                                <span class="flex items-center px-4">
                                    <span class="block pb-0.5">Back to main page</span>
                                    <FontAwesomeIcon icon="fas fa-arrow-right" class="text-lg pl-2"/>
                                </span>
                            </VActionBorder>
                        </div>
                    </template>
                </VDialogPlain>

                <VDialogPlain
                    v-show="canShowUnavailableDialog"
                    :prop-has-border="false"
                    :prop-has-auto-space-logo="false"
                    :prop-has-auto-space-title="false"
                    :prop-has-auto-space-content="false"
                    class="w-full"
                >
                    <template #logo>
                        <FontAwesomeIcon icon="far fa-face-frown" class="text-2xl"/>
                    </template>
                    <template #title>
                        <span>Recording unavailable.</span>
                    </template>
                    <template #content>
                        <span>
                            Either you've reached the maximum processing attempts, or it's been overdue.
                        </span>
                        <div class="pt-2">
                            <VActionBorder
                                prop-element="a"
                                prop-element-size="s"
                                prop-font-size="s"
                                :prop-is-icon-only="true"
                                href="/"
                                class="w-fit mx-auto"
                            >
                                <span class="flex items-center px-4">
                                    <span class="block pb-0.5">Back to main page</span>
                                    <FontAwesomeIcon icon="fas fa-arrow-right" class="text-lg pl-2"/>
                                </span>
                            </VActionBorder>
                        </div>
                    </template>
                </VDialogPlain>
            </TransitionGroupFadeSlow>
        </div>
    </div>
</template>


<script setup lang="ts">
    import VActionSpecial from '../small/VActionSpecial.vue';
    import VTextArea from '../small/VTextArea.vue';
    import VActionBorder from '../small/VActionBorder.vue';
    import VAudioClipToneField from '../medium/VAudioClipToneField.vue';
    import VAudioClipToneMenu from '../medium/VAudioClipToneMenu.vue';
    import VRecorderField from '../medium/VRecorderField.vue';
    import VRecorderMenu from '../medium/VRecorderMenu.vue';
    import VProgressBar from '../small/VProgressBar.vue';
    import VDialogPlain from '../small/VDialogPlain.vue';
    import TransitionGroupFadeSlow from '@/transitions/TransitionGroupFadeSlow.vue';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faArrowRight } from '@fortawesome/free-solid-svg-icons/faArrowRight';
    import { faFaceFrown } from '@fortawesome/free-regular-svg-icons/faFaceFrown';

    library.add(faArrowRight, faFaceFrown);
</script>

<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import AudioClipTonesTypes from '@/types/AudioClipTones.interface';
    import { notify } from '@/wrappers/notify_wrapper';
    // import { CreateAudioClips__isSubmitSuccessfulTypes } from '@/types/General.interface';
    import AWSPresignedPostURLTypes from '@/types/AWSPresignedPostURL.interface';
    import { useAudioClipProcessingsStore } from '@/stores/AudioClipProcessingsStore';
    const axios = require('axios');

    export default defineComponent({
        data() {
            return {
                audio_clip_processings_store: useAudioClipProcessingsStore(),

                event_name: "",

                //updates only from _Field to _Menu
                is_audio_clip_tone_menu_open: false,
                is_recorder_menu_open: false,

                audio_clip_tone_choice: null as AudioClipTonesTypes|null,

                is_recording: false,
                final_blob: null as Blob|null,
                blob_duration: 0,
                blob_volume_peaks: [] as number[],
                bucket_quantity: 20,
                // propMaxDuration: (1000 * 60 * 2) + 500,    //2m + 0.5s, as final_blob is always +-0.1s away
                max_duration_ms: 120500,    //2m + 0.5s, as final_blob is always +-0.1s away
                recorded_file_extension: 'webm',

                //data received and/or used for submits
                submit_upload_url: '',
                submit_upload_fields: null as AWSPresignedPostURLTypes|null,
                submit_event_id: null as number|null,
                submit_audio_clip_id: null as number|null,

                is_submitting: false,
                show_processing_dialog: false,
                show_unavailable_dialog: false,
                warn_before_unload: false,

                //VProgressBar
                progress_bar_step: null as number|null,
                progress_bar_timestamps_ms: {
                    durations: [6000, 14000],
                    scales: [0.35, 1],
                },

                //track step progress
                submit_steps_done: {
                    backend_upload: false,
                    aws_upload: false,
                },
            };
        },
        props: {
            propReuploadAudioClipId: {
                type: Number as PropType<Number|null>,
                required: false,
                default: null
            },
            propIsOriginator: {
                type: Boolean,
                required: true,
                default: true
            },
            propEventId: {
                type: Number,
                required: false,
                default: null
            },
            propCanSubmit: {    //used to disallow submit, e.g. when parent is deleting and loading
                type: Boolean,
                default: true
            },
        },
        emits: ['isSubmitting', 'isSubmitSuccessful', 'hasForm', 'newLambdaAttemptsLeft',],
        watch: {
            is_submitting(new_value){

                this.$emit('isSubmitting', new_value);
            },
            is_audio_clip_tone_menu_open(new_value){

                if(new_value === true && this.is_recorder_menu_open === true){

                    this.is_recorder_menu_open = false;
                }
            },
            is_recorder_menu_open(new_value){
                
                if(new_value === true && this.is_audio_clip_tone_menu_open === true){

                    this.is_audio_clip_tone_menu_open = false;
                }
            },
            isFormEnabled(new_value){

                this.$emit('hasForm', new_value);
            },
        },
        computed: {
            isReupload() : boolean {

                return this.propReuploadAudioClipId !== null;
            },
            getIdleSubmitText() : string {

                if(this.isReupload === true){

                    return 'Reupload';
                }

                if(this.propIsOriginator === true){

                    return 'Start event';

                }else{

                    return 'Create reply';
                }
            },
            getSubmittingLoadingText() : string {

                if(this.isReupload === true){

                    return 'Reuploading...';
                }

                if(this.propIsOriginator === true){

                    return 'Starting event...';

                }else{

                    return 'Creating reply...';
                }
            },
            getSubmitDoneText() : string {

                if(this.isReupload === true){

                    return 'Reuploaded recording.';
                }

                if(this.propIsOriginator === true){

                    return 'Started event.';

                }else{

                    return 'Created reply.';
                }
            },
            isAnyMenuOpen() : boolean {

                return this.is_recorder_menu_open === true || this.is_audio_clip_tone_menu_open === true;
            },
            canSubmit() : boolean {

                if(
                    this.isReupload === false &&
                    this.propCanSubmit === true &&
                    this.is_submitting === false &&
                    (
                        (this.propIsOriginator === true && this.event_name.trim() !== '') ||
                        (this.propIsOriginator === false && this.propEventId !== null)
                    ) &&
                    this.audio_clip_tone_choice !== null &&
                    this.is_recording === false &&
                    this.final_blob !== null &&
                    this.blob_volume_peaks.length === this.bucket_quantity &&
                    this.blob_duration > 0
                ){

                    return true;
                }

                //don't do show_has_empty_field_error here because it should only show on submit attempt
                return false;
            },
            canReupload() : boolean {
                if(
                    this.isReupload === true &&
                    this.propCanSubmit === true &&
                    this.is_submitting === false &&
                    this.is_recording === false &&
                    this.final_blob !== null &&
                    this.blob_volume_peaks.length === this.bucket_quantity &&
                    this.blob_duration > 0
                ){

                    return true;
                }

                return false;
            },
            isFormEnabled() : boolean {

                return this.is_submitting === false;
            },
            canShowForm() : boolean {

                return (
                    this.is_submitting === false &&
                    this.show_processing_dialog === false &&
                    this.show_unavailable_dialog === false
                );
            },
            canShowSubmitting() : boolean {

                return (
                    this.is_submitting === true &&
                    this.show_processing_dialog === false &&
                    this.show_unavailable_dialog === false
                );
            },
            canShowProcessingDialog() : boolean {

                return (
                    this.is_submitting === false &&
                    this.show_processing_dialog === true &&
                    this.show_unavailable_dialog === false &&
                    this.audio_clip_tone_choice !== null
                );
            },
            canShowUnavailableDialog() : boolean {

                return (
                    this.is_submitting === false &&
                    this.show_processing_dialog === false &&
                    this.show_unavailable_dialog === true
                );
            },
            hasDialog() : boolean {

                //this is used to help parent hide any text
                //helps to not overwhelm the user with text
                return (
                    this.show_processing_dialog === true ||
                    this.show_unavailable_dialog === true
                );
            },
        },
        methods: {
            handleIsRecording(new_value:boolean) : void {

                this.is_recording = new_value;
            },
            closeAllMenu() : void {

                this.is_recorder_menu_open = false;
                this.is_audio_clip_tone_menu_open = false;
            },
            notifyGenericFailure(error_text:string) : void {

                notify({
                    type: 'error',
                    title: 'Error',
                    text: error_text,
                    icon: {'font_awesome': 'fas fa-exclamation'},
                }, 4000);

            },
            reuploadSetup() : void {

                if(this.isReupload === false){

                    return;
                }

                //see if reupload_audio_clip_id exists in template
                //we separate .getAttribute() and JSON.parse() data to avoid TS variable nightmare

                //get data from SSR template
                const container = (document.getElementById('data-container-get-events') as HTMLElement);

                if(container === null){

                    throw new Error('Container was not found in template.');
                }

                const container_data = {
                    audio_clip_id: this.propReuploadAudioClipId,
                    audio_clip_tone_id: container.getAttribute('data-reupload-audio-clip-tone-id'),
                    audio_clip_tone_name: container.getAttribute('data-reupload-audio-clip-tone-name'),
                    audio_clip_tone_slug: container.getAttribute('data-reupload-audio-clip-tone-slug'),
                    audio_clip_tone_symbol: container.getAttribute('data-reupload-audio-clip-tone-symbol'),
                    event_id: container.getAttribute('data-event-id'),
                    event_name: document.getElementById('event-name'),
                }

                for(const [key, value] of Object.entries(container_data)){

                    if(value === null){

                        //missing data neede for reupload
                        throw new Error('Missing required data from template: ' + key);
                    }
                }

                const valid_data = {
                    audio_clip_id: this.propReuploadAudioClipId,
                    audio_clip_tone_id: JSON.parse(container_data['audio_clip_tone_id']!) as number,
                    audio_clip_tone_name: container_data['audio_clip_tone_name']! as string,
                    audio_clip_tone_slug: container_data['audio_clip_tone_slug']! as string,
                    audio_clip_tone_symbol: container_data['audio_clip_tone_symbol']! as string,
                    event_id: JSON.parse(container_data['event_id']!) as number,
                    event_name: container_data['event_name']!.textContent! as string,
                };

                //restore values to this component

                //only need this to remake new processing, if it suddenly does not exist on submit
                this.audio_clip_tone_choice = {
                    id: valid_data['audio_clip_tone_id'],
                    audio_clip_tone_name: valid_data['audio_clip_tone_name'],
                    audio_clip_tone_slug: valid_data['audio_clip_tone_slug'],
                    audio_clip_tone_symbol: valid_data['audio_clip_tone_symbol'],
                };

                this.submit_event_id = valid_data['event_id'];

                //if prop is Number, TS complains when variable is number
                this.submit_audio_clip_id = Number(this.propReuploadAudioClipId);

                //prepare this step to be skipped
                this.submit_steps_done.backend_upload = true;

                const target_audio_clip_processing = this.audio_clip_processings_store.getAudioClipProcessing(
                    this.submit_audio_clip_id
                );

                if(
                    target_audio_clip_processing === null
                ){

                    //do not create record in store if it doesn't exist
                    //we only create when processing
                    return;
                }

                //sync attempts
                this.$emit(
                    'newLambdaAttemptsLeft',
                    target_audio_clip_processing.lambda_attempts_left
                );
            },
            async uploadToBackendReceiveS3UploadURL() : Promise<void> {

                //step 1
                //submit form and receive AWS URL for file upload

                if(this.submit_steps_done.backend_upload === true){

                    return;
                }

                //prepare form and URL
                let data = new FormData();
                let post_url = window.location.origin + '/api/events';

                data.append(
                    'audio_clip_tone_id',
                    JSON.stringify((this.audio_clip_tone_choice as AudioClipTonesTypes)['id'])
                );
                data.append('recorded_file_extension', this.recorded_file_extension);

                //adjust form fields and URL for propIsOriginator context

                if(this.propIsOriginator === true){

                    data.append('event_name', this.event_name);
                    post_url += '/create';

                }else{

                    data.append('event_id', JSON.stringify(this.propEventId));
                    post_url += '/replies/create';
                }

                post_url += '/upload';

                //submit
                await axios.post(
                    post_url,
                    data,
                ).then((result:any) => {

                    //when first time submit, 201
                    //for replies, subsequent submits, 200

                    if(result.status !== 200 && result.status !== 201){

                        throw new Error('Unexpected status code.');
                    }

                    //ok

                    this.submit_upload_url = result.data['upload_url'] as string;
                    this.submit_upload_fields = JSON.parse(result.data['upload_fields']) as AWSPresignedPostURLTypes;
                    this.submit_audio_clip_id = result.data['audio_clip_id'] as number;

                    if(this.propIsOriginator === true){

                        this.submit_event_id = result.data['event_id'] as number;
                    }

                    this.submit_steps_done.backend_upload = true;

                }).catch((error:any) => {

                    let error_text = '';

                    if(
                        Object.hasOwn(error, 'request') === true &&
                        Object.hasOwn(error, 'response') === true &&
                        Object.hasOwn(error.response.data, 'message') === true
                    ){

                        error_text = error.response.data['message'];
                    }

                    //only check originator here
                    //responder reply limit is enforced at "choices"
                    if(Object.hasOwn(error.response.data, 'event_create_daily_limit_reached') === true){

                        //create limit reached
                        notify({
                            type: 'generic',
                            title: 'Creation limit reached',
                            text: error_text,
                            icon: {'font_awesome': 'fas fa-battery-empty'},
                        }, 4000);

                        return;
                    }

                    this.notifyGenericFailure(error_text);
                });
            },
            async uploadToS3() : Promise<void> {

                //step 2
                //upload to AWS

                if(this.submit_steps_done.aws_upload === false){

                    //check
                    if(
                        this.submit_upload_url === null ||
                        this.submit_upload_fields === null ||
                        this.final_blob === null
                    ){

                        throw new Error('Unexpected null');
                    }

                    let data = new FormData();

                    //add upload_fields as form data
                    for(const key_name in this.submit_upload_fields){

                        data.append(
                            key_name,
                            this.submit_upload_fields[key_name as keyof AWSPresignedPostURLTypes] as string
                        );
                    }

                    //add file as last field, as required by AWS
                    //must be last field
                    data.append('file', this.final_blob as Blob);

                    //submit
                    //be sure to enable at bucket's CORS policy
                    await axios.post(
                        this.submit_upload_url,
                        data,
                        {
                            headers: {
                                "Access-Control-Allow-Origin": "*",
                            },
                        },
                    ).then(() => {

                        //AWS S3 is tested to always return 204, regardless of whether file already exists
                        //however, it feels safer to not specify 204, as there are no docs on this
                        //doc from RedHat's "S3 common response status codes" mentions 200/201/202/204/206

                        //ok
                        this.submit_steps_done.aws_upload = true;

                    }).catch((error:any)=>{

                        console.log(error.response);

                        //due to possible retries in a single action, don't notify here
                        return;
                    });
                }
            },
            async regenerateS3UploadURL() : Promise<boolean> {

                //backend upload already returns AWS upload URL
                //this is only used if original AWS upload URL expires

                if(this.submit_audio_clip_id === null){

                    throw new Error('Unexpected null.');
                }

                //prepare URL
                let post_url = window.location.origin + '/api/events';

                if(this.propIsOriginator === true){

                    post_url += '/create';

                }else{

                    post_url += '/replies/create';
                }

                post_url += '/upload/regenerate-url';

                //prepare data
                let data = new FormData();
                data.append('audio_clip_id', JSON.stringify(this.submit_audio_clip_id));

                let is_success = true;

                //get new upload URL
                await axios.post(
                    post_url,
                    data
                ).then((result:any)=>{

                    if(result.status !== 200){

                        throw new Error('Unexpected status code.');
                    }

                    //ok
                    //update AWS upload info
                    this.submit_upload_url = result.data['upload_url'] as string;
                    this.submit_upload_fields = JSON.parse(result.data['upload_fields']) as AWSPresignedPostURLTypes;

                }).catch((error:any)=>{

                    if(
                        Object.hasOwn(error, 'request') === true &&
                        Object.hasOwn(error, 'response') === true &&
                        Object.hasOwn(error.response.data, 'message') === true
                    ){

                        this.notifyGenericFailure(error.response.data['message']);
                    }

                    is_success = false;
                });

                return is_success;
            },
            handleAudioClipProcessingStatus() : void {

                //always reset
                this.show_processing_dialog = false;
                this.show_unavailable_dialog = false;

                if(this.submit_audio_clip_id === null){

                    return;
                }

                const target_audio_clip_processing = this.audio_clip_processings_store.getAudioClipProcessing(
                    this.submit_audio_clip_id
                );

                if(target_audio_clip_processing === null){

                    if(this.isReupload === false){

                        //if null, then another tab must've done notify() and user had closed it
                        //when not at reupload page, redirecting sounds better than leaving the user hanging

                        window.location.replace(
                            window.location.origin +
                            "/event/" + this.submit_event_id!.toString()
                        );

                    }

                    return;
                }

                switch(target_audio_clip_processing.status){

                    case 'processed':

                        //success, redirect

                        window.location.replace(
                            window.location.origin +
                            "/event/" + this.submit_event_id!.toString()
                        );

                        break;

                    case 'processing':{

                        //create interval here

                        this.show_processing_dialog = true;
                        let has_api_call = false;

                        const processing_interval = window.setInterval(async ()=>{

                            //no need for new interval while a request is still running
                            if(has_api_call === true){

                                return;
                            }

                            has_api_call = true;

                            //exit condition, this won't be expected to occur
                            if(this.submit_audio_clip_id === null){

                                window.clearInterval(processing_interval);
                                return;
                            }

                            const target_audio_clip_processing = this.audio_clip_processings_store.getAudioClipProcessing(
                                this.submit_audio_clip_id
                            );

                            //exit condition
                            if(
                                target_audio_clip_processing === null ||
                                target_audio_clip_processing.status !== 'processing'
                            ){

                                window.clearInterval(processing_interval);
                                this.handleAudioClipProcessingStatus();
                                return;
                            }

                            //api call, basically polling
                            await this.audio_clip_processings_store.processAudioClipAPI(
                                'user_submit',
                                this.submit_audio_clip_id!,
                            ).finally(()=>{
                                has_api_call = false;
                            });

                        }, 5000);

                        break;
                    }

                    case 'lambda_error':

                        //update attempts left
                        //if user is not at reupload page, redirect

                        if(this.isReupload === false){

                            window.location.replace(
                                window.location.origin +
                                "/event/" + this.submit_event_id!.toString() +
                                "?reupload=" + this.submit_audio_clip_id!.toString()
                            );

                            break;
                        }

                        //sync attempts
                        this.$emit(
                            'newLambdaAttemptsLeft',
                            target_audio_clip_processing.lambda_attempts_left
                        );

                        //server can return until 0 attempts left
                        //no need to allow user to reupload if at 0, as server won't process at that point
                        if(
                            target_audio_clip_processing.lambda_attempts_left === null ||
                            target_audio_clip_processing.lambda_attempts_left === 0
                        ){

                            this.show_unavailable_dialog = true;

                            break;
                        }

                        break;

                    case 'not_found':

                        //no longer available

                        this.show_unavailable_dialog = true;

                        break;

                    case 'error':

                        //generic error

                        notify({
                            type: 'error',
                            title: 'Recording error',
                            text: 'Try again later.',
                            icon: {'font_awesome': 'fas fa-exclamation'},
                        }, 4000);

                        break;

                    default:

                        break;
                }

            },
            async doSubmit() : Promise<void> {

                if(this.canSubmit === false && this.canReupload === false){

                    return;
                }

                this.warn_before_unload = true;
                this.is_submitting = true;
                this.progress_bar_step = 0;
                this.$emit('isSubmitting', true);

                //close menus
                this.is_recorder_menu_open = false;
                this.is_audio_clip_tone_menu_open = false;

                try{

                    //if never uploaded to backend
                    if(this.submit_steps_done.backend_upload === false){

                        await this.uploadToBackendReceiveS3UploadURL();
                    }

                    //if still false, stop here
                    if(this.submit_steps_done.backend_upload === false){

                        return;
                    }

                    //expect this from backend_upload, or template if for reupload
                    if(this.submit_audio_clip_id === null){

                        this.progress_bar_step = null;
                        throw new Error('Unexpected null.');
                    }

                    this.progress_bar_step = 1;

                    //if never uploaded to S3 yet
                    //and if backend_upload was not skipped, i.e. has AWS data
                    if(
                        this.submit_steps_done.aws_upload === false &&
                        this.submit_upload_url !== '' &&
                        this.submit_upload_fields !== null
                    ){

                        await this.uploadToS3();
                    }

                    //if still not uploaded, try regenerating URL once, and try again
                    if(this.submit_steps_done.aws_upload === false){

                        const has_new_s3_url = await this.regenerateS3UploadURL();

                        if(has_new_s3_url === false){

                            return;
                        }

                        await this.uploadToS3();
                    }

                    //if after 1 retry and still not uploaded to S3, stop here
                    if(this.submit_steps_done.aws_upload === false){

                        this.notifyGenericFailure(
                            'Unable to ' + this.getIdleSubmitText.toLowerCase() + '.'
                        );
                        return;
                    }

                    //prepare event_name if it's supposed to already exist
                    if(this.event_name.trim() === ''){

                        const event_name = document.getElementById('event-name');

                        if(event_name === null || event_name.textContent === null){

                            throw new Error('Missing data.');
                        }

                        this.event_name = event_name.textContent;
                    }

                    //ensure these data exist
                    if(
                        this.submit_event_id === null ||
                        this.audio_clip_tone_choice === null
                    ){

                        throw new Error('Missing data.');
                    }

                    //store if first time
                    if(
                        Object.hasOwn(
                            this.audio_clip_processings_store.getAudioClipProcessings,
                            this.submit_audio_clip_id
                        ) === false
                    ){

                        this.audio_clip_processings_store.storeAudioClipProcessing(
                            this.propIsOriginator,
                            this.submit_audio_clip_id,
                            {
                                id: this.submit_event_id,
                                event_name: this.event_name,
                            },
                            this.audio_clip_tone_choice,
                        );
                    }

                    //finalise
                    this.progress_bar_step = null;
                    this.show_processing_dialog = true;
                    this.$emit('isSubmitSuccessful', true);

                    //call processing API
                    //handling success/error is only important if user is still on the same page

                    //set this early, as next API may immediately redirect
                    this.warn_before_unload = false;

                    await this.audio_clip_processings_store.processAudioClipAPI(
                        'user_submit',
                        this.submit_audio_clip_id
                    ).catch(()=>{

                        return;
                    });

                    //reflect UI to status
                    this.handleAudioClipProcessingStatus();

                }finally{

                    this.$emit('isSubmitting', false);
                    this.progress_bar_step = null;
                    this.is_submitting = false;
                    this.warn_before_unload = false;
                }
            },
            handleNewRecording(new_value:{'blob':Blob, 'blob_duration':number, 'blob_volume_peaks':number[]}) : void {

                this.final_blob = new_value['blob'];
                this.blob_duration = new_value['blob_duration'];
                this.blob_volume_peaks = new_value['blob_volume_peaks'];
            },
            handleIsRecorderMenuOpen(new_value:boolean) : void {

                this.is_recorder_menu_open = new_value;
            },
            handleAudioClipToneSelected(new_value:AudioClipTonesTypes|null) : void {

                this.is_audio_clip_tone_menu_open = false;
                this.audio_clip_tone_choice = new_value;
            },
            handleIsAudioClipToneMenuOpen(new_value:boolean) : void {

                this.is_audio_clip_tone_menu_open = new_value;
            },
            handleNewAudioClipName(new_value:string) : void {

                this.event_name = new_value;
            },
            handleBeforeUnload(event:BeforeUnloadEvent) : void {

                if(this.warn_before_unload === true){

                    //this is only effective when user has interacted with page
                    //e.g. if user opens tab and immediately closes, without scrolling, tab simply closes
                    event.preventDefault();
                }
            },
        },
        beforeMount(){

            this.reuploadSetup();

            window.addEventListener('beforeunload', this.handleBeforeUnload);
        },
        mounted(){

            this.handleAudioClipProcessingStatus();

        },
        beforeUnmount(){

            window.removeEventListener('beforeunload', this.handleBeforeUnload);
        },
    });
</script>



