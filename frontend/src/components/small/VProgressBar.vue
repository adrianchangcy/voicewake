<template>    
    <div class="flex flex-col">
        <slot></slot>
        <div class="w-full h-4 border-2 border-theme-black relative">
            <!--background-->
            <div class="w-full h-full absolute">
                <div class="w-full h-full skeleton">
                </div>
            </div>
            <!--progress-->
            <div
                ref="progress_bar"
                class="w-full h-full absolute inset-0 origin-left progress-bar bg-theme-black after:bg-theme-lead"
                style="opacity: 0; transform: scaleX(0);"
            >
            </div>
        </div>
    </div>
</template>


<script lang="ts">
    import { PropType, defineComponent } from 'vue';
    import anime from 'animejs';

    //cumulative
    //pause must always be < duration
    //give sufficient space between duration and pause to prevent line-of-code race condition
    interface TimestampsMsTypes {
        durations: number[],
        scales: number[],
    }

    export default defineComponent({
        data(){
            return {
                part_pause_timeout: null as number|null,
            };
        },
        watch: {
            propStep(new_value:number|null){

                if(new_value === null){

                    this.endFinalPart(true);
                    return;
                }

                if(new_value >= this.propTimestampsMs.durations.length){

                    throw new Error('Invalid value: ' + new_value.toString());
                }

                if(new_value < (this.propTimestampsMs.durations.length - 1)){

                    this.startPart(new_value);

                }else{

                    this.endFinalPart(false);
                }
            },
        },
        props: {
            propTimestampsMs: {
                type: Object as PropType<TimestampsMsTypes>,
                required: true,
            },
            propStep: {
                type: Number as PropType<Number|null>,
            },
        },
        methods: {
            startPart(part_index:number) : void {

                //check that all lengths are the same

                const target_length = this.propTimestampsMs.durations.length;

                if(
                    target_length === 0 ||
                    target_length !== this.propTimestampsMs.scales.length
                ){

                    throw new Error('Must have > 0 parts and equal array lengths.');
                }

                //proceed
                //quirky code below fixes "anime's first time will scale while leaving subpixel gap"

                const target_el = this.$refs.progress_bar as HTMLElement;

                //remove
                anime.remove(target_el);

                const current_anime = anime.timeline({
                    targets: target_el,
                    easing: 'linear',
                    loop: false,
                    autoplay: false,
                });

                if(part_index === 0){

                    //subpixel gap solution

                    //declaring opacity-0 and scale-x-1 at style attribute did not help with anything
                    target_el.style.transform = 'scaleX(1)';
                    target_el.style.opacity = '0.01';

                    //reset element to desired initial state via anime
                    //do it here to prevent flashing, compared to immediate change via .style
                    current_anime.add({
                        opacity: 1,
                        scaleX: 0,
                        duration: 1,
                    });

                }else{

                    //has previous part unfinished
                    current_anime.add({
                        scaleX: this.propTimestampsMs.scales[part_index - 1],
                        duration: 100,
                    });
                }

                //actual anime
                //we do 0.75 so we can wait for overdue request
                current_anime.add({
                    scaleX: this.propTimestampsMs.scales[part_index] * 0.86,
                    duration: this.propTimestampsMs.durations[part_index] * 0.86,
                });

                current_anime.play();
            },
            endFinalPart(has_reset:boolean) : void {

                const target_el = this.$refs.progress_bar as HTMLElement;

                //remove
                anime.remove(target_el);

                anime({
                    targets: target_el,
                    easing: 'linear',
                    loop: false,
                    autoplay: true,
                    scaleX: 1,
                    duration: 100,
                    complete: ()=>{
                        if(has_reset === true){
                            target_el.style.transform = 'scaleX(0)';
                            target_el.style.opacity = '0';
                        }
                    },
                });
            },
        },
    });
</script>