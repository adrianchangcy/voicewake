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
            <!-- <div class="col-span-1 w-full h-full flex flex-nowrap text-4xl text-center items-center"> -->
            <div
                :class="[
                    is_emoji_picker_open ? 'w-full' : 'w-0',
                    'col-span-1 w-full h-full flex flex-nowrap text-4xl text-center items-center place-items-start transition-all duration-300 ease-in-out'
                ]"
            >
                <button
                    v-if="picked_emoji !== null"
                    ref="left_emoji_button"
                    @click.prevent="toggleEmojiPicker()"
                    :aria-label="'Current choice is '+picked_emoji.index"
                    class="flex-1"
                >
                    {{picked_emoji.emoji}}
                </button>
            </div>
            <TransitionFadeSlow>
                <!--we use the left border here as divider instead of main button's, with box-content for true divider position-->
                <div
                    v-show="is_emoji_picker_open"
                    class="col-span-3 w-full h-full overflow-x-hidden overflow-y-auto bg-theme-light text-2xl border-l-2 border-theme-black box-content"
                >
                    <div
                        class="items-center place-items-center grid grid-flow-row grid-cols-4 text-center"
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
            //prevent click from registering during transition
            closeEmojiPicker(){

                this.is_emoji_picker_open = false;
            },
            handleEmojiClick(event, emoji, index){
                this.closeEmojiPicker();
                this.picked_emoji = {'index': index, 'emoji': emoji};
                this.$emit('emoji_click', this.picked_emoji);
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