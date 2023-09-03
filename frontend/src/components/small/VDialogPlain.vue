<template>
    <div>
        <div class="flex flex-col items-center text-center text-xl px-2 pb-2 text-theme-black">
            <slot name="logo"></slot>
        </div>
        <div
            :class="[
                propHasBorder === true? 'border border-theme-light-gray divide-y divide-theme-light-gray' : '',
                'w-fit h-fit mx-auto flex flex-col text-theme-black rounded-lg'
            ]"
        >
            <div class="flex flex-col items-center text-xl font-medium px-4 py-2">
                <div class="w-full h-fit text-center">
                    <slot name="title"></slot>
                </div>
            </div>
            <div class="text-base p-4 text-center">
                <slot name="content"></slot>
            </div>
        </div>
    </div>
</template>


<script lang="ts">

    export default{
        props: {
            propHasBorder: {
                type: Boolean,
                default: true
            },
        },
    };
</script>