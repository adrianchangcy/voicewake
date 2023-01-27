<template>

    <div class="md:w-2/4 lg:w-3/6 xl:w-2/6 mx-auto h-fit">

        <div class="w-[90%] mx-auto">
            <VSectionTitle>Reply</VSectionTitle>

            <VPlaybackPending class=""/>
        </div>

        <div class="sticky w-full h-fit bottom-0 z-40">
            <VPlayback
                :propIsSticky="true"
            />
        </div>
    </div>
</template>


<script setup>

    import VPlayback from '/src/components/medium/VPlayback.vue';
    import VPlaybackPending from '/src/components/medium/VPlaybackPending.vue';
    import VSectionTitle from '/src/components/small/VSectionTitle.vue';
</script>

<script>

    export default {
        data(){
            return {


            };
        },
        components:{
            VPlaybackPending,
        },
    }
</script>