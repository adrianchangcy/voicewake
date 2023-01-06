<template>
    <!--
        we deal with csrf and form logic later
        we handle the design part of form first
        https://blog.xoxzo.com/2021/05/24/vue-with-django-rest-framework-api/
        https://docs.djangoproject.com/en/dev/howto/csrf/
    -->

    <div class="bg-theme-light text-left text-lg">
        <form
            spellcheck="false"
            class="
                md:w-2/4 lg:w-3/6 xl:w-2/6 m-4 md:mx-auto h-fit p-4 bg-theme-light
                flex flex-nowrap flex-col gap-10
                "
        >
            <VSectionTitle>
                <span>Say</span>
            </VSectionTitle>
            <div class="w-[90%] mx-auto">
                <VInputLabel class="w-fit mx-auto">Share your thoughts</VInputLabel>
                <VAudioPlayback
                    :propFile="final_file"
                    :propIsRecording="is_recording"
                    :propRecordingVolume="recording_volume"
                    :propTimeInterval="time_interval"
                    @isAnimePlaybackCompleted="handleIsAnimePlaybackCompleted($event)"
                />
                <VRecorder
                    @hasNewRecording="handleHasNewRecording($event)"
                    @isRecording="handleIsRecording($event)"
                    @hasNewRecordingVolume="handleHasNewRecordingVolume($event)"
                    @hasNewTimeInterval="handleHasNewTimeInterval($event)"
                    :propIsAnimePlaybackCompleted="is_anime_playback_completed"
                />
            </div>
            <VSectionTitle>
                <span>Details</span>
            </VSectionTitle>
            <div 
                :class="[
                    final_file === null ? '' : '',
                    'flex flex-col gap-5'
                ]"
            >
                <div class="w-[80%] mx-auto">
                    <EmojiPicker
                        propLabelText="Label the feeling"
                        class="w-full"
                    />
                </div>
                <div class="w-[80%] mx-auto">
                    <VInput
                        :propIsRequired="false"
                        propElementId="event-name"
                        propLabel="Give it a title"
                        propPlaceholder=""
                        :propMaxLength="40"
                        :propHasTextCounter="true"
                        :propHasStatusText="false"
                        :propIsOk="event_name_is_ok"
                        :propIsWarning="event_name_is_warning"
                        :propIsError="event_name_is_error"
                        :propStatusText="event_name_status_text"
                        @hasNewValue="validateEventName"
                    />
                </div>
            </div>
            <div class="w-0 h-0"><!--extra div for another divider onto main page button--></div>
            <div>
                <VActionButtonBig
                    @click.prevent="handleSubmit()"
                    class="w-full"
                >
                    <span>Done</span>
                </VActionButtonBig>
            </div>
            <div class="h-10">
                <!--extra spacing for EmojiPicker dropdown-->
            </div>
        </form>
    </div>
</template>


<script setup>

    import VRecorder from './VRecorder.vue';
    import VAudioPlayback from './VAudioPlayback.vue';
    import VActionButtonBig from './VActionButtonBig.vue';
    import EmojiPicker from './EmojiPicker.vue';
    import VInput from './VInput.vue';
    import VInputLabel from './VInputLabel.vue';
    import VSectionTitle from './VSectionTitle.vue';
</script>

<script>
    export default {
        data(){
            return {

                final_file: null,
                is_recording: false,
                recording_volume: 0,    //0-1, only changes when recording
                time_interval: 0,   //ms, based on VRecorder time_interval
                is_anime_playback_completed: null,

                event_name: '',
                event_name_is_ok: false,
                event_name_is_warning: false,
                event_name_is_error: false,
                event_name_status_text: '',

                event_tone_id: null,
                event_message: '',
            };
        },
        components: {
            VRecorder,
            VActionButtonBig,
            EmojiPicker,
            VInput,
            VSectionTitle,
        },
        watch: {
        },
        methods: {
            handleHasNewRecording(new_value){

                this.final_file = new_value;
            },
            handleIsRecording(new_value){

                this.is_recording = new_value;
            },
            handleHasNewRecordingVolume(new_value){

                this.recording_volume = new_value;
            },
            handleHasNewTimeInterval(new_value){

                this.time_interval = new_value;
            },
            validateEventName(new_value){
                
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
            newEmojiChoice(new_value){
                this.event_tone_id = new_value;
            },
            newEventMessage(new_value){
                this.event_message = new_value;
            },
            handleSubmit(){
                console.log('y submit? lol');
            },
            handleIsAnimePlaybackCompleted(new_value){

                this.is_anime_playback_completed = new_value;
            }
        }
    };
</script>



