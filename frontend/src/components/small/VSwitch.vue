<template>
    <div class="flex flex-row pr-4 items-center relative">
        <slot></slot>
        <button
            class="absolute w-fit h-10 right-4 top-0 bottom-0 m-auto cursor-pointer hover:scale-105 transition-transform"
            type="button"
            @click.stop="changeToggle()"
        >
            <div
                :class="is_toggled ? 'bg-theme-lead/75 hover:shadow-theme-lead' : 'bg-theme-medium-gray/75 shadow-theme-medium-gray'"
                class="relative my-1 inline-flex h-7 w-14 shrink-0 shadow-inner rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out"
            >
                <span class="sr-only">{{ propScreenReaderText }} {{ is_toggled }}</span>
                <span
                    aria-hidden="true"
                    :class="is_toggled ? 'translate-x-7' : 'translate-x-0'"
                    class="pointer-events-none inline-block h-6 w-6 transform rounded-full bg-theme-light border-t-2 border-theme-light-trim shadow-lg ring-0 transition duration-200 ease-in-out"
                />
            </div>
        </button>
    </div>
</template>

<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        name: 'GetEventRoomsApp',
        data() {
            return {
                is_toggled: false,
            };
        },
        props: {
            propScreenReaderText: {
                type: String,
                required: true
            },
        },
        watch: {
            is_toggled(new_value){

                this.$emit('isToggled', new_value);
            }
        },
        methods: {
            changeToggle(){
                this.is_toggled = !this.is_toggled;
            },
        }
    });
</script>
