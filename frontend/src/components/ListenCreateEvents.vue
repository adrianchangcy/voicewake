<template>
    <!--
        we deal with csrf and form logic later
        we handle the design part of form first
        https://blog.xoxzo.com/2021/05/24/vue-with-django-rest-framework-api/
        https://docs.djangoproject.com/en/dev/howto/csrf/
    -->
    <div class="bg-theme-light text-left text-lg">
        <form class="h-fit m-4 bg-theme-light flex flex-nowrap flex-col       rounded-md shadow-inner">
            <div class="flex-1 p-4 flex flex-col gap-y-4">
                <span class="text-3xl">Describe your episode</span>
                <div class="flex flex-col">
                    <div>
                        <label for="event_name" class="text-xl">Title</label>
                        <div class="float-right">
                            <span><!--for text baseline alignment--></span>
                            <span class="w-fit text-sm">{{current_event_name_count}}/{{max_event_name_count}}</span>
                        </div>
                    </div>
                    <textarea
                        id="event_name"
                        v-model="event_name"
                        class="h-20 p-2 bg-theme-light rounded-lg border-2 border-theme-black"
                        placeholder="Trip, diarrhea, etc."
                        spellcheck="false"
                        autocomplete="off"
                        :maxlength="max_event_name_count"
                    ></textarea>
                </div>
                <div class="flex flex-col">
                    <label for="emoji-picker-slot"  class="text-xl">
                        What I feel
                    </label>
                    <div id="emoji-picker-slot" class="h-20 p-2 bg-theme-light rounded-lg border-2 border-theme-black">
                        <EmojiPicker @emojiClick="newEmojiChoice"/>
                        <input type="hidden" :data="event_tone_id">
                    </div>
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
                        placeholder="Share what you'd like them to know"
                        spellcheck="false"
                        autocomplete="off"
                        :maxlength="max_event_message_count"
                    ></textarea>
                </div>
            </div>

            <div class="flex-1 p-4 flex flex-col gap-y-2">
                <span>Who to hear from</span>
                <span>{{event_tone_id}}</span>


            </div>

        </form>
    </div>
</template>


<script setup>

    import EmojiPicker from '/src/components/EmojiPicker.vue';

</script>

<script>
    export default{
        data(){
            return {
                current_event_name_count: 0,
                max_event_name_count: 40,
                event_name: '',
                event_tone_id: null,
                current_event_message_count: 0,
                max_event_message_count: 200,
                event_message: '',
            };
        },
        components: {
            EmojiPicker
        },
        watch: {
            event_name(newValue){
                this.current_event_name_count = newValue.length;
            },
            event_message(newValue){
                this.current_event_message_count = newValue.length;
            },
        },
        methods: {
            newEmojiChoice(newValue){
                this.event_tone_id = newValue;
            },
        }
    };
</script>



