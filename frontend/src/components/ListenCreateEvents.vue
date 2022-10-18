<template>
    <!--
        we deal with csrf and form logic later
        we handle the design part of form first
        https://blog.xoxzo.com/2021/05/24/vue-with-django-rest-framework-api/
        https://docs.djangoproject.com/en/dev/howto/csrf/
    -->
    <div class="bg-theme-light text-left h-min">
        <form class="h-fit m-4 bg-theme-light flex flex-nowrap flex-col       rounded-md shadow-inner text-lg">
            <div class="flex-1 p-4 flex flex-col gap-y-4">
                <span>Your episode</span>
                <div class="flex flex-col">
                    <label for="event_name" class="">
                        Title
                    </label>
                    <input 
                        type="text"
                        id="event_name"
                        class="h-10 p-2 bg-theme-light rounded-lg border-2 border-theme-black"
                        autocomplete="off"
                        placeholder="Trip, diarrhea, etc."
                    />
                </div>
                <div class="flex flex-col">
                    <label for="emoji-picker-slot"  class="">
                        What I feel
                    </label>
                    <div id="emoji-picker-slot" class="h-20 p-2 bg-theme-light rounded-lg border-2 border-theme-black">
                        <slot name="emojiPicker"></slot>
                    </div>
                </div>
                <div class="flex flex-col">
                    <label for="event_message" class="">To whoever sees this</label>
                    <textarea
                        id="event_message"
                        class="h-20 p-2 bg-theme-light rounded-lg border-2 border-theme-black"
                        placeholder="Share what you'd like them to know"
                        spellcheck="false"
                        autocomplete="off"
                        rows="2"
                    ></textarea>
                </div>
            </div>

            <div class="flex-1 p-4 flex flex-col gap-y-2">
                <span>Who to hear from</span>

                Anyone
                Someone specific

            </div>

        </form>
    </div>
</template>




