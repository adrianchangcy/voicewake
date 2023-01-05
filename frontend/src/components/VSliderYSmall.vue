<template>
    <!-- specify your own height -->
    <div
        ref="slider"
        class="relative p-2 w-fit left-0 right-0 mx-auto touch-none"
        @mousedown.stop="[startDrag(), doDrag($event)]"
        @touchstart.stop="[startDrag(true), doDrag($event)]"
    >
        <!--need 99% to remove dead pixel-->
        <div
            class="w-2 h-[99%] absolute bg-theme-idle left-0 right-0 mx-auto top-0 bottom-0"
        ></div>
        <div
            ref="slider_progress"
            class="w-2 h-full absolute bg-theme-dominant left-0 right-0 mx-auto bottom-0 origin-bottom"
        >
            <div
                ref="slider_knob"
                class="w-4 h-4 bg-theme-black absolute -left-1 -top-2"
            ></div>
        </div>
    </div>
</template>


<script>

    //there are reasons we do it this way instead of <input type="range">
        //firefox does not support vertical orientation
        //the screen will move before <input> does, in a bad way

    export default {

        data(){
            return {
                slider_dimension: null,
                slider_value: 0,
                is_dragging: false,
                is_touch: false,
            };
        },
        mounted(){

            //attach listeners to window for mouse Y
            window.addEventListener('mousemove', this.doDrag);  //hovering over :disabled elements causes unresponsiveness
            window.addEventListener('touchmove', this.doDrag);
            window.addEventListener('mouseup', this.stopDrag);
            window.addEventListener('touchend', this.stopDrag);
        },
        beforeUnmount(){

            //remove listeners
            window.removeEventListener('mousemove', this.doDrag);
            window.removeEventListener('touchmove', this.doDrag);
            window.removeEventListener('mouseup', this.stopDrag);
            window.removeEventListener('touchend', this.stopDrag);
        },
        props: {
            propSliderValue: Number,
        },
        emits: ['hasNewSliderValue', 'hasNewIsDraggingValue'],
        watch: {

            propSliderValue(new_value){

                if(this.slider_value !== new_value && this.propSliderValue >= 0 && this.propSliderValue <= 1){

                    //using watcher is important past initial 0 values, i.e. if localStorage exists
                    this.slider_value = this.propSliderValue;
                }

                this.repositionSlider();
            },
            is_dragging(new_value){

                this.$emit('hasNewIsDraggingValue', new_value);
            },
        },
        methods: {
            startDrag(is_touch=false){

                this.slider_dimension = this.$refs.slider.getBoundingClientRect();

                this.is_dragging = true;
                this.is_touch = is_touch;
            },
            doDrag(event=null){

                //for mouse, we need these to avoid text highlighting, accidental permanent drag state, etc.
                //for touch, we need these to avoid mouse firing
                if(event !== null && event.cancelable === true){
                    
                    event.preventDefault();
                }

                if(this.is_dragging === true){

                    //can use clientY, screenY, pageY, but pageY is most accurate in this context
                    let user_y = undefined;

                    if(this.is_touch === true){

                        user_y = event.touches[0].clientY;
                        
                    }else{

                        user_y = event.clientY;
                    }

                    if(user_y >= this.slider_dimension.top && user_y <= this.slider_dimension.bottom){

                        this.slider_value = ((this.slider_dimension.bottom - user_y) / this.slider_dimension.height).toFixed(2) * 1;

                    }else if(user_y < this.slider_dimension.top){

                        this.slider_value = 1;

                    }else if(user_y > this.slider_dimension.bottom){

                        this.slider_value = 0;
                    }

                    this.repositionSlider(this.slider_value);
                    this.emitNewSliderValue();

                    //troubleshoot if needed
                    // console.log("==========================");
                    // console.log('user_y: '+user_y);
                    // console.log('slider_top: '+this.slider_dimension.top);
                    // console.log('slider_bottom: '+this.slider_dimension.bottom);
                    // console.log(this.slider_value);
                    // console.log("==========================");
                }
            },
            stopDrag(){

                this.is_dragging = false;

                //we reset touch detection on every startDrag() and stopDrag()
                //so we get latest status of is_touch
                this.is_touch = false;
            },
            repositionSlider(){

                //we must not go fully 0, else it hides slider_knob
                let scale_value = this.slider_value;

                if(this.slider_value === 0){

                    scale_value = 0.001;
                }

                //handle visual representation
                this.$refs.slider_progress.style.transform = 'scaleY(' + scale_value.toString() + ')';
                
                //since we have no px to refer to for translate due to v-show, we do inverse scale trick
                this.$refs.slider_knob.style.transform = 'scaleY(' + (1 / scale_value).toString() + ')';
            },
            emitNewSliderValue(){

                this.$emit('hasNewSliderValue', this.slider_value);
            },
        },
    }
</script>