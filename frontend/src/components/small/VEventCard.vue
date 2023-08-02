<template>

    <!--h-20 as all relevant components will be h-20, which prevents content shifting-->
    <div class="text-theme-black h-20">

        <!--label, ripples, total duration-->
        <div
            ref="card_button"
            style="opacity: 1;"
        >
            <button
                class="w-full grid grid-cols-4     h-20 text-4xl bg-theme-light/60 hover:bg-theme-light/80 hover:border-theme-light-trim/40 hover:shadow-sm      border-t-2 border-theme-light-trim rounded-lg shadow-md transition     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-theme-outline"
                type="button"
                @click.stop="handleIsSelected()"
            >

                <div class="col-span-1 h-full relative">
                    <!--total duration, width is to match emoji-->
                    <span
                        class="w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto text-sm font-medium"
                    >
                        {{ prettyFileDuration }}
                    </span>
                </div>

                <!--ripples-->
                <!--h-8 because VPlayback at half is h-4-->
                <div class="col-span-2 h-8 top-0 bottom-0 my-auto relative">
                    <div
                        ref="volume_ripples_container"
                        class="w-full h-full absolute flex flex-row justify-evenly"
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
                    <!--label-->
                    <span
                        class="w-fit h-fit absolute left-0 right-0 top-0 bottom-0.5 m-auto text-2xl has-emoji pb-0.5"
                    >
                        {{ propEvent.event_tone.event_tone_symbol }}
                    </span>
                    <span class="sr-only">{{ propEvent.event_tone.event_tone_name }}</span>
                </div>
            </button>
        </div>

        <!--for playback teleport-->
        <!--must be here to ensure it's in the correct order of focus after card_button disappears-->
        <div
            :id="playback_teleport_event_id"
            ref="playback_container"
            style="opacity: 0;"
        ></div>
    </div>
</template>


<script setup lang="ts">

</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import anime from 'animejs';
    import EventTypes from '@/types/Events.interface';
    import { prettyDuration } from '@/helper_functions';

    export default defineComponent({
        data(){
            return {
                playback_teleport_event_id: '',
                main_anime: null as InstanceType<typeof anime> | null,
            };
        },
        mounted(){

            this.playback_teleport_event_id = 'playback-teleport-event-id-' + this.propEvent.id.toString();

            for(let x = 0; x < this.propEvent.audio_volume_peaks.length; x++){

                const target_ripple = (this.$refs.volume_ripple as HTMLElement[])[x];

                //UPDATE: non-zero feels more functional for end user
                if(this.propEvent.audio_volume_peaks[x] < 0.05){

                    target_ripple.style.transform = 'scaleY('+ 0.05 +')';

                }else if(this.propEvent.audio_volume_peaks[x] > 1){

                    target_ripple.style.transform = 'scaleY('+ 1 +')';                    

                }else{

                    target_ripple.style.transform = 'scaleY('+ this.propEvent.audio_volume_peaks[x] +')';                    
                }
            }
        },
        props: {
            propEvent: {
                type: Object as PropType<EventTypes>,
                required: true,
            },
            propIsSelected: {
                type: Boolean,
                default: false
            },
        },
        watch: {
            propIsSelected(new_value){

                this.main_anime === null ? null : this.main_anime.pause();

                if(new_value === true){

                    this.main_anime = anime.timeline({
                        easing: 'linear',
                        autoplay: true,
                        loop: false,
                    }).add({
                        targets: this.$refs.card_button,
                        opacity: '0',
                        duration: 0,
                        complete: () => {
                            (this.$refs.card_button as HTMLElement).style.display = 'none';
                        }
                    }).add({
                        targets: this.$refs.playback_container,
                        opacity: '1',
                        duration: 150,
                    });

                }else{

                    this.main_anime = anime.timeline({
                        easing: 'linear',
                        autoplay: true,
                        loop: false,
                    }).add({
                        targets: this.$refs.playback_container,
                        opacity: '0',
                        duration: 0,
                    }).add({
                        begin: () => {
                            (this.$refs.card_button as HTMLElement).style.display = 'grid';
                        },
                        targets: this.$refs.card_button,
                        opacity: '1',
                        duration: 150,
                    });
                }
            }
        },
        computed: {
            prettyFileDuration(){

                if('audio_file_seconds' in this.propEvent){

                    return prettyDuration(this.propEvent.audio_file_seconds);

                }else{

                    return prettyDuration(1);
                }
            },
        },
        methods: {
            handleIsSelected() : void {

                this.$emit('isSelected', this.propEvent);
            },

        }

    });
</script>