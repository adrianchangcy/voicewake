<template>
    <div
        class=""
    >
        <div class="w-20 h-20 mx-auto relative">
            <!--need inline CSS to prevent jolting from anime if without it-->
            <div
                ref="recording_visualiser_circle_0"
                class="absolute w-full h-full left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-lead/60"
                style="transform: scaleX(0) scaleY(0);"
            ></div>
            <div
                ref="recording_visualiser_circle_1"
                class="absolute w-full h-full left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-lead/40"
                style="transform: scaleX(0) scaleY(0);"
            ></div>
            <div
                ref="recording_visualiser_circle_2"
                class="absolute w-full h-full left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-lead/20"
                style="transform: scaleX(0) scaleY(0);"
            ></div>
        </div>
    </div>
</template>


<script setup lang="ts">
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import anime from 'animejs';

    export default defineComponent({
        data(){
            return {
            };
        },
        props: {
            propIntervalMs: {   //milliseconds, based on VRecorder time_interval
                type: Number,
                default: 200
            },
            propNewPulse: {    //0 to 1
                type: Number,
                default: 0
            },
            propIsRecording: {
                type: Boolean
            },
        },
        watch: {
            propNewPulse(new_value){

                this.animeRecordingVisualiser(new_value);
            },
            propIsRecording(new_value){

                if(new_value === false){

                    this.resetRecordingVisualiser();
                }
            },
        },
        methods: {
            resetRecordingVisualiser() : void {

                const recording_visualiser_circles = [
                    this.$refs.recording_visualiser_circle_0,
                    this.$refs.recording_visualiser_circle_1,
                    this.$refs.recording_visualiser_circle_2,
                ];

                //scale does not accept % or px, only percentage digit
                anime({
                    targets: recording_visualiser_circles,
                    easing: 'linear',
                    loop: false,
                    autoplay: true,
                    scaleX: '0',
                    scaleY: '0',
                    duration: this.propIntervalMs,
                });
            },
            animeRecordingVisualiser(new_value:number) : void {
                
                const recording_visualiser_circles = [
                    this.$refs.recording_visualiser_circle_0,
                    this.$refs.recording_visualiser_circle_1,
                    this.$refs.recording_visualiser_circle_2,
                ];

                //scale works with values from 0 to 1
                const base_target_percentage = 0.1;
                const percentage_increment = 0.3;
                
                anime.remove(recording_visualiser_circles);

                for(let x=0; x < recording_visualiser_circles.length; x++){

                    const extra_target_percentage = (x + 1) * percentage_increment;
                    const final_target_percentage = (new_value * extra_target_percentage) + base_target_percentage;

                    //scale does not accept % or px, only percentage digit
                    anime({
                        targets: recording_visualiser_circles[x],
                        scaleX: final_target_percentage.toString(),
                        scaleY: final_target_percentage.toString(),
                        autoplay: true,
                        easing: 'linear',
                        loop: false,
                        duration: this.propIntervalMs,
                    });
                }
            },
        }
    });
</script>