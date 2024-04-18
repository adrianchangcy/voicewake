<template>
    <!-- your specified width will be entirely clickable -->
    <!-- if your parent container causes slider to fire twice at edge, put touch-none to fix it -->
    <div class="touch-none">
        <div
            ref="slider"
            class="relative w-full h-full left-0 right-0 mx-auto cursor-pointer parent-trigger-double-width-when-hover"
            @pointerdown.prevent="[startDrag($event), doDrag($event)]"
        >
            <div
                class="w-2 absolute bg-theme-gray-3 dark:bg-dark-theme-gray-3 left-0 right-0 top-0 bottom-0 m-auto double-width-when-hover transition-transform"
            >
            </div>
            <!--this is just to patch up grey spot-->
            <div
                class="w-2 h-3 absolute bg-theme-lead dark:bg-dark-theme-lead left-0 right-0 mx-auto bottom-0"
            ></div>
            <div
                ref="slider_progress"
                class="w-2 absolute bg-theme-lead dark:bg-dark-theme-lead left-0 right-0 mx-auto top-2 bottom-2 origin-bottom"
            >
                <div
                    ref="slider_knob"
                    class="w-4 h-4 absolute -top-2 -left-1  bg-theme-black dark:bg-dark-theme-white-2"
                ></div>
            </div>
        </div>
    </div>
</template>


<script lang="ts">
    import { defineComponent } from 'vue';
    import VSliderTypes from '@/types/values/VSlider';

    //there are reasons we do it this way instead of <input type="range">
        //firefox does not support vertical orientation
        //the screen will move before <input> does, in a bad way

    export default defineComponent({

        data(){
            return {
                slider_dimension: null as DOMRect | null,   //reminder to parseFloat(val.toFixed(2)) to avoid negative exponent bugs
                slider_value: 0,
                is_dragging: false,
            };
        },
        props: {
            propSliderValue: {
                type: Number,
                required: true,
                default: 0
            },
        },
        emits: ['hasNewSliderValue', 'startDragSliderValue', 'stopDragSliderValue'],
        watch: {
            propSliderValue(new_value){

                //may be circular, but watchers don't trigger when value is the same
                this.mainUpdateSlider(new_value);
            },
        },
        methods: {
            emitDragSliderValue(e:PointerEvent, start_or_stop:"start"|"stop") : void {

                if(start_or_stop === "start"){

                    this.$emit('startDragSliderValue',
                        {
                            slider_value: this.slider_value,
                            pointer_type: e.pointerType
                        } as VSliderTypes
                    );
                
                }else if(start_or_stop === "stop"){

                    this.$emit('stopDragSliderValue',
                        {
                            slider_value: this.slider_value,
                            pointer_type: e.pointerType
                        } as VSliderTypes
                    );
                }
            },
            startDrag(e:PointerEvent){

                this.slider_dimension = (this.$refs.slider as HTMLElement).getBoundingClientRect();
                this.is_dragging = true;

                this.emitDragSliderValue(e, "start");
            },
            doDrag(e:PointerEvent){

                if(this.is_dragging === true && this.slider_dimension !== null){

                    //can use clientY, screenY, pageY, but they are calculated slightly differently
                    //clientY seems to work best
                    const user_y = e.clientY;
                    
                    if(user_y >= this.slider_dimension.top && user_y <= this.slider_dimension.bottom){
                        
                        this.slider_value = parseFloat(((this.slider_dimension.bottom - user_y) / this.slider_dimension.height).toFixed(2));

                    }else if(user_y < this.slider_dimension.top){

                        this.slider_value = 1;

                    }else if(user_y > this.slider_dimension.bottom){

                        this.slider_value = 0;
                    }

                    this.animeSlider();
                    this.$emit('hasNewSliderValue', this.slider_value);

                    //troubleshoot if needed
                    // console.log("==========================");
                    // console.log('user_y: '+user_y);
                    // console.log('slider_top: '+this.slider_dimension.top);
                    // console.log('slider_bottom: '+this.slider_dimension.bottom);
                    // console.log(this.slider_value);
                    // console.log("==========================");
                }
            },
            stopDrag(e:PointerEvent) : void {

                if(this.is_dragging === false){

                    return;
                }

                this.is_dragging = false;
                this.emitDragSliderValue(e, "stop");
            },
            animeSlider() : void {

                //animation only

                //we must not go fully 0, else it hides slider_knob
                let scale_value = this.slider_value;

                if(this.slider_value === 0){

                    scale_value = 0.001;
                }

                //handle visual representation
                (this.$refs.slider_progress as HTMLElement).style.transform = 'scaleY(' + scale_value.toString() + ')';
                
                //since we have no px to refer to for translate due to v-show, we do inverse scale trick
                (this.$refs.slider_knob as HTMLElement).style.transform = 'scaleY(' + (1 / scale_value).toString() + ')';
            },
            mainUpdateSlider(new_value:number) : void {

                //you can call this from parent, and everything at VSliderYSmall will update accordingly
                if(new_value >= 0 && new_value <= 1){

                    this.slider_value = new_value;
                    this.animeSlider();
                }
            },
        },
        mounted(){

            this.mainUpdateSlider(this.propSliderValue);

            //attach listeners to window for Y coordinate
            //hovering over :disabled elements causes unresponsiveness for mousedown and touchstart, not sure about pointer
            window.addEventListener('pointermove', this.doDrag);
            window.addEventListener('pointerup', this.stopDrag);
            window.addEventListener('pointercancel', this.stopDrag);
        },
        beforeUnmount(){

            //remove listeners
            window.removeEventListener('pointermove', this.doDrag);
            window.removeEventListener('pointerup', this.stopDrag);
            window.removeEventListener('pointercancel', this.stopDrag);
        },
    });
</script>