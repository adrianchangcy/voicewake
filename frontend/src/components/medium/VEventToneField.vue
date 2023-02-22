<template>
    <div>
        <VInputLabel for="event-tone-picker">
            {{propLabelText}}
        </VInputLabel>
        <button
            id="event-tone-picker"
            :aria-label="concludeAriaLabel"
            @click.stop="[toggleMenu(), emitIsOpen()]"
            :class="[
                is_open ? 'border-theme-black' : 'border-theme-medium-gray shade-border-when-hover',
                'w-full h-20 relative border-2 rounded-lg text-3xl text-theme-black text-center'
            ]"
            type="button"
        >
            <i
                v-if="propEventToneChoice === null"
                class="far fa-face-meh-blank absolute w-fit h-fit left-0 right-0 top-0 bottom-0 m-auto"
            ></i>
            <span
                v-else
                class="absolute w-fit h-fit left-0 right-0 top-0 bottom-0 m-auto"
            >
                {{propEventToneChoice.event_tone_symbol}}
            </span>
        </button>
    </div>
</template>

<script setup lang="ts">
    import VInputLabel from '/src/components/small/VInputLabel.vue';
</script>

<script lang="ts">
    //we don't keep VEventToneMenu in this component due to the inflexibility of button size =/= menu size
    import { defineComponent, PropType } from 'vue';
    import EventToneTypes from '@/types/EventTones.interface';

    export default defineComponent({
        data(){
            return{
                is_open: false,
            };
        },
        emits: ['isOpen'],
        props: {
            propLabelText: String,
            propEventToneChoice: {
                type: Object as PropType<EventToneTypes> | null,
                default: null,
            },
            propIsOpen: {
                type: Boolean,
                default: false
            },
        },
        computed: {
            concludeAriaLabel() : string {

                if(this.propEventToneChoice !== null){

                    return 'select a feeling; your current selection is ' + this.propEventToneChoice.event_tone_name;

                }else{

                    return 'select a feeling; you have not selected any';
                }
            },
        },
        watch: {
            propIsOpen(new_value:boolean) : void {
                this.is_open = new_value;
            },
        },
        methods: {
            toggleMenu() : void {
                //this dictates whether VEventToneMenu is open
                this.is_open = !this.is_open;
                
            },
            emitIsOpen() : void {
                this.$emit('isOpen', this.is_open);
            }
        },
    });
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