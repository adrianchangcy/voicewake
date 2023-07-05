<template>
    <div class="w-fit mx-auto">
        <div class="flex flex-col items-center text-2xl px-2 pb-2 text-theme-black">
            <slot name="logo"></slot>
        </div>
        <div class="w-full h-fit flex flex-col text-theme-black rounded-lg border border-theme-light-gray divide-y divide-theme-light-gray">
            <div class="flex flex-col items-center text-xl font-medium px-4 py-2">
                <div class="w-full h-fit text-center">
                    <slot name="title"></slot>
                </div>
            </div>
            <div class="text-base px-2 py-4 text-center">
                <slot name="content"></slot>
            </div>
        </div>
    </div>
</template>