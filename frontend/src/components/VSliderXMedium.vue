<template>
    <!-- specify your own height -->
    <div
        class="relative p-2 top-0 bottom-0 my-auto touch-none"
        @mousedown.stop="[startDrag(), doDrag($event)]"
        @touchstart.stop="[startDrag(true), doDrag($event)]"
    >
        <!--need 99% to remove dead pixel-->
        <div
            ref="slider"
            class="w-[99%] h-1 absolute bg-theme-idle top-0 bottom-0 left-0 right-0 m-auto rounded-full"
        ></div>
        <div
            ref="current_position"
            class="h-1 absolute bg-theme-dominant top-0 bottom-0 my-auto left-0 rounded-l-full"
        >
            <div
                class="w-4 h-4 rounded-full bg-theme-black top-0 bottom-0 my-auto right-0 absolute translate-x-2"
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
            window.addEventListener('mousemove', this.doDrag);
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
            propIsEnabled: {
                type: Boolean,
                default: true,
            },
        },
        emits: ['hasNewSliderValue'],
        watch: {

            propSliderValue(new_value){

                if(this.slider_value !== new_value && this.propSliderValue >= 0 && this.propSliderValue <= 1){

                    //using watcher is important past initial 0 values, i.e. if localStorage exists
                    this.slider_value = this.propSliderValue;
                    this.repositionSlider(this.propSliderValue);
                }
            },
        },
        methods: {
            startDrag(is_touch=false){

                if(this.propIsEnabled === false){

                    return false;
                }

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

                    //can use clientX, screenX, pageX, but pageX is most accurate in this context
                    let user_x = undefined;

                    if(this.is_touch === true){

                        user_x = event.touches[0].clientX;

                    }else{

                        user_x = event.clientX;
                    }

                    if(user_x >= slider_rect.left && user_x <= slider_rect.right){

                        this.slider_value = ((user_x - slider_rect.left) / slider_rect.width).toFixed(2) * 1;

                    }else if(user_x < slider_rect.left){

                        this.slider_value = 0;

                    }else if(user_x > slider_rect.right){

                        this.slider_value = 1;
                    }

                    this.repositionSlider(this.slider_value);
                    this.emitNewSliderValue();

                    //troubleshoot if needed
                    // console.log("==========================");
                    // console.log('user_x: '+user_x);
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
                //some browsers also trigger both touch + mouse events together
                this.is_touch = false;
            },
            repositionSlider(new_value){

                //handle visual representation
                this.$refs.current_position.style.width = (new_value * 100).toString() + '%';
            },
            emitNewSliderValue(){

                this.$emit('hasNewSliderValue', this.slider_value);
            },
        },        
    }
</script>