<template>
    <audio
        ref="audio_playback"
        controls
        class="hidden"
        @loadedmetadata="getPlaybackDuration()"
        @ended="is_playing = false"
        @play="is_playing = true"
        @timeupdate="[updateCurrentPlaybackTime()]"
        @canplay="current_playback_state = playback_states[2]"
        @waiting="current_playback_state = playback_states[3]"
        @progress="current_playback_state = playback_states[3]"
        @error="current_playback_state = playback_states[4]"
        @stalled="current_playback_state = playback_states[4]"
        :loop="is_repeat"
    ></audio>
    <!--22.5rem is h-60 + h-30-->
    <div class="text-center h-[20rem] relative" tabindex="0">
        <!--extras-->
        <div ref="playback_extras" class="absolute w-full h-20 bottom-0 px-3">
                <!--navigation slider-->
                <div class="w-full h-10">
                    <VSliderXMedium
                        ref="playback_navigation"
                        class="w-full h-full"
                        :propSliderValue="0"
                        @hasNewSliderValue="handlePlaybackDrag($event)"
                    />
                </div>
                <!--timers-->
                <div class="w-full h-10 text-base items-center grid grid-cols-4">
                    <span class="col-start-1 col-span-1 text-left">{{current_playback_time}}</span>
                    <span class="col-start-4 col-span-1 text-right">{{playback_duration}}</span>
                </div>
        </div>
        <!--main-->
        <div ref="playback_main" class="absolute w-full">
            <div class="w-full h-full relative">
                <!--audio bars-->
                <div ref="playback_progress" class="absolute h-full left-0 rounded-lg px-3"></div>
                <div class="absolute w-full h-full grid grid-cols-max grid-flow-col gap-1 place-items-center px-3">
                    <div
                        v-for="volume_ripple in bucket_quantity" :key="volume_ripple"
                        :class="[
                            (current_playback_state === null ? 'hidden' : ''),
                            (current_playback_state === playback_states[0] ? 'bg-theme-idle' : ''),
                            (current_playback_state === playback_states[4] ? 'bg-theme-danger' : ''),
                            'col-span-1 w-0.5 bg-theme-black'
                        ]"
                        ref="volume_ripple"
                    ></div>
                </div>
                <!--recording visualiser-->
                <div
                    class="absolute w-40 h-40 left-0 right-0 top-0 bottom-0 m-auto"
                >
                    <div class="relative w-full h-full bg-pink-400">
                        <div
                            ref="volume_analyser_circle_0"
                            class="absolute w-0 h-0 left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-dominant/60"
                        ></div>
                        <div
                            ref="volume_analyser_circle_1"
                            class="absolute w-0 h-0 left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-dominant/40"
                        ></div>
                        <div
                            ref="volume_analyser_circle_2"
                            class="absolute w-0 h-0 left-0 right-0 top-0 bottom-0 m-auto rounded-full bg-theme-dominant/20"
                        ></div>
                    </div>
                </div>
                <!--options-->
                <VBox
                    :class="[
                        final_file === null ? 'text-theme-disabled' : 'text-theme-black',
                        'hidden w-full h-full grid grid-rows-5 grid-cols-4 items-center rounded-lg gap-2 p-2 text-xl'
                    ]"
                >
                    <div class="row-start-2 row-span-3 col-start-1 col-span-1 h-full">
                        <button
                            :disabled="final_file === null"
                            :class="[
                                final_file === null ? 'cursor-not-allowed' : '',
                                'w-full h-full'
                            ]"
                        >
                            <i class="fas fa-rotate-left"></i>
                            <br>
                            <span>10</span>
                        </button>
                    </div>
                    <div class="row-start-2 row-span-3 col-start-2 col-span-2 h-full">
                        <button
                            @click.prevent="togglePlaybackPlayPause()"
                            :disabled="final_file === null"
                            :class="[
                                final_file === null ? 'cursor-not-allowed' : '',
                                'w-full h-full'
                            ]"
                        >
                            <i
                                :class="[
                                    is_playing? 'fa-pause' : 'fa-play',
                                    'fas text-4xl'
                                ]"
                            ></i>
                        </button>
                    </div>
                    <div class="row-start-2 row-span-3 col-start-4 col-span-1 h-full">
                        <button
                            :disabled="final_file === null"
                            :class="[
                                final_file === null ? 'cursor-not-allowed' : '',
                                'w-full h-full'
                            ]"
                        >
                            <i class="fas fa-rotate-right"></i>
                            <br>
                            <span>10</span>
                        </button>
                    </div>
                    <!--playback speed-->
                    <div
                        ref="playback_speed_options_button"
                        class="row-start-5 row-span-1 col-start-2 col-span-1 h-full"
                    >
                        <div class="relative w-full h-0">
                            <TransitionFade>
                                <VBox
                                    v-show="is_playback_speed_options_open"
                                    v-click-outside="{
                                        related_data: 'is_playback_speed_options_open',
                                        exclude: ['playback_speed_options_button']
                                    }"
                                    class="
                                        w-full h-32 absolute text-center text-theme-black bottom-1
                                        grid grid-rows-3 divide-y divide-theme-black/5
                                    "
                                >
                                        <div class="row-span-1">
                                            <button
                                                @click.prevent="changePlaybackRate(1.5)"
                                                :class="[
                                                    playback_rate === 1.5 ? 'bg-theme-dominant' : 'bg-none' ,
                                                    'w-full h-full transition-colors duration-200 ease-in-out p-2 rounded-t-lg'
                                                ]"
                                            >
                                                1.5
                                            </button>
                                        </div>
                                        <div class="row-span-1">
                                            <button
                                                @click.prevent="changePlaybackRate(1)"
                                                :class="[
                                                    playback_rate === 1 ? 'bg-theme-dominant' : 'bg-none' ,
                                                    'w-full h-full transition-colors duration-200 ease-in-out p-2'
                                                ]"
                                            >
                                                1
                                            </button>
                                        </div>
                                        <div class="row-span-1">
                                            <button
                                                @click.prevent="changePlaybackRate(0.5)"
                                                :class="[
                                                    playback_rate === 0.5 ? 'bg-theme-dominant' : 'bg-none' ,
                                                    'w-full h-full transition-colors duration-200 ease-in-out p-2 rounded-b-lg'
                                                ]"
                                            >
                                                0.5
                                            </button>
                                        </div>
                                </VBox>
                            </TransitionFade>
                        </div>
                        <button
                            @click.prevent="togglePlaybackSpeedOptions()"
                            class="w-full h-full"
                        >
                            <i
                                :class="[
                                    is_playback_speed_options_open ? '-rotate-90' : 'rotate-0',
                                    'fas fa-forward transition duration-200 ease-in-out'
                                ]"
                            ></i>
                        </button>
                    </div>
                    <!--playback volume-->
                    <div
                        ref="playback_volume_button"
                        class="row-start-5 row-span-1 col-start-3 col-span-1 h-full"
                    >
                        <div class="relative w-full h-0">
                            <TransitionFade>
                                <VBox
                                    v-show="is_playback_volume_open"
                                    v-click-outside="{
                                        related_data: 'is_playback_volume_open',
                                        exclude: ['playback_volume_button']
                                    }"
                                    class="
                                        w-full h-32 absolute text-center bottom-1 p-2 py-6
                                    "
                                >
                                    <VSliderYSmall
                                        ref="volume_slider"
                                        :propSliderValue="playback_volume"
                                        @hasNewSliderValue="changePlaybackVolume($event)"
                                        class="h-full"
                                    />
                                </VBox>
                            </TransitionFade>
                        </div>
                        <button
                            @click.prevent="togglePlaybackVolumeOptions()"
                            class="w-full h-full"
                        >
                            <i
                                :class="[
                                    (playback_volume === 0 ? 'fa-volume-xmark' : ''),
                                    (playback_volume <= 0.25 ? 'fa-volume-off' : ''),
                                    (playback_volume <= 0.5 ? 'fa-volume-low' : ''),
                                    (playback_volume <= 1 ? 'fa-volume-high' : ''),
                                    (is_playback_volume_open ? '-rotate-90' : 'rotate-0'),
                                    'fas transition duration-200 ease-in-out'
                                ]"
                            ></i>
                        </button>
                    </div>
                </VBox>
            </div>
        </div>
    </div>
