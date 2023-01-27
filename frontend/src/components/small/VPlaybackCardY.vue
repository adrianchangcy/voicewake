<template>

    <div class="w-full text-center text-theme-black">

        <div class="h-fit text-base">
            <i class="fas fa-user block"></i>
        </div>

        <!--username-->
        <div class="h-fit text-base">
            <span>{{propUsername}}</span>
        </div>

        <!--label, ripples, total duration-->
        <button class="w-full h-fit rounded-lg border-2 border-theme-light-gray p-2" type="button">
    
            <!--label-->
            <div class="h-12 relative text-3xl">
                <span class="w-fit h-fit absolute left-0 right-0 top-0 bottom-0.5 m-auto">{{event_tone}}</span>
            </div>
    
            <!--ripples-->
            <div class="h-20 my-2 relative">
                <div
                    ref="volume_ripples_container"
                    class="w-full h-full absolute flex flex-row justify-evenly"
                >
                    <div
                        v-for="volume_ripple in buckets.length" :key="volume_ripple"
                        ref="volume_ripple"
                        class="h-full scale-y-0 origin-center"
                    >
                        <div class="left-0 right-0 mx-auto w-0.5 h-full bg-theme-black">
                        </div>
                    </div>
                </div>

                <!-- <i class="fas fa-play absolute left-0 right-0 top-0 bottom-0 m-auto w-fit h-fit text-4xl text-theme-black"></i> -->
            </div>
    
            <!--total duration-->
            <div class="h-8 relative text-base">
                <span class="h-fit absolute left-0 right-0 top-0 m-auto">{{pretty_file_duration}}</span>
            </div>
        </button>

        <!--when uploaded-->
        <div class="h-fit text-base font-light">
            <span>{{pretty_upload_datetime}}</span>
        </div>
        
    </div>
</template>


<script setup>

</script>


<script>
export default {
    data(){
        return {

            event_tone: '😭',
            buckets: [0.4, 0.2, 0.6, 0.7, 0.5, 0.2, 0.1, 0.7, 1, 1, 0.4, 0.2, 0.6, 0.7, 0.5, 0.2, 0.1, 0.7, 0.9, 0.9],
            pretty_file_duration: '01:20',
            pretty_upload_datetime: '40 minutes ago',

        };
    },
    props: {
        propUsername: {
            type: String,
            default: '',
        },
    },
    mounted(){

        for(let x = 0; x < this.buckets.length; x++){

            this.$refs.volume_ripple[x].style.transform = 'scaleY('+this.buckets[x]+')';
        }
    },

}
</script>