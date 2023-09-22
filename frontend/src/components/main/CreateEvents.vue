<template>
    <div
        spellcheck="false"
        class="bg-theme-light text-theme-black flex flex-col gap-4"
    >
        <!--title-->
        <VTextArea
            v-if="propIsOriginator === true"
            :propIsRequired="true"
            propElementId="event-name"
            propLabel="Title"
            propPlaceholder=""
            :propMaxLength="40"
            :propHasTextCounter="true"
            :propHasStatusText="false"
            @newValue="handleNewEventName($event)"
            @wasInteracted="closeAllMenu()"
        />

        <!--fields for open/close-->
        <div class="grid grid-cols-8 gap-2">

            <!--open/close VRecorderMenu-->
            <div ref="recorder_field" class="col-span-6">
                <VRecorderField
                    propLabel="Voice"
                    :propIsOpen="is_recorder_menu_open"
                    :propBucketQuantity="bucket_quantity"
                    :propHasRecording="final_blob !== null"
                    :propFileVolumes="blob_volume_peaks"
                    @isOpen="handleIsRecorderMenuOpen($event)"
                />
            </div>

            <!--open/close VEventToneMenu-->
            <div ref="event_tone_field" class="col-span-2">
                <VEventToneField
                    propLabel="Tag"
                    :propEventToneChoice="event_tone_choice"
                    :propIsOpen="is_event_tone_menu_open"
                    @isOpen="handleIsEventToneMenuOpen($event)"
                />
            </div>
        </div>
    </div>

    <!--menus-->
    <!--we separate it out here to prevent two-sided gap, since this is not hidden, but we still add back one gap at top-->
    <div
        :class="hasExtraGap ? 'pt-4' : ''"
        class="w-full h-fit relative"
    >

        <!--arrows, aesthetics only-->
        <!--uses padding to represent gap above, because there is always only one element, so gap wouldn't work-->
        <div class="w-full h-0 grid grid-cols-8">
            <div
                v-show="is_recorder_menu_open || is_event_tone_menu_open"
                :class="[
                    is_recorder_menu_open ? 'col-span-6 col-start-1 pr-2' : '',
                    is_event_tone_menu_open ? 'col-span-2 col-start-7 pl-2' : '',
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
                @newRecording="handleNewRecording($event)"
                class="border-2 border-theme-black rounded-lg p-4"
            />
        </div>

        <!--event_tone menu-->
        <div>
            <VEventToneMenu
                :propIsOpen="is_event_tone_menu_open"
                @eventToneSelected="handleEventToneSelected($event)"
                class="border-2 border-theme-black rounded-lg p-4"
            />
        </div>
    </div>

    <!--submit-->
    <div class="mt-8 flex flex-col gap-2">
        <VActionSpecial
            @click.stop="submitForm()"
            :propIsEnabled="canSubmit"
            propElement="button"
            type="button"
            propElementSize="l"
            propFontSize="l"
            class="w-full"
        >
            <div class="mx-auto">

                <div v-if="propIsOriginator === true">

                    <VLoading
                        v-if="is_submitting"
                        propElementSize="l"
                    >
                        <span class="pl-2">Starting event...</span>
                    </VLoading>

                    <span v-else>
                        Start event
                    </span>
                </div>

                <div v-else-if="propIsOriginator === false">

                    <VLoading
                        v-if="is_submitting"
                        propElementSize="l"
                    >
                        <span class="pl-2">Creating reply...</span>
                    </VLoading>

                    <span v-else>
                        Create reply
                    </span>
                </div>
            </div>
        </VActionSpecial>
    </div>
</template>


