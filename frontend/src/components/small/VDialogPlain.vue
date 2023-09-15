<template>
    <div class="text-theme-black">
        <div
            :class="[
                propHasAutoSpacing ? 'px-2 pb-2' : '',
                'flex flex-col items-center text-center text-xl'
            ]"
        >
            <slot name="logo"></slot>
        </div>
        <div
            :class="[
                propHasBorder === true? 'border border-theme-light-gray divide-y divide-theme-light-gray' : '',
                'w-full h-fit text-center flex flex-col rounded-lg'
            ]"
        >
            <div
                :class="[
                    propHasAutoSpacing ? 'px-4 py-2' : '',
                    'flex flex-col items-center text-xl font-medium'
                ]"
            >
                <div class="w-full h-fit text-center">
                    <slot name="title"></slot>
                </div>
            </div>
            <div
                :class="[
                    propHasAutoSpacing ? 'p-4' : '',
                    'text-base text-center'
                ]"
            >
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
            propHasAutoSpacing: {
                type: Boolean,
                default: true
            },
        },
    };
</script>