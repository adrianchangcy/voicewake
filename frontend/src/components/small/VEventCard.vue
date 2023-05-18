<template>

    <div class="text-theme-black">
        <!--label, ripples, total duration-->
        <VActionButtonM
            class="w-full px-5 grid grid-cols-4"
            @click.stop="handleIsSelected()"
        >            
            <!--ripples-->
            <div class="col-span-2 h-full top-0 bottom-0 my-auto relative">
                <div
                    ref="volume_ripples_container"
                    class="w-full h-full absolute flex flex-row justify-between"
                >
                    <div
                        v-for="volume_ripple in propEvent.audio_volume_peaks.length" :key="volume_ripple"
                        ref="volume_ripple"
                        class="h-full scale-y-0 origin-center"
                    >
                        <div class="left-0 right-0 mx-auto w-0.5 h-full bg-theme-black">
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-span-1 h-full relative">
                <!--total duration, width is to match emoji-->
                <span
                    v-if="is_selected === false"
                    class="w-10 h-fit absolute right-0 top-0 bottom-0 m-auto text-sm font-medium"
                >
                    {{ prettyFileDuration }}
                </span>
                <i v-else class="w-fit h-fit text-2xl fas fa-square-check text-theme-lead absolute left-0 right-0 top-0 bottom-0 m-auto"></i>
            </div>

            <div class="col-span-1 h-full relative">
                <!--label-->
                <span
                    class="w-fit h-fit absolute right-0 top-0 bottom-0.5 m-auto text-3xl has-emoji pb-0.5"
                >
                    {{ propEvent.event_tone.event_tone_symbol }}
                </span>
                <span class="sr-only">{{ propEvent.event_tone.event_tone_name }}</span>
            </div>
        </VActionButtonM>
    </div>
</template>


<script setup lang="ts">

    import VActionButtonM from '/src/components/small/VActionButtonM.vue';
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    // import anime from 'animejs';
    import EventTypes from '@/types/Events.interface';
    import { prettyDuration } from '@/helper_functions';

    export default defineComponent({
        data(){
            return {
                is_selected: false,
            };
        },
        mounted(){

            for(let x = 0; x < this.propEvent.audio_volume_peaks.length; x++){

                (this.$refs.volume_ripple as HTMLElement[])[x].style.transform = 'scaleY('+this.propEvent.audio_volume_peaks[x]+')';
            }
        },
        props: {
            propEvent: {
                type: Object as PropType<EventTypes>,
                required: true,
            },
        },
        computed: {
            prettyFileDuration(){
                return prettyDuration(this.propEvent.audio_file_seconds);
            },
        },
        methods: {
            handleIsSelected() : void {

                this.is_selected = !this.is_selected;
                this.$emit('isSelected', this.is_selected);
            },

        }

    });
</script>