<script setup lang="ts">

    import VActionSpecial from '../small/VActionSpecial.vue';
    import VTextArea from '/src/components/small/VTextArea.vue';
    import VEventToneField from '/src/components/medium/VEventToneField.vue';
    import VEventToneMenu from '/src/components/medium/VEventToneMenu.vue';
    import VRecorderField from '/src/components/medium/VRecorderField.vue';
    import VRecorderMenu from '/src/components/medium/VRecorderMenu.vue';
    import VLoading from '../small/VLoading.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import EventToneTypes from '@/types/EventTones.interface';
    import { notify } from 'notiwind';
    const axios = require('axios');

    export default defineComponent({
        data() {
            return {
                event_name: "",

                is_event_tone_menu_open: false, //updates only from VEventToneField to VEventToneMenu, maybe use vuex
                event_tone_choice: null as EventToneTypes|null,
                is_submitting: false,

                is_recorder_menu_open: false,
                final_blob: null as Blob|null,
                blob_duration: 0,
                blob_volume_peaks: [] as number[],
                bucket_quantity: 20,
                // propMaxDuration: (1000 * 60 * 2) + 500,    //2m + 0.5s, as final_blob is always +-0.1s away
                max_duration_ms: 120000,    //2m + 0.5s, as final_blob is always +-0.1s away
            };
        },
        props: {
            propIsOriginator: {
                type: Boolean,
                required: true,
                default: true
            },
            propEventRoomId: {
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
            is_event_tone_menu_open(new_value){

                if(new_value === true && this.is_recorder_menu_open === true){

                    this.is_recorder_menu_open = false;
                }
            },
            is_recorder_menu_open(new_value){
                
                if(new_value === true && this.is_event_tone_menu_open === true){

                    this.is_event_tone_menu_open = false;
                }
            },
        },
        computed: {
            hasExtraGap() : boolean {

                return this.is_recorder_menu_open === true || this.is_event_tone_menu_open === true;
            },
            canSubmit() : boolean {

                if(
                    this.propCanSubmit === true &&
                    this.is_submitting === false &&
                    (
                        (this.propIsOriginator === true && this.event_name.trim() !== '') ||
                        (this.propIsOriginator === false && this.propEventRoomId !== null)
                    ) &&
                    this.event_tone_choice !== null &&
                    this.final_blob !== null &&
                    this.blob_volume_peaks.length === this.bucket_quantity &&
                    this.blob_duration > 0
                ){

                    return true;
                }

                //don't do show_has_empty_field_error here because it should only show on submit attempt
                return false;
            },
        },
        methods: {
            closeAllMenu() : void {

                this.is_recorder_menu_open = false;
                this.is_event_tone_menu_open = false;
            },
            async submitForm() : Promise<void> {

                if(this.canSubmit === false){

                    return;
                }

                this.is_submitting = true;

                let data = new FormData();
                const specific_url = this.propIsOriginator === true ? 'create-new' : 'reply';
                
                //prepare data
                //webm follows VRecorder
                data.append('event_tone_id', JSON.stringify((this.event_tone_choice as EventToneTypes)['id']));
                data.append('audio_file', this.getPreparedFileForSubmit());

                if(this.propIsOriginator === true && this.event_name.trim() !== ''){

                    //originator, paired data
                    data.append('event_room_name', this.event_name);

                }else if(this.propIsOriginator === false && this.propEventRoomId !== null){

                    //responder, paired data
                    data.append('event_room_id', JSON.stringify(this.propEventRoomId));

                }else{

                    this.is_submitting = false;
                    return;
                }

                await axios.post(window.location.origin + '/api/event-rooms/' + specific_url, data)
                .then((response:any) => {

                    if(response.status === 201 && 'event_room_id' in response.data['data']){

                        this.$emit('isSubmitSuccessful', true);

                        //redirect to this page without storing current URL, so it is only shown once in history
                        window.location.replace(window.location.origin + "/hear/" + response.data['data']['event_room_id'].toString());

                    }else{

                        this.$emit('isSubmitSuccessful', false);
                        this.is_submitting = false;
                    }

                })
                .catch((error:any) => {

                    this.$emit('isSubmitSuccessful', false);
                    this.is_submitting = false;

                    notify({
                        title: this.propIsOriginator === true ? 'Creating event failed' : 'Creating reply failed',
                        text: (this.propIsOriginator === true ? 'Unable to create event. ' : 'Unable to create reply. ') + error.response.data['message'],
                        type: "error"
                    }, 3000);
                });
            },
            getPreparedFileForSubmit() : File {

                if(this.final_blob === null){

                    throw new Error("Cannot prepare final_blob for submit when it is null.");
                }

                return new File([this.final_blob as Blob], 'new_recording.mp3', {type:"audio/mp3"});
            },
            handleNewRecording(new_value:{'blob':Blob, 'blob_duration':number, 'blob_volume_peaks':number[]}) : void {

                this.final_blob = new_value['blob'];
                this.blob_duration = new_value['blob_duration'];
                this.blob_volume_peaks = new_value['blob_volume_peaks'];
            },
            handleIsRecorderMenuOpen(new_value:boolean) : void {

                this.is_recorder_menu_open = new_value;
            },
            handleEventToneSelected(new_value:EventToneTypes|null) : void {

                this.is_event_tone_menu_open = false;
                this.event_tone_choice = new_value;
            },
            handleIsEventToneMenuOpen(new_value:boolean) : void {

                this.is_event_tone_menu_open = new_value;
            },
            handleNewEventName(new_value:string) : void {

                this.event_name = new_value;
            },
            axiosSetup() : boolean {

                //your template must have {% csrf_token %}
                let token = document.getElementsByName("csrfmiddlewaretoken")[0];

                if(token === undefined){

                    console.log('CSRF not found.');
                    return false;
                }

                axios.defaults.headers.common['X-CSRFToken'] = (token as HTMLFormElement).value;
                axios.defaults.headers.post['Content-Type'] = 'multipart/form-data';
                return true;
            },
        },
        mounted(){

            //set up axios appropriately
            this.axiosSetup();
        },
    });
</script>



