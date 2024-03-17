<template>
    <div
        class="w-full flex flex-col"
    >
        <div
            spellcheck="false"
            class="w-full flex flex-col gap-4"
        >
            <!--reupload banner-->
            <span v-if="is_reupload === true" class="text-red-700 text-base border border-red-700 p-2">
                Your previous recording could not be processed. You may reupload.
            </span>

            <!--title-->
            <VTextArea
                v-if="propIsOriginator === true && is_reupload === false"
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
                <div class="col-span-6">
                    <VRecorderField
                        propLabel="Recording"
                        :propIsOpen="is_recorder_menu_open"
                        :propBucketQuantity="bucket_quantity"
                        :propHasRecording="final_blob !== null"
                        :propAudioVolumePeaks="blob_volume_peaks"
                        @isOpen="handleIsRecorderMenuOpen($event)"
                    />
                </div>

                <!--open/close VAudioClipToneMenu-->
                <div class="col-span-2 relative">
                    <VAudioClipToneField
                        v-if="is_reupload === false"
                        propLabel="Tag"
                        :propIsEnabled="!is_reupload"
                        :propAudioClipToneChoice="audio_clip_tone_choice"
                        :propIsOpen="is_audio_clip_tone_menu_open"
                        @isOpen="handleIsAudioClipToneMenuOpen($event)"
                    />
                    <div
                        v-else-if="is_reupload === true && audio_clip_tone_choice !== null"
                        class="w-full h-20 text-3xl absolute bottom-0 flex items-center"
                    >
                        <span class="sr-only">
                            {{audio_clip_tone_choice.audio_clip_tone_name}}, cannot be changed during reupload
                        </span>
                        <span class="mx-auto">
                            {{ audio_clip_tone_choice.audio_clip_tone_symbol }}
                        </span>
                    </div>
                </div>
            </div>
        </div>

        <!--menus-->
        <!--must be here on its own, prevents unwanted top-and-bottom gaps if it were in the flexbox above-->
        <div
            class="w-full h-fit relative pt-4"
        >

            <!--arrows, aesthetics only-->
            <!--uses padding to represent gap above, because there is always only one element, so gap wouldn't work-->
            <div class="w-full h-0 grid grid-cols-8">
                <div
                    v-show="is_recorder_menu_open || is_audio_clip_tone_menu_open"
                    :class="[
                        is_recorder_menu_open ? 'col-span-6 col-start-1 pr-2' : '',
                        is_audio_clip_tone_menu_open ? 'col-span-2 col-start-7 pl-2' : '',
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

        <!--submit and progress bar-->
        <!--sibling above already has padding, so only need pt-4 here to achieve pt-8-->
        <!--when sibling above is open, have full padding here-->
        <div
            :class="[
                isAnyMenuOpen ? 'pt-8' : 'pt-4',
                'w-full relative'
            ]"
        >
            <TransitionGroupFade :prop-has-absolute="true">
                <!--submit-->
                <div
                    v-show="!is_submitting"
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
                            {{ getIdleSubmitButtonText }}
                        </span>
                    </VActionSpecial>
                </div>

                <!--submitting-->
                <div
                    v-show="is_submitting"
                    class="w-full flex items-center"
                >
                    <VProgressBar
                        :prop-timestamps-ms="progress_bar_timestamps_ms"
                        :prop-step="progress_bar_step"
                        class="mx-auto"
                    >
                        <VLoading
                            prop-element-size="m"
                        >
                            <span class="pl-2 pb-1 text-2xl font-medium">
                                {{ getSubmittingLoadingText }}
                            </span>
                        </VLoading>
                    </VProgressBar>
                </div>
            </TransitionGroupFade>
        </div>
    </div>
</template>


