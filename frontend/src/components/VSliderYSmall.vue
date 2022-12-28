<template>
    <!-- specify your own height -->
    <div
        class="relative p-2 w-fit left-0 right-0 mx-auto touch-none"
        @mousedown.stop="[startDrag(), doDrag($event)]"
        @touchstart.stop="[startDrag(true), doDrag($event)]"
    >
        <!--need 99% to remove dead pixel-->
        <div
            ref="slider"
            class="w-2 h-[99%] absolute bg-theme-idle left-0 right-0 mx-auto top-0 bottom-0"
        ></div>
        <div
            ref="current_position"
            class="w-2 absolute bg-theme-dominant left-0 right-0 mx-auto bottom-0"
        >
            <div
                class="w-4 h-4 bg-theme-black left-0 right-0 top-0 absolute -translate-y-2 -translate-x-1"
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
                    this.repositionSlider(this.propSliderValue);
                }
            },
            is_dragging(new_value){

                this.$emit('hasNewIsDraggingValue', new_value);
            },
        },
        methods: {
            startDrag(is_touch=false){

                this.is_dragging = true;
                this.is_touch = is_touch;
            },
            doDrag(event){

                //for mouse, we need these to avoid text highlighting, accidental permanent drag state, etc.
                //for touch, we need these to avoid mouse firing
                if(event.cancelable === true){
                    
                    event.preventDefault();
                }

                if(this.is_dragging === true){

                    let slider_rect = this.$refs.slider.getBoundingClientRect();

                    //can use clientY, screenY, pageY, but pageY is most accurate in this context
                    let user_y = undefined;

                    if(this.is_touch === true){

                        user_y = event.touches[0].clientY;
                        
                    }else{

                        user_y = event.clientY;
                    }

                    if(user_y >= slider_rect.top && user_y <= slider_rect.bottom){

                        this.slider_value = ((slider_rect.bottom - user_y) / slider_rect.height).toFixed(2) * 1;

                    }else if(user_y < slider_rect.top){

                        this.slider_value = 1;

                    }else if(user_y > slider_rect.bottom){

                        this.slider_value = 0;
                    }

                    this.repositionSlider(this.slider_value);
                    this.emitNewSliderValue();

                    //troubleshoot if needed
                    // console.log("==========================");
                    // console.log('user_y: '+user_y);
                    // console.log('slider_top: '+slider_rect.top);
                    // console.log('slider_bottom: '+slider_rect.bottom);
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
            repositionSlider(new_value){

                //handle visual representation
                this.$refs.current_position.style.height = (new_value * 100).toString() + '%';
            },
            emitNewSliderValue(){

                this.$emit('hasNewSliderValue', this.slider_value);
            },
        },        
    }
</script>