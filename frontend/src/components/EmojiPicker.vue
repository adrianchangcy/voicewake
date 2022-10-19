<template>
    <div class="w-full h-full flex flex-col">
        <button
            v-click-outside="{
                related_data: 'is_emoji_picker_open',
                exclude: ['left_emoji_button']
            }"
            @click.self="toggleEmojiPicker()"
            :disabled="is_emoji_picker_open"
            class="w-full h-full grid grid-cols-4 grid-flow-col items-center"
        >
            <div
                :class="[
                    is_emoji_picker_open ? 'w-full' : 'w-0',
                    'col-span-1 w-full h-full flex flex-nowrap text-4xl text-center items-center place-items-start transition-all duration-300 ease-in-out'
                ]"
            >
                <button
                    v-if="emoji_choice !== null"
                    ref="left_emoji_button"
                    @click.prevent="toggleEmojiPicker()"
                    :aria-label="'Current choice is '+emoji_choice.index"
                    class="flex-1"
                >
                    {{emoji_choice.emoji}}
                </button>
            </div>
            <TransitionFadeSlow>
                <!--we use the left border here as divider instead of main button's, with box-content for true divider position-->
                <div
                    v-show="is_emoji_picker_open"
                    class="col-span-3 w-full h-full emojis-container overflow-x-hidden overflow-y-auto bg-theme-light text-2xl border-l-2 border-theme-black box-content"
                >
                    <div
                        class="items-center place-items-center grid grid-flow-row grid-cols-4 text-center"
                        v-for="category in emoji_categories" :key="category"
                    >
                        <div
                            class="col-span-1"
                            v-for="(emoji, index) in category" :key="index"
                        >
                            <button
                                @click.prevent="handleEmojiClick($event, emoji, index)"
                                :aria-label="index"
                                :disabled="is_emoji_disabled"
                            >
                                {{emoji}}
                            </button>

                        </div>
                    </div>
                </div>
            </TransitionFadeSlow>
        </button>
    </div>
</template>

<script setup>

    import TransitionFadeSlow from '/src/transitions/TransitionFadeSlow.vue';

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
                is_emoji_disabled: true,
            };
        },
        computed: {
            emoji_categories(){
                return emoji_data;
            }
        },
        methods: {
            toggleEmojiPicker(){

                this.is_emoji_picker_open = !this.is_emoji_picker_open;

                //if needed,
                //compare performance on "v-bind on many buttons" vs. "emit same value constantly on spam"
                this.is_emoji_disabled = !this.is_emoji_disabled;
            },
            handleEmojiClick(event, emoji, index){

                this.toggleEmojiPicker();
                this.emoji_choice = {'index': index, 'emoji': emoji};
                this.$emit('emojiClick', this.emoji_choice);
            },
        },
        mounted(){

            //navigate emojis until we get our first emoji key:value to set as default
            let full_emojis = this.emoji_categories;
            let category_key = Object.keys(full_emojis)[0];
            let first_emoji = Object.entries(full_emojis[category_key])[0];
            this.emoji_choice = {
                'index': first_emoji[0],
                'emoji': first_emoji[1]
            };
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