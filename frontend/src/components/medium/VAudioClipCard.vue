<template>

    <!--h-20 as all relevant components will be h-20, which prevents content shifting-->
    <div class="h-20">

        <!--label, ripples, total duration-->
        <div
            v-show="!isSelected"
            class="w-full h-full"
        >
            <VAction
                prop-element="button"
                prop-element-size="m"
                prop-font-size="m"
                :prop-is-icon-only="true"
                type="button"
                class="w-full shadow-md active:shadow-sm"
                @click="emitSelectedAudioClip()"
            >
                <div class="w-full h-full grid grid-cols-4 text-4xl">
                    <span class="sr-only">play recording</span>

                    <div class="col-span-1 h-full relative">
                        <!--total duration, width is to match emoji-->
                        <div
                            class="w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto text-sm"
                        >
                            <span>{{ prettyFileDuration }}</span>
                        </div>
                    </div>

                    <!--ripples-->
                    <!--h-8 because VPlayback at half is h-4-->
                    <div ref="canvas_ripples_container" class="col-span-2 h-8 top-0 bottom-0 my-auto">
                        <canvas ref="canvas_ripples" class="w-full h-full mx-auto"></canvas>
                    </div>

                    <div class="col-span-1 h-full relative">
                        <!--label-->
                        <span
                            class="w-fit h-fit absolute left-0 right-0 top-0 bottom-0.5 m-auto text-2xl has-emoji pb-0.5"
                            aria-hidden="true"
                        >
                            {{ propAudioClip.audio_clip_tone.audio_clip_tone_symbol }}
                        </span>
                        <span class="sr-only">{{ propAudioClip.audio_clip_tone.audio_clip_tone_name }}</span>
                    </div>
                </div>
            </VAction>
        </div>

        <div
            v-show="isSelected"
            :id="getTeleportId"
            class="w-full h-full"
        >
        </div>

    </div>
</template>


<script setup lang="ts">
    import VAction from '../small/VAction.vue';
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import anime from 'animejs';
    import AudioClipsTypes from '@/types/AudioClips.interface';
    import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';
    import { prettyDuration, drawCanvasRipples } from '@/helper_functions';
    import { useRedrawCanvasesStore } from '@/stores/RedrawCanvasesStore';

    export default defineComponent({
        data(){
            return {
                redraw_canvases_store: useRedrawCanvasesStore(),
                redraw_canvases_store_index: null as number|null,

                main_anime: null as InstanceType<typeof anime> | null,
            };
        },
        props: {
            propAudioClip: {
                type: Object as PropType<AudioClipsTypes|AudioClipsAndLikeDetailsTypes>,
                required: true,
            },
            propSelectedAudioClip: {
                type: Object as PropType<AudioClipsTypes|AudioClipsAndLikeDetailsTypes|null>,
                default: null,
            },
            propBucketQuantity: {
                type: Number,
                default: 20,
            },
        },
        computed: {
            prettyFileDuration(){

                return prettyDuration(this.propAudioClip.audio_duration_s);
            },
            getTeleportId(){

                return 'vplayback-teleport-audio-clip-id-' + this.propAudioClip.id.toString();
            },
            isSelected() : boolean {

                return this.propSelectedAudioClip !== null && this.propAudioClip.id === this.propSelectedAudioClip.id;
            },
        },
        emits: [
            'selectedAudioClip', 'newVPlaybackTeleportId',
        ],
        watch: {
            isSelected(new_value){

                //this watcher is affordable when used with Virtual Scroller
                //must watch isSelected, as passing active from Virtual Scroller is unreliable

                if(new_value === true){

                    this.emitNewVPlaybackTeleportId(true);
                }

                //we cannot emit teleport(false) here,
                //since it would cause a race condition with selected's teleport(true)

                this.drawRipples();
            },
            propAudioClip(new_value:AudioClipsTypes, old_value:AudioClipsTypes){

                //if old value is same as selected, it means it was previously selected
                //this happens when VirtualScroller reuses selected component on scroll
                if(
                    this.propSelectedAudioClip !== null &&
                    old_value.id === this.propSelectedAudioClip.id &&
                    new_value.id !== this.propSelectedAudioClip.id
                ){

                    this.emitNewVPlaybackTeleportId(false);
                }

                this.drawRipples();
            },
        },
        methods: {
            emitNewVPlaybackTeleportId(can_teleport:boolean) : void {

                if(can_teleport === true){

                    this.$emit('newVPlaybackTeleportId', '#' + this.getTeleportId);

                }else{

                    //this teleports VPlayback on unmount so audio persists
                    this.$emit('newVPlaybackTeleportId', '#temporary-vplayback-teleport');
                }
            },
            emitSelectedAudioClip() : void {

                if(this.isSelected === true){

                    return;
                }

                this.$emit('selectedAudioClip', this.propAudioClip);
            },
            drawRipples() : void {

                this.$nextTick(()=>{

                    drawCanvasRipples(
                        (this.$refs.canvas_ripples_container as HTMLElement).getBoundingClientRect(),
                        this.$refs.canvas_ripples as HTMLCanvasElement,
                        this.propAudioClip.audio_volume_peaks,
                        'center',
                    );
                });
            },
            redrawCanvasRipples() : void {

                this.drawRipples();

                //redraw again after 200ms
                //resize can sometimes fire before final dimension is known
                window.setTimeout(()=>{
                    this.drawRipples();
                }, 200);
            },
        },
        mounted(){

            if(this.isSelected === true){

                this.emitNewVPlaybackTeleportId(true);
            }

            this.drawRipples();

            this.redraw_canvases_store_index = this.redraw_canvases_store.addAudioVolumePeakCanvas(
                this.redrawCanvasRipples
            );
        },
        beforeUnmount(){

            if(this.isSelected === true){

                this.emitNewVPlaybackTeleportId(false);
            }

            if(this.redraw_canvases_store_index !== null){

                this.redraw_canvases_store.deleteAudioVolumePeakCanvas(this.redraw_canvases_store_index);
            }
        },
    });
</script>