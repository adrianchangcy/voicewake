<template>
    <div class="w-full h-fit flex flex-col text-theme-black rounded-lg border border-theme-light-gray divide-y divide-theme-light-gray">
        <div class="flex flex-row items-center gap-2 text-lg font-medium p-2">
            <slot name="title"></slot>
        </div>
        <div class="text-base px-2 py-4">
            <slot name="content"></slot>
        </div>
    </div>
</template>