</template>


<script setup>

    import VSliderYSmall from './VSliderYSmall.vue';
    import VSliderXMedium from './VSliderXMedium.vue';
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
                current_playback_time: '00:00',
                playback_duration: '00:00',
                is_playing: false,
                is_dragging: false,
                
                playback_rate: 1,  //accepts 0 to 2
                playback_volume: 0.5, //accepts 0 to 1
                is_repeat: false,

                is_playback_speed_options_open: false,
                is_playback_volume_open: false,

                is_ready_to_navigate: false,
                playback_states: ['empty', 'recording', 'has_file', 'loading', 'error'],
                current_playback_state: null,
                bucket_quantity: 30,
                file_volumes: [],
            };
        },
        components: {
            VSliderYSmall,
            VSliderXMedium,
            VBox,
            TransitionFade,
        },
        mounted(){

            //playback speed, accepts 0 to 2, default 1
            //also convert from localStorage's String back to Float
            if(window.localStorage.playback_rate === undefined){

                this.playback_rate = 1;

            }else{

                this.playback_rate = parseFloat(window.localStorage.playback_rate);
            }
            this.$refs.audio_playback.playbackRate = this.playback_rate;
            
            //playback speed, accepts 0 to 1, default 0.5
            //also convert from localStorage's String back to Float
            if(window.localStorage.playback_volume === undefined){

                this.playback_volume = 0.5;

            }else{

                this.playback_volume = parseFloat(window.localStorage.playback_volume);
            }
            this.$refs.audio_playback.volume = this.playback_volume;

            //set audio visualiser default
            //bar is 2/4, so 1/4 space on both sides
            for(let x=0; x < this.bucket_quantity; x++){

                this.$refs.volume_ripple[x].style.height = '50%';
            }
            
            //initialise with 'empty' state
            this.current_playback_state = this.playback_states[0];

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
            propFile: Object,
            propIsRecording: Boolean,
            propRecordingVolume: Number,    //0-1
            propTimeInterval: Number,  //based on VRecorder time_interval
        },
        watch: {
            async propFile(new_value){

                this.final_file = new_value;

                if(new_value === null){

                    return false;
                }

                const audio_context = new AudioContext();

                await new_value.arrayBuffer()
                    .then(buffer => audio_context.decodeAudioData(buffer))
                    .then(decoded_audio => decoded_audio.getChannelData(0)) //only 1 channel as expected
                    .then(audio_data => this.getVolumes(audio_data))
                    .then(() => {
                        //no need to fire 'has_file' here, <audio> @canplay will do that for us
                        this.attachRecordedAudioToPlayback();
                    })
                    .catch(error => {
                        alert("A bug has been created! It's not your fault. The developer has been notified.");
                        console.log(error);
                    });
            },
            propRecordingVolume(new_value){

                this.animeVolumeAnalyser(new_value);
            },
            propIsRecording(new_value){

                if(new_value === false){

                    return false;
                }

                //reset everything when recording a new instance
                this.current_playback_state = this.playback_states[1];
                this.final_file = null;
                this.final_file_duration = 0;
                this.current_playback_time = '00:00';
                this.playback_duration = '00:00';
                this.is_playing = false;
                this.is_ready_to_navigate = false;
            },
            current_playback_state(){

                this.animePlayback();
            },
        },
        methods: {
            resetVolumeAnalyser(){

                const volume_analyser_circles = [
                    this.$refs.volume_analyser_circle_0,
                    this.$refs.volume_analyser_circle_1,
                    this.$refs.volume_analyser_circle_2,
                ];

                anime({
                    targets: volume_analyser_circles,
                    easing: 'linear',
                    loop: false,
                    autoplay: true,
                    width: '0',
                    height: '0',
                    duration: this.propTimeInterval,
                });
            },
            animeVolumeAnalyser(new_value){

                const volume_analyser_circles = [
                    this.$refs.volume_analyser_circle_0,
                    this.$refs.volume_analyser_circle_1,
                    this.$refs.volume_analyser_circle_2,
                ];

                //circles have width and height of 20-30, 30-50, 50-80 %
                let base_target_percentage = 10;
                const percentage_increment = 30;
                
                anime.remove(volume_analyser_circles);

                for(let x=0; x < volume_analyser_circles.length; x++){

                    const extra_target_percentage = (x + 1) * percentage_increment;

                    const final_target_percentage = (new_value * extra_target_percentage) + base_target_percentage;

                    anime({
                        targets: volume_analyser_circles[x],
                        width: final_target_percentage.toString() + '%',
                        height: final_target_percentage.toString() + '%',
                        autoplay: true,
                        easing: 'linear',
                        loop: false,
                        duration: this.propTimeInterval,
                    });
                }
            },
            handlePlaybackDrag(new_value){

                //handle actual playback time
                // if(this.is_ready_to_navigate === false){

                //     return false;
                // }

                //expect new_value to be float 0 to 1
                const new_seconds = this.final_file_duration * new_value;

                //handle visuals
                this.$refs.playback_progress.style.width = (new_value * 100).toString() + '%';

                //handle <audio>
                this.$refs.audio_playback.currentTime = new_seconds;

                //handle timer
                this.updateCurrentPlaybackTime();
            },
            updateCurrentPlaybackTime(){

                //playback_progress
                // let new_progress = this.$refs.audio_playback.currentTime / this.final_file_duration;
                //we set one single anime() then play/pause it, instead of adjusting from here

                //timer
                this.current_playback_time = new Date(
                    this.$refs.audio_playback.currentTime * 1000
                ).toISOString().substring(14, 19);
            },
            changePlaybackRate(new_value){

                //note that on every new file loaded into <audio>, playbackRate is reset
                //attachRecordedAudioToPlayback() will handle this inconvenience
                this.$refs.audio_playback.playbackRate = new_value;
                this.playback_rate = new_value;
                window.localStorage.playback_rate = new_value;
            },
            changePlaybackVolume(new_value){
                
                this.$refs.audio_playback.volume = new_value;
                this.playback_volume = new_value;
                window.localStorage.playback_volume = new_value;
            },
            togglePlaybackSpeedOptions(){

                this.is_playback_speed_options_open = !this.is_playback_speed_options_open;
            },
            toggleRepeat(){

                this.is_repeat = !this.is_repeat;
            },
            togglePlaybackVolumeOptions(){

                this.is_playback_volume_open = !this.is_playback_volume_open;
            },
            togglePlaybackPlayPause(){

                const target = this.$refs.audio_playback;

                //note that when .ended is true, .paused is also true
                //seems not possible to handle .ended here, so we handle it at element
                if(target.paused === true){
                    
                    target.play();
                    this.is_playing = true;

                }else{

                    target.pause();
                    this.is_playing = false;
                }
            },
            animePlayback(){

                const volume_ripples = this.$refs.volume_ripple;

                //reset all elements
                //reset all translates to 0
                anime.remove(volume_ripples);

                switch(this.current_playback_state){

                    case this.playback_states[0]: {

                        //'empty', a.k.a. initial state

                        //initialise or reset all relevant elements
                        this.$refs.playback_main.style.height = '20rem';
                        this.$refs.playback_extras.style.display = 'none';
                        this.$refs.playback_extras.style.opacity = '0';
                        this.resetVolumeAnalyser();

                        //animate volume_ripples
                        anime({
                            targets: volume_ripples,
                            easing: 'linear',
                            loop: true,
                            autoplay: true,
                            translateY: ['0%', '-5%', '5%', '0%'],
                            delay: anime.stagger(100),
                        });
                        
                        break;
                    }
                    case this.playback_states[1]:

                        //'recording'

                        //fade playback_extras and hide, reset volume_ripples, expand playback_main
                        anime.timeline({
                            easing: 'linear',
                            loop: false,
                            autoplay: true,
                        }).add({
                            targets: this.$refs.playback_extras,
                            opacity: 0,
                            duration: 100,
                            complete: ()=>{this.$refs.playback_extras.style.display = 'none';}
                        }).add({
                            targets: volume_ripples,
                            translateY: ['0%'],
                            height: '0%',
                            duration: 100,
                        }).add({
                            targets: this.$refs.playback_main,
                            height: '20rem',
                            duration: 2000
                        });

                        break;

                    case this.playback_states[2]:

                        //'has_file'

                        //shrink playback_main, process volume_ripples, fade in playback_extras
                        anime.timeline({
                            easing: 'linear',
                            loop: false,
                            autoplay: true,
                        }).add({
                            targets: this.$refs.playback_main,
                            height: '15rem',
                            begin: this.resetVolumeAnalyser,
                            duration: 100,
                            complete: this.adjustVolumeRipples,
                        }).add({
                            targets: this.$refs.playback_extras,
                            begin: ()=>{this.$refs.playback_extras.style.display = 'block';},
                            opacity: 1,
                            duration: 100,
                        });

                        break;

                    case this.playback_states[3]:

                        //'loading'
                        anime({
                            targets: volume_ripples,
                            translateY: ['0%', '-10%', '10%', '0%'],
                            autoplay: true,
                            delay: anime.stagger(20),
                            easing: 'linear',
                            loop: true,
                        });
                        break;

                    case this.playback_states[4]:

                        //'error'
                        //reset height
                        anime({
                            targets: volume_ripples,
                            translateY: ['0%'],
                            height: '50%',
                            autoplay: true,
                            easing: 'linear',
                            loop: false,
                            duration: 200,
                        });
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

                //we don't calculate volume range because it is unnecessary
                //0.1-0.2 is not 55%-60% but 0%-100%
                //min and max range is also -1 to 1, so need extra 'if' statements
                //lastly, we expect -1 to 1, but at 0 audio, we get only -0.0001
            },
            adjustVolumeRipples(){

                //we calculate height relative to most quiet and loudest parts
                //samples are expected to be between -1 and 1, but we get -0.0001 when no audio


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

                    // if(this.file_volumes[x] < 0){
                        
                    //     current_height = (1 - (this.file_volumes[x] * -1)) * 50;

                    // }else{

                    //     current_height = 50 + (this.file_volumes[x] * 50);
                    // }

                    //expected volume range is -1 to 0, but our peaks at 0 audio is still -0.0001...
                    //so we recalibrate from lower and upper 50 to full 100
                    if(this.file_volumes[x] < 0){

                        //for aesthetics, if you prefer 0 to be visible, do this.file_volumes[x]<0.05 ... current_height=5
                        current_height = 0;

                    }else if(this.file_volumes[x] > 1){

                        current_height = 100;

                    }else{

                        current_height = this.file_volumes[x] * 100;
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

                //on every new file loaded into <audio>, playbackRate is reset
                this.$refs.audio_playback.playbackRate = this.playback_rate;
                return true;
            },
            getPlaybackDuration(){

                this.is_ready_to_navigate = false;

                //there's a bug that gives us 'Infinity'
                //this is how we fix it
                //https://stackoverflow.com/a/69512775
                if(this.$refs.audio_playback.duration == 'Infinity'){

                    const handler = ()=>{

                        this.$refs.audio_playback.currentTime = 0;
                        this.$refs.audio_playback.removeEventListener('timeupdate', handler);
                        this.final_file_duration = this.$refs.audio_playback.duration;

                        //mm:ss
                        //only for duration display we will use floor
                        this.playback_duration = 
                            new Date(Math.floor(this.final_file_duration) * 1000).toISOString().substring(14, 19);
                        this.is_ready_to_navigate = true;
                    };

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