<template>
    <VInputLabel
    class="left-0"
    for="click-to-record"
    >
        {{ propLabel }}
    </VInputLabel>
    <button
        @click.stop="[toggleMenu(), emitIsOpen()]"
        :class="[
            is_open ? 'border-theme-black' : 'border-theme-medium-gray shade-border-when-hover',
            'w-full h-20 px-4 py-2 border-2 rounded-lg'
        ]"
        id="click-to-record"
        type="button"
    >
        <!--ripples-->
        <div class="w-full h-[75%] top-0 bottom-0 m-auto relative">
            <div
                class="w-full h-full absolute"
            >
                <div class="h-full flex flex-row justify-between">
                    <div
                        v-for="volume_ripple in propBucketQuantity" :key="volume_ripple"
                        ref="volume_ripple"
                        class="h-full scale-y-0 origin-center"
                    >
                        <div
                            :class="[
                                propHasRecording ? 'bg-theme-black' : 'outline-1 outline outline-theme-dark-gray',
                                'left-0 right-0 mx-auto w-0.5 h-full'
                            ]"
                        >
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <span v-if="propHasRecording" class="sr-only">
            You have a recording
        </span>
        <span v-else class="sr-only">
            No recording
        </span>
        <span v-if="propIsOpen" class="sr-only">
            Close recording menu
        </span>
        <span v-else class="sr-only">
            Open recording menu
        </span>
    </button>
</template>


<script setup lang="ts">
    import VInputLabel from '/src/components/small/VInputLabel.vue';
</script>

<script lang="ts">
    //we don't keep VRecorderMenu in this component due to the inflexibility of button size =/= menu size
    import { defineComponent, PropType } from 'vue';
    import anime from 'animejs';

    export default defineComponent({
        data(){
            return{
                is_open: false,
            };
        },
        emits: ['isOpen'],
        mounted(){

        },
        props: {
            propLabel: String,
            propBucketQuantity: {
                type: Number,
                required: true,
            },
            propFileVolumes: {    //not sure if this is the best way to type this, but it looks ok
                type: Array as PropType<number[]>,
                default: () => [],
            },
            propHasRecording: {
                type: Boolean,
                default: false
            },
            propFileDuration: { //milliseconds
                type: Number,
                default: 0
            },
            propIsOpen: {
                type: Boolean,
                default: false
            },
        },
        computed: {
            getPrettyPropFileDuration() : string {

                if(this.propHasRecording === true){

                    return new Date(
                        this.propFileDuration
                        ).toISOString().substring(14, 19);

                }else{

                    return 'empty';
                }
            },
        },
        watch: {
            propIsOpen(new_value:boolean){
                this.is_open = new_value;
            },
            propFileVolumes(){

                this.adjustVolumeRipples();
            },
        },
        methods: {
            toggleMenu() : void {

                //this dictates whether VEventToneMenu is open
                this.is_open = !this.is_open;
                
            },
            emitIsOpen() : void {

                this.$emit('isOpen', this.is_open);
            },
            adjustVolumeRipples() : void {

                //we calculate height relative to most quiet and loudest parts
                //samples are expected to be between -1 and 1, but we get -0.0001 when no audio
                
                let scaleY_percentage = 0;

                for(let x=0; x < this.propFileVolumes.length; x++){

                    //expected volume range is -1 to 0, but our peaks at 0 audio is still -0.0001...
                    //so we recalibrate from lower and upper 50 to full 100
                    //instead of <0 ... =0, if you prefer 0 to be visible, do <0.05 ... =5
                    //UPDATE: non-zero feels more functional for end user
                    if(this.propFileVolumes[x] < 0.05){

                        scaleY_percentage = 0.05;

                    }else if(this.propFileVolumes[x] > 0.9){

                        //we max at 0.9 to make space for -+5% translateY anime
                        scaleY_percentage = 0.9;

                    }else{

                        scaleY_percentage = this.propFileVolumes[x];
                    }
                    
                    //add the deficit
                    // scaleY_percentage += volume_range_deficit;

                    //this performs fine, so do not add Tailwind transition, else it interferes
                    anime({
                        targets: (this.$refs.volume_ripple as HTMLElement[])[x],
                        scaleY: scaleY_percentage.toString(),
                        autoplay: true,
                        loop: false,
                        easing: 'easeInOutQuad',
                        duration: 200,
                    });
                }
            },
        },
    });
</script>