<template>
    <!--
        we deal with csrf and form logic later
        we handle the design part of form first
        https://blog.xoxzo.com/2021/05/24/vue-with-django-rest-framework-api/
        https://docs.djangoproject.com/en/dev/howto/csrf/
    -->

    <div class="md:w-2/4 lg:w-3/6 xl:w-2/6 mx-auto h-fit bg-theme-light text-left text-lg">

        <div class="w-[90%] mx-auto">
            <VSectionTitle>Say</VSectionTitle>
        </div>

        <form
            spellcheck="false"
            class="w-[80%] mx-auto bg-theme-light flex flex-nowrap flex-col gap-8"
        >

            <div class="">
                <VInputLabel
                    class="left-0"
                    for="click-to-record"
                >
                    Share something
                </VInputLabel>
                <VPlayback
                    :propFile="final_file"
                    :propIsRecording="is_recording"
                    :propRecordingVolume="recording_volume"
                    :propTimeInterval="time_interval"
                    :propIsForRecording="false"
                    @isAnimePlaybackCompleted="handleIsAnimePlaybackCompleted($event)"
                />
                <div class="w-0 h-2"></div>
                <VRecorder
                    @hasNewRecording="handleHasNewRecording($event)"
                    @isRecording="handleIsRecording($event)"
                    @hasNewRecordingVolume="handleHasNewRecordingVolume($event)"
                    @hasNewTimeInterval="handleHasNewTimeInterval($event)"
                    :propIsAnimePlaybackCompleted="is_anime_playback_completed"
                />
            </div>

            <div class="w-[80%] mx-auto">
                <VEventTonePicker
                    propLabelText="How you feel about it"
                    class="w-full"
                />
            </div>

            <div class="w-[80%] mx-auto">
                <VTextArea
                    :propIsRequired="false"
                    propElementId="event-name"
                    propLabel="Details (optional)"
                    propPlaceholder=""
                    :propMaxLength="100"
                    :propHasTextCounter="true"
                    :propHasStatusText="false"
                    :propIsOk="event_name_is_ok"
                    :propIsWarning="event_name_is_warning"
                    :propIsError="event_name_is_error"
                    :propStatusText="event_name_status_text"
                    @hasNewValue="validateEventName"
                />
            </div>

            <div class="w-0 h-0"></div>

            <VActionButtonBig
                @click.prevent="handleSubmit()"
                class="w-[60%] left-0 right-0 mx-auto"
            >
                <span>Hear from someone</span>
            </VActionButtonBig>

            <div class="w-0 h-0"></div>
        </form>
    </div>
</template>


<script setup lang="ts">
    import VRecorder from '/src/components/medium/VRecorder.vue';
    import VPlayback from '/src/components/medium/VPlayback.vue';
    import VEventTonePicker from '/src/components/medium/VEventTonePicker.vue';
    import VActionButtonBig from '/src/components/small/VActionButtonBig.vue';
    import VInputLabel from '/src/components/small/VInputLabel.vue';
    import VSectionTitle from '/src/components/small/VSectionTitle.vue';
    import VTextArea from '/src/components/small/VTextArea.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return {

                final_file: null as File | null,
                is_recording: false,
                recording_volume: 0,    //0-1, only changes when recording
                time_interval: 0,   //ms, based on VRecorder time_interval
                is_anime_playback_completed: false,

                event_name: '',
                event_name_is_ok: false,
                event_name_is_warning: false,
                event_name_is_error: false,
                event_name_status_text: '',

                event_tone_id: null as string | null,   //change to number if emojis are from db later
                event_message: '',
            };
        },

        watch: {
        },
        methods: {
            handleHasNewRecording(new_value:File) : void {

                this.final_file = new_value;
            },
            handleIsRecording(new_value:boolean) : void {

                this.is_recording = new_value;
            },
            handleHasNewRecordingVolume(new_value:number) : void {

                this.recording_volume = new_value;
            },
            handleHasNewTimeInterval(new_value:number) : void {

                this.time_interval = new_value;
            },
            validateEventName(new_value:string) : void {
                
                //VInput cannot .trim() for us, due to v-model
                //doing it this way is easier than managing css classes
                if(new_value.trim().length > 0){

                    //all perfect
                    this.event_name_status_text = '';
                    this.event_name_is_ok = true;
                    this.event_name_is_warning = false;
                    this.event_name_is_error = false;

                    //store
                    this.event_name = new_value;

                }else if(new_value.trim().length === 0){

                    this.event_name_status_text = '';
                    this.event_name_is_ok = false;
                    this.event_name_is_warning = false;
                    this.event_name_is_error = true;

                }else{

                    //reset
                    this.event_name_status_text = '';
                    this.event_name_is_ok = false;
                    this.event_name_is_warning = false;
                    this.event_name_is_error = false;
                }
            },
            newEmojiChoice(new_value:string) : void {
                this.event_tone_id = new_value;
            },
            newEventMessage(new_value:string) : void {
                this.event_message = new_value;
            },
            handleSubmit() : void {
                console.log('y submit? lol');
            },
            handleIsAnimePlaybackCompleted(new_value:boolean) : void {

                this.is_anime_playback_completed = new_value;
            }
        }
    });
</script>



