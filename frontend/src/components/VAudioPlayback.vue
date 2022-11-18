<template>
    <audio
        ref="audio_playback"
        controls
        class="w-full p-2 hidden"
        @loadedmetadata="processPlaybackDuration()"
        @ended="is_playing = false"
    ></audio>
    <div class="h-fit border-2 border-theme-black/5 p-2">
        <div class="w-full h-20 relative border-2 border-theme-black/5 p-2">
            <!-- <div class="bg-teal-400/50 w-1 h-full left-0"></div> -->
            <div
                ref="audio_visualiser"
                :class="[
                    final_file !== null ? 'cursor-pointer' : '',
                    'w-full h-full py-2 grid grid-cols-max grid-flow-col gap-x-1 place-items-center'
                ]"
                @click.prevent="navigateAudioVisualiser($event)"
            >
                <div
                    v-for="volume_ripple in bucket_quantity" :key="volume_ripple"
                    :class="[
                        (current_playback_state === null ? 'hidden' : ''),
                        (current_playback_state === 'empty' ? 'bg-theme-idle' : ''),
                        (current_playback_state === 'recording' ? 'bg-red-600' : ''),
                        (current_playback_state === 'has_file' ? 'bg-theme-black' : ''),
                        'col-span-1 w-1'
                    ]"
                    ref="volume_ripple"
                ></div>
            </div>
        </div>
        <div
            :class="[
                final_file === null ? 'invisible' : 'block',
                'w-full h-fit text-center py-2'
            ]"
        >
            <span>00:00 / {{pretty_final_file_duration}}</span>
        </div>
        <div class="grid grid-rows-1 grid-cols-3 grid-flow-col pb-2">
            <VActionButtonSmall
                @click.prevent="togglePlaybackPlayPause()"
                :class="[
                    final_file === null ? 'text-theme-disabled cursor-not-allowed' : 'text-theme-black',
                    'row-start-1 col-start-2 row-span-1 col-span-1 transition-colors duration-200 ease-in-out'
                ]"
                :disabled="final_file === null"
            >
                <i v-if="is_playing" class="fas fa-pause"></i>
                <i v-else class="fas fa-play"></i>
            </VActionButtonSmall>
        </div>
        <!-- playback option menus -->
        <div class="relative grid grid-cols-3 gap-2 text-theme-black">
            <VBox
                class="
                    w-full h-32 col-start-1 col-span-1 absolute text-center text-theme-black bottom-2
                    grid grid-rows-3 divide-y divide-theme-black/5
                "
            >
                <button 
                    @click.prevent="changePlaybackSpeed(1.5)"
                    :class="[playback_speed === 1.5 ? 'bg-theme-dominant' : 'bg-none' , 'row-span-1 p-2']"
                >1.5</button>
                <button 
                    @click.prevent="changePlaybackSpeed(1)"
                    :class="[playback_speed === 1 ? 'bg-theme-dominant' : 'bg-none' , 'row-span-1 p-2']"
                >Normal</button>
                <button 
                    @click.prevent="changePlaybackSpeed(0.5)"
                    :class="[playback_speed === 0.5 ? 'bg-theme-dominant' : 'bg-none' , 'row-span-1 p-2']"
                >0.5</button>
            </VBox>
            <TransitionFade>
            <VBox
                class="
                    w-full h-32 col-start-3 col-span-1 absolute text-center bottom-2 p-4
                "
            >
                <VSliderY
                    ref="volume_slider"
                    :propDefaultValue="playback_volume"
                    @hasNewSliderValue="changePlaybackVolume($event)"
                    class="h-full"
                />
            </VBox>
            </TransitionFade>
        </div>
        <div class="grid grid-rows-1 grid-cols-3 grid-flow-col gap-2">
            <VActionButtonSmall
                @click.prevent=""
                :class="[
                    final_file === null ? 'text-theme-disabled cursor-not-allowed' : 'text-theme-black',
                    'row-start-1 col-span-1 transition-colors duration-200 ease-in-out'
                ]"
                :disabled="final_file === null"
            >
                <i class="fas fa-forward -rotate-90"></i>
            </VActionButtonSmall>
            <VActionButtonSmall
                @click.prevent=""
                :class="[
                    final_file === null ? 'text-theme-disabled cursor-not-allowed' : 'text-theme-black',
                    'row-start-1 col-span-1 transition-colors duration-200 ease-in-out'
                ]"
                :disabled="final_file === null"
            >
                <i class="fas fa-repeat"></i>
            </VActionButtonSmall>
            <VActionButtonSmall
                @click.prevent="togglePlaybackVolumeOptions()"
                :class="[
                    final_file === null ? 'text-theme-disabled cursor-not-allowed' : 'text-theme-black',
                    'row-start-1 col-span-1 transition-colors duration-200 ease-in-out'
                ]"
                :disabled="final_file === null"
            >
                <i
                    :class="[
                        (playback_volume === 0 ? 'fas fa-volume-xmark' : ''),
                        (playback_volume <= 0.25 ? 'fas fa-volume-off' : ''),
                        (playback_volume <= 0.5 ? 'fas fa-volume-low' : ''),
                        (playback_volume <= 1 ? 'fas fa-volume-high' : ''),
                        (is_playback_volume_options_open ? '-rotate-90' : 'rotate-0'),
                        'transition duration-200 ease-in-out'
                    ]"
                ></i>
            </VActionButtonSmall>
        </div>
    </div>
