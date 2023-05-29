<template>
    <div
        class="h-fit py-6"
    >
        <div class="h-fit text-4xl font-light text-theme-black">
            <slot name="title"></slot>
        </div>
        <div class="h-fit text-2xl font-light text-theme-black/80 pt-2">
            <slot name="titleDescription"></slot>
        </div>
    </div>
</template>