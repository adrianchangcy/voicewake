<template>
    <div>
        <VInputLabel for="event-tone-picker">
            {{propLabel}}
        </VInputLabel>
        <button
            id="event-tone-picker"
            @click.stop="[toggleMenu(), emitIsOpen()]"
            :class="[
                is_open ? 'border-theme-dark-gray      focus-visible:-outline-offset-2' : 'border-theme-medium-gray shade-border-when-hover   focus-visible:-outline-offset-2',
                'w-full h-20 relative border-2 rounded-lg text-3xl text-theme-black text-center     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-theme-accent'
            ]"
            type="button"
        >
            <span
                v-if="propEventToneChoice !== null"
                class="absolute w-fit h-fit left-0 right-0 top-0 bottom-0 m-auto has-emoji"
            >
                {{propEventToneChoice.event_tone_symbol}}
                <span class="sr-only">{{propEventToneChoice.event_tone_name}}</span>
            </span>
            <span v-else class="sr-only">No emoji selected</span>
            <span v-if="propIsOpen" class="sr-only">
                Close emoji menu
            </span>
            <span v-else class="sr-only">
                Open emoji menu
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
            propLabel: String,
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