</template>


<script setup>

    import VActionButtonSmall from './VActionButtonSmall.vue';
    import VSliderY from './VSliderY.vue';
    import VBox from './VBox.vue';
    import TransitionFade from '/src/transitions/TransitionFade.vue';
</script>

<script>

    import anime from 'animejs';

    export default{
        data(){
            return {
                final_file: null,
                final_file_duration: 0, //float seconds
                pretty_final_file_duration: '00:00',
                is_playing: false,

                playback_speed: 1,  //accepts 0 to 2
                playback_volume: 0.5, //accepts 0 to 1

                is_playback_speed_options_open: false,
                is_playback_volume_options_open: false,

                lowest_volume: null,
                highest_volume: null,
                is_ready_to_navigate: false,
                playback_states: ['empty', 'recording', 'has_file'],
                current_playback_state: null,
                bucket_quantity: 20,
                file_volumes: [],
                min_volume: -1,     //samples are in Float32Array, from -1 to 1
                max_volume: 1,      //samples are in Float32Array, from -1 to 1
            };
        },
        components: {
            
            VActionButtonSmall,
            VSliderY,
            VBox,
            TransitionFade,
        },
        mounted(){

            //playback speed, accepts 0 to 2, default 1
            //also convert from localStorage's String back to Float
            if(window.localStorage.playback_speed === undefined){

                this.playback_speed = 1;

            }else{

                this.playback_speed = parseFloat(window.localStorage.playback_speed);
            }
            
            //playback speed, accepts 0 to 1, default 0.5
            //also convert from localStorage's String back to Float
            if(window.localStorage.playback_volume === undefined){

                this.playback_volume = 0.5;

            }else{

                this.playback_volume = parseFloat(window.localStorage.playback_volume);
            }

            //set audio visualiser default
            //bar is 2/4, so 1/4 space on both sides
            for(let x=0; x < this.bucket_quantity; x++){

                this.$refs.volume_ripple[x].style.height = '50%';
            }
            
            //initialise with 'empty' state
            this.current_playback_state = this.playback_states[0];
            this.animePlayback();

        },
        props: {
            propFile: Object,
            propIsRecording: Boolean,
        },
        watch: {
            async propFile(new_value){

                this.final_file = new_value;

                if(new_value === null){

                    return false;
                }

                const context = new AudioContext();

                await new_value.arrayBuffer()
                    .then(buffer => context.decodeAudioData(buffer))
                    .then(decoded_audio => decoded_audio.getChannelData(0)) //specified 2 but got 1
                    .then(audio_data => this.getVolumes(audio_data))
                    .then(() => this.current_playback_state = this.playback_states[2])
                    .then(() => this.animePlayback())
                    .then(() => this.adjustVolumeRipples())
                    .then(() => this.attachRecordedAudioToPlayback());
            },
            propIsRecording(new_value){

                if(new_value === false){

                    return false;
                }

                this.current_playback_state = this.playback_states[1];
                this.animePlayback();
            },
        },
        methods: {
            changePlaybackSpeed(new_value){

                this.$refs.audio_playback.playbackRate = new_value;
                window.localStorage.playback_speed = new_value;
            },
            changePlaybackVolume(new_value){
                
                this.$refs.audio_playback.volume = new_value;
                this.playback_volume = new_value;
                window.localStorage.playback_volume = new_value;
            },
            togglePlaybackSpeedOptions(){

                this.is_playback_speed_options_open = !this.is_playback_speed_options_open;
            },
            togglePlaybackVolumeOptions(){

                this.is_playback_volume_options_open = !this.is_playback_volume_options_open;
            },
            togglePlaybackPlayPause(){

                const target = this.$refs.audio_playback;

                //note that when .ended is true, .paused is also true
                //seems not possible to handle .ended here, so we handle it at element
                if(target.paused === true){
                    
                    target.play();
                    this.is_playing = true;

                }else if(target.playing === true){

                    target.pause();
                    this.is_playing = false;
                }
            },
            animePlayback(){

                const targets = this.$refs.volume_ripple;

                //reset all elements
                //reset all translates to 0
                anime.remove(targets);


                // let starting_point = translateY_start.toString() + '%';
                switch(this.current_playback_state){

                    case this.playback_states[0]:
                        anime({
                            targets: targets,
                            translateY: ['0%', '-50%', '50%', '0%'],
                            autoplay: true,
                            delay: anime.stagger(100),
                            easing: 'linear',
                            loop: true,
                        });
                        break;
                    
                    case this.playback_states[1]:
                        //'recording'
                        //reset height
                        anime({
                            targets: targets,
                            translateY: ['0%'],
                            height: '50%',
                            autoplay: true,
                            easing: 'linear',
                            loop: false,
                            duration: 200,
                        });
                        break;

                    case this.playback_states[2]:
                        //'has_file'
                        //handled by adjustVolumeRipples()

                        //use opacity instead of transition-all for better performance
                        break;

                    default:
                        console.log('State is currently null or not one of the declared playback_states.');
                        return false;
                }

            },
            getVolumes(audio_data){

                let bucket_peaks = [];
                let bucket_threshold = Math.round(audio_data.length / this.bucket_quantity);
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

                //store lowest and highest volumes
                this.lowest_volume = this.arrayMin(audio_data);
                this.highest_volume = this.arrayMax(audio_data);
            },
            adjustVolumeRipples(){

                //we calculate height relative to most quiet and loudest parts
                //samples are between -1 and 1
                // const volume_range = this.highest_volume - this.lowest_volume;
                const volume_range = 2;

                // //now we find the highest volume, and its distance from max height
                // //we will shift everything based on this difference
                // let volume_range_deficit = 0;
                // let highest_file_volume = null;

                // highest_file_volume = this.arrayMax(this.file_volumes);

                // if(highest_file_volume < 0){

                //     volume_range_deficit = 100 - 50 - (((highest_file_volume * -1) / volume_range) * 100);
                    
                // }else{

                //     volume_range_deficit = 100 - ((highest_file_volume / volume_range) * 100);
                // }

                //shift half to make it readable, not full, else it'll be globally inconsistent for user
                // volume_range_deficit = volume_range_deficit / 2;

                let current_height = 0;

                for(let x=0; x < this.bucket_quantity; x++){

                    if(this.file_volumes[x] < 0){
                        
                        //we keep <0 below 50%, because -1 to 0 is 0% to 50%
                        current_height = (((this.file_volumes[x] * -1) / volume_range) * 100) - 50;

                    }else{

                        current_height = (this.file_volumes[x] / volume_range) * 100;
                    }

                    //add the deficit
                    // current_height += volume_range_deficit;

                    //this performs fine, so do not add Tailwind transition, else it interferes
                    anime({
                        targets: this.$refs.volume_ripple[x],
                        height: current_height.toString() + '%',
                        autoplay: true,
                        loop: false,
                        easing: 'easeInOutQuad',
                        duration: 200,
                    });
                }
            },
            attachRecordedAudioToPlayback(){

                //attach file into <audio>
                this.$refs.audio_playback.src = URL.createObjectURL(this.final_file);

                this.$refs.audio_playback.onload = function(){
                    //free the memory
                    return URL.revokeObjectURL(this.$refs.audio_playback.src);
                };

                return true;
            },
            navigateAudioVisualiser(event){

                if(this.is_ready_to_navigate === false){
                    
                    return false;
                }

                let rect = event.currentTarget.getBoundingClientRect();

                //get user's x relative to screen - element's x relative to screen
                let mouse_x_in_element = event.clientX - rect.left;

                this.$refs.audio_playback.currentTime = (mouse_x_in_element / (rect.right - rect.left)) * this.final_file_duration;
            },
            processPlaybackDuration(){

                this.is_ready_to_navigate = false;

                //there's a bug that gives us 'Infinity'
                //this is how we fix it
                //https://stackoverflow.com/a/69512775

                //function needs a name to add/remove event listener
                //need to use ()=>{} to preserve 'this' reference
                const handler = ()=>{
                    this.$refs.audio_playback.currentTime = 0;
                    this.$refs.audio_playback.removeEventListener('timeupdate', handler);
                    this.final_file_duration = this.$refs.audio_playback.duration;
                    //mm:ss
                    this.pretty_final_file_duration = new Date(this.final_file_duration * 1000).toISOString().substring(14, 19);
                    this.is_ready_to_navigate = true;
                };

                if(this.$refs.audio_playback.duration == 'Infinity'){

                    this.$refs.audio_playback.currentTime = 1e101;
                    this.$refs.audio_playback.addEventListener('timeupdate', handler);

                }else{

                    this.final_file_duration = this.$refs.audio_playback.duration;
                    this.is_ready_to_navigate = true;
                }

                
                //don't try to access this.final_file_duration precisely here
                //you'll get 0, but if you check via watch, the value does change
            },

        }
    }
</script>