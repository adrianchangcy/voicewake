<template>
    <!--
        we deal with csrf and form logic later
        we handle the design part of form first
        https://blog.xoxzo.com/2021/05/24/vue-with-django-rest-framework-api/
        https://docs.djangoproject.com/en/dev/howto/csrf/
    -->


    <div class="bg-theme-light text-left text-lg">
        <form spellcheck="false" class="h-fit m-4 md:w-2/4 lg:w-2/6 md:mx-auto bg-theme-light flex flex-nowrap flex-col       rounded-md shadow-inner">
            <div class="flex-1 p-4 flex flex-col gap-y-4">
                <span class="text-3xl pb-4">???</span>
                <div class="flex flex-col">
                    <VInput
                        :propIsRequired="true"
                        propElementId="event_name"
                        propLabel="Title"
                        propPlaceholder="Trip, diarrhea, etc."
                        :propMaxLength="40"
                        :propHasTextCounter="true"
                        :propStatusText="event_name_input_status"
                        :propIsOk="event_name_show_ok"
                        :propIsWarning="false"
                        :propIsError="event_name_show_error"
                        @hasNewValue="newEventName"
                    />
                </div>
                <div class="flex flex-col">
                    <label for="emoji-picker-slot"  class="text-xl">
                        What I feel
                    </label>
                    <div id="emoji-picker-slot" class="h-20 p-2 bg-theme-light rounded-lg border-2 border-theme-black">
                        <EmojiPicker @emojiClick="newEmojiChoice"/>
                        <input type="hidden" :data="event_tone_id">
                    </div>
                    <span class="h-2 text-sm"></span>
                </div>
                <div class="flex flex-col">
                    <div>
                        <label for="event_name" class="text-xl">To whoever sees this</label>
                        <div class="float-right">
                            <span><!--for text baseline alignment--></span>
                            <span class="w-fit text-sm">{{current_event_message_count}}/{{max_event_message_count}}</span>
                        </div>
                    </div>
                    <textarea
                        id="event_message"
                        v-model="event_message"
                        class="h-20 p-2 bg-theme-light rounded-lg border-2 border-theme-black"
                        placeholder="Optional"
                        autocomplete="off"
                        :maxlength="max_event_message_count"
                    ></textarea>
                    <span class="h-2 text-sm"></span>
                </div>
                <div class="pt-8">
                    <VActionButton
                        @click.prevent="handleSubmit()"
                    >
                        <span class="text-2xl">Start hearing from others</span>
                    </VActionButton>
                </div>
            </div>


        </form>
    </div>
</template>


<script setup>

    import VInput from '/src/components/VInput.vue';
    import VActionButton from '/src/components/VActionButton.vue';
    import EmojiPicker from '/src/components/EmojiPicker.vue';

</script>

<script>
    export default {
        data(){
            return {
                event_name: '',
                event_name_length: 0,
                event_name_show_ok: false,
                event_name_show_error: false,
                event_name_input_status: '',
                event_tone_id: null,
                current_event_message_count: 0,
                max_event_message_count: 200,
                event_message: '',
            };
        },
        components: {
            VInput,
            VActionButton,
            EmojiPicker,
        },
        watch: {
            event_message(new_value){
                this.current_event_message_count = new_value.length;
            },
        },
        methods: {
            newEventName(new_value){
                this.event_name = new_value;

                this.event_name_length = new_value.length;

                //doing it this way is easier than managing css classes
                if(this.event_name_length > 0 && new_value.trim().length === 0){

                    this.event_name_input_status = 'Please enter more than just whitespace.';
                    this.event_name_show_ok = false;
                    this.event_name_show_error = true;

                }else if(this.event_name_length > 0){

                    this.event_name_input_status = '';
                    this.event_name_show_ok = true;
                    this.event_name_show_error = false;

                }else{

                    this.event_name_input_status = '';
                    this.event_name_show_ok = false;
                    this.event_name_show_error = false;
                }
            },
            newEmojiChoice(new_value){
                this.event_tone_id = new_value;
            },
            handleSubmit(){
                console.log('y submit? lol');
            }
        }
    };
</script>



