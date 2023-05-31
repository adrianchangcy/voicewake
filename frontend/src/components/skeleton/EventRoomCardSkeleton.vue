<template>
    <div>
        <!--title and datetime-->
        <div class="flex flex-col gap-1 py-8">
            <div class="w-[75%] h-6 skeleton"></div>
            <div class="w-[25%] h-4 skeleton"></div>
        </div>
        <div class="flex flex-col gap-6">
            <!--events-->
            <div v-for="x in propEventQuantity" :key="x">
                <div class="flex flex-col gap-2">
                    <!--user-->
                    <div class="h-5 flex flex-row gap-2">
                        <div class="w-4 h-full skeleton"></div>
                        <div class="w-[25%] h-full skeleton"></div>
                    </div>
                    <!--card-->
                    <div class="w-full h-20 skeleton"></div>
                    <!--like/dislike-->
                    <div class="w-full h-10 grid grid-cols-8">
                        <div class="col-span-6 lg:col-span-4 h-full skeleton"></div>
                    </div>
                </div>
                
            </div>
        </div>
        <!--reply button-->
        <div
            v-show="propCanReply === true"
            class="h-28 mt-8 skeleton"
        ></div>
    </div>
</template>


<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        props: {
            propEventQuantity: {
                type: Number,
                default: 2
            },
            propCanReply: {
                type: Boolean,
                default: false
            }
        }
    });
</script>