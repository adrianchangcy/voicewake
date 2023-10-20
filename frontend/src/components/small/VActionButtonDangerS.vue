<template>
    <button
        :class="[
            (propIsEnabled ? '' : 'opacity-30'),
            'block h-10 text-base font-medium text-theme-light action-danger-hover      rounded-lg border-t-2    shadow-md active:shadow-sm     shadow-theme-soft-danger/75 active:shadow-theme-soft-danger/75        bg-[#f9482b] active:bg-theme-danger     border-[#fd8a8a] active:border-[#f66868]    transition      focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-theme-outline'
        ]"
        type="button"
        :disabled="!propIsEnabled"
    >
        <!--current font sinks too low, hence pb-->
        <div class="w-full h-full pb-0.5 flex items-center">
            <slot></slot>
        </div>
    </button>
</template>


<script lang="ts">
    //focus:border-2 focus:outline-none focus:ring-1 focus:ring-theme-black focus:border-theme-black
    //for all buttons, change our hover css to click, and come up with another css for hover

    //we do not handle :disabled for buttons,
    //because it prevents other elements from dragging when mouse goes over :disabled elements
    //also decided not to use cursor-not-allowed, because it only registers if your mouse moves
    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return {

            };
        },
        props:{
            propIsEnabled: {
                type: Boolean,
                default: true
            },
        },
    });
</script>