<template>

    <div class="flex flex-col gap-12 text-theme-black">

        <div v-for="reply_event in 3" :key="reply_event">

            <div class="border border-theme-light-gray rounded-lg px-4 py-8">

                <!--title from user 1-->
                <div class="w-full h-fit text-xl pb-4">
                    <span class="text-center">
                        I have something to tell you!!
                    </span>
                </div>

                <div class="w-full h-fit flex flex-col gap-2">

                    <!--user 1-->
                    <VPlaybackCardX
                        propUsername="carlj101"
                    />

                    <!--option to reply-->
                    <VReplyButtonX/>
                </div>
            </div>

        </div>
    </div>


</template>


<script setup>

    import VPlaybackCardX from '/src/components/small/VPlaybackCardX.vue';
    import VReplyButtonX from '/src/components/small/VReplyButtonX.vue';
</script>


<script>
export default {
    data(){
        return {



        };
    },
    components: {
        VPlaybackCardX,
        VReplyButtonX,
    },

}
</script>