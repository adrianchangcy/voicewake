<template>
    <div class="">
        <div
            :class="[
                propHasAutoSpaceLogo ? 'px-2 pb-2' : '',
                'flex flex-col items-center text-center text-xl'
            ]"
        >
            <slot name="logo"></slot>
        </div>
        <div
            :class="[
                propHasBorder === true? 'border border-theme-gray-2 dark:border-dark-theme-gray-2 divide-y divide-theme-gray-2 dark:divide-dark-theme-gray-2' : '',
                'w-full h-fit text-center flex flex-col rounded-lg'
            ]"
        >
            <div
                :class="[
                    propHasAutoSpaceTitle ? 'px-4 py-2' : '',
                    'flex flex-col items-center text-xl font-medium'
                ]"
            >
                <div class="w-full h-fit text-center">
                    <slot name="title"></slot>
                </div>
            </div>
            <div
                :class="[
                    propHasAutoSpaceContent ? 'p-4' : '',
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
            propHasAutoSpaceLogo: {
                type: Boolean,
                default: true
            },
            propHasAutoSpaceTitle: {
                type: Boolean,
                default: true
            },
            propHasAutoSpaceContent: {
                type: Boolean,
                default: true
            },
        },
    };
</script>