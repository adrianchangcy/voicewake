<template>
    <div>
        <div class="h-fit text-xl break-words text-theme-black">
            <slot name="title"></slot>
        </div>
        <div class="h-fit text-base font-light text-theme-black/80">
            <slot name="titleDescription"></slot>
        </div>
    </div>
</template>