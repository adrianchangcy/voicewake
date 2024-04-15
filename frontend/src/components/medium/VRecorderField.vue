<template>
    <VInputLabel
    class="left-0"
    for="click-to-record"
    >
        {{ propLabel }}
    </VInputLabel>
    <button
        @click.stop="[toggleMenu(), emitIsOpen()]"
        :disabled="!propIsEnabled"
        :class="[
            is_open ? 'border-theme-black dark:border-dark-theme-white      focus-visible:outline-offset-0' : 'border-theme-gray-3 dark:border-dark-theme-gray-3 shade-border-when-hover   focus-visible:-outline-offset-2',
            'w-full h-20 px-4 py-2 relative border-2 rounded-lg     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-theme-black dark:focus-visible:outline-dark-theme-white'
        ]"
        id="click-to-record"
        type="button"
    >
        <!--ripples-->
        <div ref="canvas_ripples_container" class="w-full h-[75%] top-0 bottom-0 m-auto">
            <canvas ref="canvas_ripples" class="w-full h-full mx-auto"></canvas>
        </div>
        <span v-if="propHasRecording" class="sr-only">
            You have a recording
        </span>
        <span v-else class="sr-only">
            No recording
        </span>
        <span v-if="propIsOpen" class="sr-only">
            Close recording menu
        </span>
        <span v-else class="sr-only">
            Open recording menu
        </span>
    </button>
</template>


<script setup lang="ts">
    import VInputLabel from '../small/VInputLabel.vue';
</script>

<script lang="ts">
    //we don't keep VRecorderMenu in this component due to the inflexibility of button size =/= menu size
    import { defineComponent, PropType } from 'vue';
    import { drawCanvasRipples } from '@/helper_functions';

    export default defineComponent({
        data(){
            return{
                is_open: false,
            };
        },
        emits: ['isOpen'],
        props: {
            propLabel: String,
            propBucketQuantity: {
                type: Number,
                required: true,
            },
            propAudioVolumePeaks: {    //not sure if this is the best way to type this, but it looks ok
                type: Array as PropType<number[]>,
                default: () => [],
            },
            propHasRecording: {
                type: Boolean,
                default: false
            },
            propIsOpen: {
                type: Boolean,
                default: false
            },
            propIsEnabled: {
                type: Boolean,
                default: true
            },
            propIsRecording: {
                type: Boolean,
                default: false
            },
        },
        watch: {
            propIsOpen(new_value:boolean){

                this.is_open = new_value;
            },
            propAudioVolumePeaks(){

                this.drawRipples();
            },
            propIsRecording(new_value:boolean){

                if(new_value === true){

                    (this.$refs.canvas_ripples_container as HTMLElement).style.opacity = '0';

                }else{

                    (this.$refs.canvas_ripples_container as HTMLElement).style.opacity = '1';
                }
            },
        },
        methods: {
            toggleMenu() : void {

                //this dictates whether VAudioClipToneMenu is open
                this.is_open = !this.is_open;
                
            },
            emitIsOpen() : void {

                this.$emit('isOpen', this.is_open);
            },
            async redrawCanvasRipplesOnResize() : Promise<void> {

                await this.drawRipples();

                //redraw again after 200ms
                //resize can sometimes fire before final dimension is known
                window.setTimeout(async ()=>{
                    await this.drawRipples();
                }, 200);
            },
            async drawRipples() : Promise<void> {

                //can be 0
                if(this.propAudioVolumePeaks.length === this.propBucketQuantity){

                    this.$nextTick(()=>{

                        drawCanvasRipples(
                            (this.$refs.canvas_ripples_container as HTMLElement).getBoundingClientRect(),
                            this.$refs.canvas_ripples as HTMLCanvasElement,
                            this.propAudioVolumePeaks,
                            'center',
                        );
                    });
                }
            },
        },
        mounted(){

            window.addEventListener('resize', this.redrawCanvasRipplesOnResize);
        },
        beforeUnmount(){

            window.removeEventListener('resize', this.redrawCanvasRipplesOnResize);
        },
    });
</script>