<template>
    <!--
        we deal with csrf and form logic later
        we handle the design part of form first
        https://blog.xoxzo.com/2021/05/24/vue-with-django-rest-framework-api/
        https://docs.djangoproject.com/en/dev/howto/csrf/
    -->
    <div class="w-full h-full box-border bg-theme-light text-left">
        <h1 class="h-fit text-center text-xl">
            Hear from someone for an upcoming episode in your life
        </h1>
        <form class="h-fit m-4 bg-theme-light flex flex-nowrap flex-col gap-y-2       rounded-md shadow-inner text-xl">
            <div class="flex flex-col p-2">
                <label
                    for="event_name"
                    class="h-fit"
                >
                    Episode name
                </label>
                <textarea
                    id="event_name"
                    class="h-fit p-2 bg-theme-light border-2 border-theme-black"
                    placeholder="Trip, surgery, graduation, diarrhea, etc."
                    spellcheck="false"
                    autocomplete="off"
                    rows="2"
                ></textarea>
            </div>
            <div class="flex flex-col p-2">
                <label class="h-fit" for="emoji-picker-slot">
                    What I feel
                </label>
                <div class="h-40" id="emoji-picker-slot">
                    <slot name="emojiPicker"></slot>
                </div>
            </div>
            <div class="flex flex-col p-2">
                <label class="h-fit">When</label>
            </div>
            <!--
                to-do:
                -successfully load first json value as default (e.g. "Not Sure") **DONE**
                -make EmojiPicker keyboard-friendly
                -beautify form

                maybe:
                -add divider here, to separate between event details and event personnel
                -if user is chosen, change from "to whoever reads this" to "to __"
                -heavily emphasise on keeping steps short, including payment (direct cash is easiest)
            -->
            <div class="flex flex-col p-2">
                <label for="event_message" class="h-fit">To whoever sees this</label>
                <textarea
                    id="event_message"
                    class="h-fit p-2 bg-theme-light border-2 border-theme-black"
                    placeholder="Share what you'd like them to know"
                    spellcheck="false"
                    autocomplete="off"
                ></textarea>
            </div>
        </form>
    </div>
</template>




