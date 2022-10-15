<template>
    <div class="w-full h-full flex flex-col">
        <div class="w-full h-full grid grid-cols-4 grid-flow-col items-center place-items-center">
            <button
                ref="pick_emoji"
                @click.prevent="toggleEmojiPicker"
                class="col-span-1 w-full h-full text-4xl items-center border-2 border-theme-black"
            >
                <span
                    v-if="picked_emoji !== null"
                    :aria-label="'Current choice is '+picked_emoji.index"
                >
                    {{picked_emoji.emoji}}
                </span>
            </button>
            <TransitionFade>
                <div
                    v-show="is_emoji_picker_open"
                    v-click-outside="{
                        related_data: 'is_emoji_picker_open',
                        exclude: ['pick_emoji']
                    }"
                    class="col-span-3 w-full h-full overflow-x-hidden overflow-y-auto bg-theme-light border-2 border-theme-black text-2xl"
                >
                    <div
                        class="w-auto h-full place-items-center grid grid-flow-row grid-cols-4 gap-x-2 text-center"
                        v-for="category in emojiCategories" :key="category"
                    >
                        <div
                            class="col-span-1"
                            v-for="(emoji, index) in category" :key="index"
                        >
                            <button
                                @click.prevent="handleEmojiClick($event, emoji, index)"
                                :aria-label="index"
                            >
                                {{emoji}}
                            </button>

                        </div>
                    </div>
                </div>
            </TransitionFade>
        </div>
    </div>
</template>

<script setup>

    import TransitionFade from '/src/transitions/TransitionFade.vue';

</script>

<script>
    
    //this depends on main.js clickOutside custom directive

    //we group all emojis in one category, while template above is ready for per-category flow
    import emoji_data from '/src/assets/data_emojis_final.json';

    export default{
        data(){
            return{
                picked_emoji: null,
                is_emoji_picker_open: false,
            };
        },

        computed: {
            emojiCategories(){
                return emoji_data;
            }
        },
        methods: {
            toggleEmojiPicker(){
                this.is_emoji_picker_open = !this.is_emoji_picker_open;

            },
            handleEmojiClick(event, emoji, index){
                this.picked_emoji = {'index': index, 'emoji': emoji};
                this.$emit('emoji_click', this.picked_emoji);
                this.toggleEmojiPicker();
            },
        },
        mounted(){

            //navigate emojis until we get our first emoji key:value to set as default
            let full_emojis = this.emojiCategories;
            let category_key = Object.keys(full_emojis)[0];
            let first_emoji = Object.entries(full_emojis[category_key])[0];
            this.picked_emoji = {
                'index': first_emoji[0],
                'emoji': first_emoji[1]
            };
        }
    }
</script>


<style scoped>

    /*
    use these fonts for emojis themselves to ensure proper rendering
    https://github.com/joeattardi/picmo/issues/242
    */
    .emojis_container{
        font-family: "Segoe UI Emoji", "Segoe UI Symbol", "Segoe UI", "Apple Color Emoji", "Twemoji Mozilla",
        "Noto Color Emoji", "EmojiOne Color", "Android Emoji"
    }


</style>