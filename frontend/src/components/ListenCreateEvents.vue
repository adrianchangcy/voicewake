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
                rounded-md shadow-inner"
        >
            <div class="flex-1 text-4xl pb-10">
                <span>Hear</span>
                <i class="fas fa-ear-listen float-right"></i>
            </div>
            <div>
                <VInput
                    :propIsRequired="false"
                    propElementId="event-name"
                    propLabel="Title"
                    propPlaceholder="An interesting title"
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
            <div class="grid grid-cols-4">
                <div class="col-span-4">
                    <EmojiPicker
                        propLabelText="Mood"
                    />
                </div>
            </div>
            <div class="grid grid-cols-4">
                <div class="col-span-4 flex flex-col gap-y-2">
                    <VRecorder
                        propLabelText="Thoughts"
                        @hasNewRecording="handleHasNewRecording"
                        @isRecording="handleIsRecording"
                    />
                    <VAudioPlayback
                        :propFile="final_file"
                        :propIsRecording="is_recording"
                    />
                </div>
            </div>
            <div class="flex-1 pt-4">
                <VActionButtonBig
                    @click.prevent="handleSubmit()"
                    class="p-4 w-full"
                >
                    <span>Start hearing from others</span>
                </VActionButtonBig>
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

</script>

<script>
    export default {
        data(){
            return {

                final_file: null,
                is_recording: false,

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
            }
        }
    };
</script>



