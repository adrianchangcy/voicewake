<template>
    <div class="relative w-full h-0">
        <div class="z-10 w-fit h-fit absolute top-1 left-0 right-0 m-auto bg-theme-light/60 backdrop-blur border border-theme-black rounded-lg text-theme-light">
            <!--must declare custom dimension and padding-->
            <slot></slot>
        </div>
        <!--tooltip arrow-->
        <div class="z-[11] w-2 h-2 absolute top-0 left-0 right-0 m-auto bg-theme-black backdrop-blur-none border-l border-t border-theme-black rotate-45">
        </div>
    </div>

    <!--
        if you want to make it advanced, separate tooltip box and arrow
        so you can center the arrow, while box shifts with screen dimension
        then do something like
        <div>
            <span>blabla</span>
            <VTooltipArrow/>
            <VTooltipBox/>
        </div>
        at css, on parent-el.hover, display:block child element of class x
    -->
</template>


<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        props: {
            propIsOpaque: {
                type: Boolean,
                default: true
            }
        }
    });
</script>
