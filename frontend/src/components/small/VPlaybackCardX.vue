<template>

    <div class="text-theme-black">

        <!--username-->
        <div class="h-fit text-base pl-2">
            <span><i class="fas fa-user"></i> {{propUsername}}</span>
        </div>
    
        <!--label, ripples, total duration-->
        <VActionButtonMedium class="w-full grid grid-cols-7 gap-2">
    
            <!--label-->
            <div class="col-span-2 col-start-1 h-full relative text-3xl">
                <span class="w-fit h-fit absolute left-0.5 right-0 top-0 bottom-0.5 m-auto">{{event_tone}}</span>
            </div>
    
            <!--ripples-->
            <div class="col-span-3 col-start-3 h-full relative">
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
            </div>
    
            <!--total duration-->
            <div class="col-span-2 col-start-6 h-full relative text-base">
                <span class="w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto">{{pretty_file_duration}}</span>
            </div>
        </VActionButtonMedium>
    
        <!--when uploaded-->
        <div class="h-fit pr-2 text-right text-base font-extralight">
            <span>{{pretty_upload_datetime}}</span>
        </div>

    </div>
</template>


<script setup>

    import VActionButtonMedium from '/src/components/small/VActionButtonMedium.vue';
</script>


<script>
export default {
    data(){
        return {

            username: 'carlj101',
            event_tone: '😭',
            buckets: [0.4, 0.2, 0.6, 0.7, 0.5, 0.2, 0.1, 0.7, 1, 1, 0.4, 0.2, 0.6, 0.7, 0.5, 0.2, 0.1, 0.7, 0.9, 0.9],
            pretty_file_duration: '01:20',
            pretty_upload_datetime: '40 minutes ago',

        };
    },
    components: {
        VActionButtonMedium,
    },
    mounted(){

        for(let x = 0; x < this.buckets.length; x++){

            this.$refs.volume_ripple[x].style.transform = 'scaleY('+this.buckets[x]+')';
        }
    },
    props: {
        propUsername: {
            type: String,
            default: '',
        },
        propIsReply: {
            type: Boolean,
            default: false,
        },
    },

}
</script>