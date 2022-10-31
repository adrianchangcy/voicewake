<template>
    <div ref="audio_visualiser" class="w-full h-20 p-2 grid grid-cols-max grid-flow-col place-items-center">
        <div
            v-for="volume_ripple in bucket_quantity" :key="volume_ripple"
            :class="['volume-ripple-'+volume_ripple+' col-span-1 w-2 bg-theme-black']"
            ref="volume_ripple"
        ></div>
    </div>
</template>

<script>

    import anime from 'animejs';

    export default{
        data(){
            return {
                bucket_quantity: 20,
                file_volumes: [],
                min_volume: -1,     //samples are in Float32Array, from -1 to 1
                max_volume: 1,      //samples are in Float32Array, from -1 to 1
            };
        },
        mounted(){

            //bar is 2/4, so 1/4 space on both sides
        },
        props: {
            propFile: Object,
        },
        watch: {
            async propFile(new_value){

                const context = new AudioContext();

                await new_value.arrayBuffer()
                    .then(buffer => context.decodeAudioData(buffer))
                    .then(decoded_audio => decoded_audio.getChannelData(0)) //specified 2 but got 1
                    .then(audio_data => this.getVolumes(audio_data));

                this.adjustVolumeRipples();
            },
        },
        methods: {
            animeLoading(target, translateY_start) {

                let starting_point = translateY_start.toString() + '%';

                anime({
                    targets: target,
                    translateY: ['0%', starting_point, '-'+starting_point, '0%'],
                    autoplay: true,
                    easing: 'linear',
                    loop: true,
                    direction: 'alternate',
                });
            },
            adjustVolumeRipples(){

                //since samples are between -1 and 1, 0 means 50%
                let current_height = 0;

                for(let x=0; x < this.bucket_quantity; x++){
                    
                    if(this.file_volumes[x] >= 0 && this.file_volumes[x] < 0.1){

                        current_height = (this.file_volumes[x] * 100) + 20;

                    }else if(this.file_volumes[x] >= 0.1){

                        current_height = (this.file_volumes[x] * 100) + 50;
                        
                    }else{
                            
                        current_height = ((this.file_volumes[x] * -1) * 100) - 50;
                    }
                    this.$refs.volume_ripple[x].style.height = current_height.toString() + '%';
                }
            },
            getVolumes(audio_data){

                let bucket_peaks = [];
                let bucket_threshold = audio_data.length / this.bucket_quantity;
                //-1 to adjust for for-loop and lets us run code on last sample of each bucket (avoids < _ -1)
                let bucket_threshold_count = bucket_threshold - 1;
                let bucket_max = 0;

                for(let x = 0; x < audio_data.length; x++){
                    
                    //check if we are at last sample of current bucket
                    if(x === bucket_threshold_count){

                        //store max peak
                        bucket_peaks.push(bucket_max);

                        //reset
                        bucket_max = 0;

                        //shift to next bucket
                        bucket_threshold_count += bucket_threshold;
                    }
                    
                    //evaluate max peak in current bucket
                    if(audio_data[x] > bucket_max){

                        bucket_max = audio_data[x];
                    }
                }

                //store highest peaks
                this.file_volumes = bucket_peaks;
            },
        }
    }
</script>