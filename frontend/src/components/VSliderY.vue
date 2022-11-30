<template>
    <!-- specify your own height -->
    <div
        @click="instantDrag($event)"
        @mousedown="startDrag()"
        @touchstart="startDrag()"
        class="relative p-2 w-fit left-0 right-0 mx-auto touch-none"
    >
        <div
            ref="slider"
            class="w-2 h-full absolute bg-theme-disabled left-0 right-0 mx-auto bottom-0 rounded-full"
        ></div>
        <div
            ref="current_position"
            class="w-2 absolute bg-theme-dominant left-0 right-0 mx-auto bottom-0 rounded-full"
        >
            <div
                class="w-4 h-4 rounded-full bg-theme-black left-0 right-0 top-0 absolute -translate-y-2 -translate-x-1"
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
            propDefaultValue: Number,
        },
        watch: {

            propDefaultValue(new_value){

                if(this.slider_value !== new_value && this.propDefaultValue >= 0 && this.propDefaultValue <= 1){

                    //using watcher is important past initial 0 values, i.e. if localStorage exists
                    this.slider_value = this.propDefaultValue;
                    this.repositionSlider(this.propDefaultValue);
                }
            },
        },
        methods: {
            startDrag(){

                this.is_dragging = true;
            },
            doDrag(event){

                //when event.passive is true, calls to .preventDefault() will be ignored

                if(this.is_dragging === true){

                    let slider_rect = this.$refs.slider.getBoundingClientRect();

                    //can use clientY, screenY, pageY, but pageY is most accurate in this context
                    let user_y = undefined;

                    //instead of using listeners (still a bit unreliable), we check on undefined
                    if(event.clientY === undefined){

                        //touch
                        user_y = event.touches[0].clientY;

                    }else{

                        //mouse
                        //we need these to avoid text highlighting, accidental permanent drag state, etc.
                        event.stopPropagation();
                        event.preventDefault();
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
            },
            instantDrag(event){

                this.startDrag();
                this.doDrag(event);
                this.stopDrag();
            },
            repositionSlider(value){

                //handle visual representation
                this.$refs.current_position.style.height = (value * 100).toString() + '%';
            },
            emitNewSliderValue(){

                this.$emit('hasNewSliderValue', this.slider_value);
            },
        },
        emits: ['hasNewSliderValue'],
        
    }
</script>