<template>
    <div class="text-center">
        <div ref="emoji_choice_label" class="w-fit h-fit">
            <VInputLabel for="emoji-picker">{{propLabelText}}</VInputLabel>
        </div>
        <div>
            <div ref="emoji_choice_button">
                <VActionButtonMedium
                    id="emoji-picker"
                    aria-label="select an emotion"
                    @click.prevent="toggleEmojiPicker()"
                    class="w-full pb-3"
                >
                    <span v-if="emoji_choice === null">
                        <i class="far fa-face-meh-blank text-theme-black"></i>
                    </span>
                    <span v-else :aria-label="'Current choice is '+emoji_choice.index">
                        {{emoji_choice.emoji}}
                    </span>
                </VActionButtonMedium>
            </div>
            <div class="relative w-full">
                <TransitionFade>
                    <VBox
                        v-show="is_emoji_picker_open"
                        v-click-outside="{
                            var_name_for_element_bool_status: 'is_emoji_picker_open',
                            refs_to_exclude: ['emoji_choice_label', 'emoji_choice_button']
                        }"
                        class="top-2 p-2 absolute z-10 w-full left-0 right-0 mx-auto"
                    >
                        <VInputLabel>Pick one!</VInputLabel>
                        <div class="h-40 box-content emojis-container overflow-x-hidden overflow-y-auto text-2xl">
                            <div
                                class="items-center place-items-center grid grid-flow-row grid-cols-4"
                                v-for="category in emoji_categories" :key="category"
                            >
                                <div
                                    class="col-span-1"
                                    v-for="(emoji, index) in category" :key="index"
                                >
                                    <button
                                        @click.prevent="handleEmojiClick($event, emoji, index)"
                                        :aria-label="index"
                                        :disabled="!is_emoji_picker_open"
                                        class="w-10 h-10 shade-when-hover rounded-md transition-colors duration-100 ease-in-out"
                                        type="button"
                                    >
                                        {{emoji}}
                                    </button>

                                </div>
                            </div>
                        </div>
                    </VBox>
                </TransitionFade>
            </div>
        </div>
    </div>
</template>

<script setup>

    import TransitionFade from '/src/transitions/TransitionFade.vue';
    import VActionButtonMedium from '/src/components/small/VActionButtonMedium.vue';
    import VInputLabel from '/src/components/small/VInputLabel.vue';
    import VBox from '/src/components/small/VBox.vue';

</script>

<script>
    
    //this depends on main.js clickOutside custom directive

    //we group all emojis in one category, while template above is ready for per-category flow
    import emoji_data from '/src/assets/data_emojis_final.json';

    export default{
        data(){
            return{
                emoji_choice: null,
                is_emoji_picker_open: false,
            };
        },
        components: {
            TransitionFade,
            VActionButtonMedium,
            VInputLabel,
            VBox,
        },
        props: {
            propLabelText: String,
        },
        computed: {
            emoji_categories(){
                return emoji_data;
            }
        },
        watch: {
        },
        methods: {
            toggleEmojiPicker(){

                this.is_emoji_picker_open = !this.is_emoji_picker_open;
            },
            handleEmojiClick(event, emoji, index){

                this.toggleEmojiPicker();
                this.emoji_choice = {'index': index, 'emoji': emoji};
                this.$emit('emojiClick', this.emoji_choice);
            },
        },
        mounted(){

            //navigate emojis until we get our first emoji key:value to set as default
            // let full_emojis = this.emoji_categories;
            // let category_key = Object.keys(full_emojis)[0];
            // let first_emoji = Object.entries(full_emojis[category_key])[0];
            // this.emoji_choice = {
            //     'index': first_emoji[0],
            //     'emoji': first_emoji[1]
            // };
        },
    }
</script>


<style scoped>

    /*
    use these fonts for emojis themselves to ensure proper rendering
    https://github.com/joeattardi/picmo/issues/242
    */
    .emojis-container{
        font-family: "Segoe UI Emoji", "Segoe UI Symbol", "Segoe UI", "Apple Color Emoji", "Twemoji Mozilla",
        "Noto Color Emoji", "EmojiOne Color", "Android Emoji"
    }


</style>