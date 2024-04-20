<template>
    <div>
        <button
            class="w-fit h-10 px-1 rounded-lg flex items-center cursor-pointer action-hover transition   focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-theme-outline dark:focus-visible:outline-dark-theme-outline"
            type="button"
            @click.stop="changeToggle()"
        >
            <div
                :class="is_toggled ? 'border-theme-lead dark:border-dark-theme-lead' : 'border-transparent'"
                class="inline-flex items-center w-12 h-6 shrink-0 rounded-full transition border-2 bg-theme-gray-3 dark:bg-dark-theme-gray-3"
            >
                <!--knob size is after removing border-->
                <span
                    aria-hidden="true"
                    :class="is_toggled ? 'translate-x-6' : 'translate-x-0'"
                    class="inline-block w-5 h-5 transition rounded-full bg-theme-black dark:bg-dark-theme-white-2"
                ></span>
            </div>
            <span class="sr-only">{{ propScreenReaderText }} {{ is_toggled }}</span>
        </button>
    </div>
</template>

<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        name: 'GetEventsApp',
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
            propDefaultToggle: {
                type: Boolean,
                default: false,
            },
        },
        emits: ['isToggled'],
        methods: {
            changeToggle(){

                this.is_toggled = !this.is_toggled;
                this.$emit('isToggled', this.is_toggled);
            },
        },
        beforeMount(){

            this.is_toggled = this.propDefaultToggle;
        },
    });
</script>
