<template>

    <div>

        <VSectionTitle
            :propTitle="templateStrings[0]"
            :propTitleDescription="templateStrings[1]"
            v-if="propIsOriginator === true"
        />

        <div
            spellcheck="false"
            class="bg-theme-light flex flex-col text-theme-black"
            :class="[
                propIsOriginator ? 'gap-4' : 'gap-2',
                ''
            ]"
        >
            <VTextArea
                :propIsRequired="true"
                propElementId="event-name"
                propLabel="Title"
                propPlaceholder=""
                :propMaxLength="40"
                :propHasTextCounter="true"
                :propHasStatusText="false"
                @newValue="handleNewEventName($event)"
                v-if="propIsOriginator === true"
            />

            <!--fields for open/close-->
            <div class="grid grid-cols-8 gap-2">

                <!--open/close VRecorderMenu-->
                <div ref="recorder_field" class="col-span-6">
                    <VRecorderField
                        propLabel="Recording"
                        :propIsOpen="is_recorder_menu_open"
                        :propBucketQuantity="bucket_quantity"
                        :propHasRecording="final_blob !== null"
                        :propFileVolumes="blob_volume_peaks"
                        :propFileDuration="blob_duration"
                        @isOpen="handleIsRecorderMenuOpen($event)"
                    />
                </div>

                <!--open/close VEventToneMenu-->
                <div ref="event_tone_field" class="col-span-2">
                    <VEventToneField
                        propLabel="Emoji"
                        :propEventToneChoice="event_tone_choice"
                        :propIsOpen="is_event_tone_menu_open"
                        @isOpen="handleIsEventToneMenuOpen($event)"
                    />
                </div>
            </div>

            <!--menus-->
            <div class="w-full h-fit relative">

                <!--arrows, aesthetics only-->
                <div class="w-full h-0 grid grid-cols-8">
                    <!--arrow for recorder menu-->
                    <div v-show="is_recorder_menu_open" class="col-span-6 col-start-1 relative">
                        <div class="z-10 w-2 h-2 absolute -top-1 left-0 right-0 m-auto bg-theme-light border-l-2 border-t-2 border-theme-black rotate-45"></div>
                    </div>
                    <!--arrow for event_tones menu-->
                    <div v-show="is_event_tone_menu_open" class="col-span-2 col-start-7 relative">
                        <div class="z-10 w-2 h-2 absolute -top-1 left-0 right-0 m-auto bg-theme-light border-l-2 border-t-2 border-theme-black rotate-45"></div>
                    </div>
                </div>

                <!--recorder menu-->
                <div>
                    <VRecorderMenu
                        :propIsOpen="is_recorder_menu_open"
                        :propBucketQuantity="bucket_quantity"
                        :propMaxDuration="max_duration"
                        @newRecording="handleNewRecording($event)"
                        class="border-2 border-theme-black rounded-lg"
                    />
                </div>

                <!--event_tone menu-->
                <div>
                    <VEventToneMenu
                        :propIsOpen="is_event_tone_menu_open"
                        @eventToneSelected="handleEventToneSelected($event)"
                        class="border-2 border-theme-black rounded-lg"
                    />
                </div>
            </div>

            <!--submit-->
            <div
                :class="[
                    propIsOriginator === true ? 'pt-4' : '',
                    ''
                ]"
            >
                <VActionButtonSpecialL
                    class="w-full"
                    :propIsEnabled="canSubmit"
                    @click.stop="submitForm()"
                >
                    <span>{{ templateStrings[2] }}</span>
                </VActionButtonSpecialL>
            </div>

        </div>

    </div>
</template>


<script setup lang="ts">

    import VActionButtonSpecialL from '/src/components/small/VActionButtonSpecialL.vue';
    import VSectionTitle from '/src/components/small/VSectionTitle.vue';
    import VTextArea from '/src/components/small/VTextArea.vue';
    import VEventToneField from '/src/components/medium/VEventToneField.vue';
    import VEventToneMenu from '/src/components/medium/VEventToneMenu.vue';
    import VRecorderField from '/src/components/medium/VRecorderField.vue';
    import VRecorderMenu from '/src/components/medium/VRecorderMenu.vue';

</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import EventToneTypes from '@/types/EventTones.interface';
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
                max_duration: 10000,    //2m + 0.5s, as final_blob is always +-0.1s away
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
        },
        watch: {
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
            templateStrings() : string[] {

                if(this.propIsOriginator === true){

                    return [
                        'Start an Event',
                        'Fill in the fields below',
                        'Done'
                    ];
                }

                return [
                    '',
                    '',
                    'Done'
                ];
            },
            canSubmit() : boolean {

                if(
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

                return false;
            },
        },
        methods: {
            async submitForm() : Promise<void> {

                if(this.canSubmit === false){

                    return;
                }

                this.is_submitting = true;

                let data = new FormData();
                
                //prepare data
                data.append('event_tone_id', JSON.stringify((this.event_tone_choice as EventToneTypes)['id']));
                data.append('audio_file', this.final_blob as Blob);
                data.append('audio_file_seconds', JSON.stringify(parseFloat(((this.blob_duration / 1000).toFixed(2)).toString())));
                data.append('is_originator', JSON.stringify(this.propIsOriginator));

                //prepare array in this specific way
                for(let x=0; x < this.blob_volume_peaks.length; x++){

                    data.append('audio_volume_peaks', JSON.stringify(this.blob_volume_peaks[x]));
                }

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
                await axios.post('http://127.0.0.1:8000/api/events/create', data)
                .then((response:any) => {

                    if(response.status === 201 && 'event_room_id' in response.data['data']){

                        window.location.href = "http://127.0.0.1:8000/hear/" + response.data['data']['event_room_id'].toString();
                        //no need to do is_submitting=true on success
                    }

                })
                .catch((error:any) => {

                    console.log(error.response.data['message']);
                    this.is_submitting = false;
                });
            },
            handleNewRecording(new_value:{'blob':Blob, 'blob_duration':number, 'blob_volume_peaks':number[]}) : void {

                this.final_blob = new_value['blob'];
                this.blob_duration = new_value['blob_duration'];
                this.blob_volume_peaks = new_value['blob_volume_peaks'];
            },
            handleIsRecorderMenuOpen(new_value:boolean) : void {

                this.is_recorder_menu_open = new_value;
            },
            handleEventToneSelected(new_value:EventToneTypes) : void {

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