<script setup lang="ts">
    import VActionSpecial from '../small/VActionSpecial.vue';
    import VTextArea from '../small/VTextArea.vue';
    import VAudioClipToneField from '../medium/VAudioClipToneField.vue';
    import VAudioClipToneMenu from '../medium/VAudioClipToneMenu.vue';
    import VRecorderField from '../medium/VRecorderField.vue';
    import VRecorderMenu from '../medium/VRecorderMenu.vue';
    import VProgressBar from '../small/VProgressBar.vue';
    import VLoading from '../small/VLoading.vue';
    import TransitionGroupFade from '@/transitions/TransitionGroupFade.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import AudioClipTonesTypes from '@/types/AudioClipTones.interface';
    import { notify } from 'notiwind';
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

                is_reupload: false,
                is_submitting: false,

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
        emits: ['isSubmitting', 'isSubmitSuccessful'],
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
        },
        computed: {
            getIdleSubmitButtonText() : string {

                if(this.is_reupload === true){

                    return 'Reupload';
                }

                if(this.propIsOriginator === true){

                    return 'Start event';

                }else{

                    return 'Create reply';
                }
            },
            getSubmittingLoadingText() : string {

                if(this.is_reupload === true){

                    return 'Reuploading...';
                }

                if(this.propIsOriginator === true){

                    return 'Starting event...';

                }else{

                    return 'Creating reply...';
                }
            },
            isAnyMenuOpen() : boolean {

                return this.is_recorder_menu_open === true || this.is_audio_clip_tone_menu_open === true;
            },
            canSubmit() : boolean {

                if(
                    this.is_reupload === false &&
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
                    this.is_reupload === true &&
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
                    title: "Error",
                    text: error_text,
                    type: "error"
                }, 4000);
            },
            handleIsReupload() : void {

                //check if URL has get param
                const current_url = new URL(window.location.href);
                const reupload_audio_clip_id_from_url = current_url.searchParams.get('reupload');

                if(reupload_audio_clip_id_from_url === null){

                    return;
                }

                //see if reupload_audio_clip_id exists in template
                //we separate .getAttribute() and JSON.parse() data to avoid TS variable nightmare

                //get data from SSR template
                const container = (document.getElementById('data-container-get-events') as HTMLElement);

                if(container === null){

                    throw new Error('container was not found in template.');
                }

                const container_data = {
                    audio_clip_id: container.getAttribute('data-reupload-audio-clip-id'),
                    audio_clip_tone_id: container.getAttribute('data-reupload-audio-clip-tone-id'),
                    audio_clip_tone_name: container.getAttribute('data-reupload-audio-clip-tone-name'),
                    audio_clip_tone_slug: container.getAttribute('data-reupload-audio-clip-tone-slug'),
                    audio_clip_tone_symbol: container.getAttribute('data-reupload-audio-clip-tone-symbol'),
                    event_id: container.getAttribute('data-event-id'),
                    event_name: document.getElementById('event-name'),
                }

                if(
                    container_data['audio_clip_id'] === null ||
                    Number(reupload_audio_clip_id_from_url) !== JSON.parse(container_data['audio_clip_id']) as number
                ){

                    //not reupload
                    return;
                }

                this.is_reupload = true;

                for(const value of Object.values(container_data)){

                    if(value === null){

                        //missing data neede for reupload
                        throw new Error('Missing required data from template.');
                    }
                }

                const valid_data = {
                    audio_clip_id: JSON.parse(container_data['audio_clip_id']!) as number,
                    audio_clip_tone_id: JSON.parse(container_data['audio_clip_tone_id']!) as number,
                    audio_clip_tone_name: JSON.parse(container_data['audio_clip_tone_name']!) as string,
                    audio_clip_tone_slug: JSON.parse(container_data['audio_clip_tone_slug']!) as string,
                    audio_clip_tone_symbol: JSON.parse(container_data['audio_clip_tone_symbol']!) as string,
                    event_id: JSON.parse(container_data['event_id']!) as number,
                    event_name: JSON.parse(container_data['event_name']!.textContent!) as string,
                };

                //sync values to this component
                this.audio_clip_tone_choice = {
                    id: valid_data['audio_clip_tone_id'],
                    audio_clip_tone_name: valid_data['audio_clip_tone_name'],
                    audio_clip_tone_slug: valid_data['audio_clip_tone_slug'],
                    audio_clip_tone_symbol: valid_data['audio_clip_tone_symbol'],
                };
                this.submit_event_id = valid_data['event_id'];
                this.submit_audio_clip_id = valid_data['audio_clip_id'];

                //check if reupload_audio_clip_id exists in AudioClipProcessingsStore

                const current_audio_clip_processing = this.audio_clip_processings_store.getAudioClipProcessing(
                    valid_data['audio_clip_id']
                );

                if(current_audio_clip_processing === null){

                    //create new record in store
                    this.audio_clip_processings_store.storeAudioClipProcessing(
                        this.propIsOriginator,
                        valid_data['audio_clip_id'],
                        {
                            event_id: valid_data['event_id'],
                            event_name: valid_data['event_name'],
                        },
                        this.audio_clip_tone_choice,
                        null
                    );

                }else{

                    //when record already exists in store, it will also have recording
                    //restore recording

                    this.final_blob = current_audio_clip_processing.recording!.final_blob;
                    this.blob_duration = current_audio_clip_processing.recording!.blob_duration;
                    this.blob_volume_peaks = current_audio_clip_processing.recording!.blob_volume_peaks;
                }

                //restore fake (disabled) audio_clip_tone in form
                //because it cannot be changed

                //skip this step
                this.submit_steps_done.backend_upload = true;

                //
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
                            icon: "fas fa-battery-empty",
                            title: 'Creation limit reached',
                            text: error_text,
                            type: "generic"
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
                    await axios.post(
                        this.submit_upload_url,
                        data,
                    ).then(() => {

                        //AWS S3 is tested to always return 204, regardless of whether file already exists
                        //however, it feels safer to not specify 204, as there are no docs on this
                        //doc from RedHat's "S3 common response status codes" mentions 200/201/202/204/206

                        //ok
                        this.submit_steps_done.aws_upload = true;

                    }).catch(()=>{

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
            async doSubmit() : Promise<void> {

                if(this.canSubmit === false){

                    return;
                }

                this.is_submitting = true;

                this.progress_bar_step = 0;

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
                            'Unable to ' + this.getIdleSubmitButtonText.toLowerCase() + '.'
                        );
                        return;
                    }

                    //start processing immediately, don't wait
                    this.audio_clip_processings_store.processAudioClipAPI(this.submit_audio_clip_id);

                    //show "we will alert you when it's done" dialog

                }finally{

                    this.progress_bar_step = null;
                    this.is_submitting = false;
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
        },
        beforeMount(){

            this.handleIsReupload();
        },
    });
</script>



