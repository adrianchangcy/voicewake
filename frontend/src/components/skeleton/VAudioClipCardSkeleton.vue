<template>
    <div class="flex flex-col">
        <!--user-->
        <div class="h-10 relative">
            <div class="absolute w-full left-0 bottom-2 h-5 flex flex-row gap-2">
                <div class="w-4 h-full rounded-full skeleton"></div>
                <div class="w-[25%] h-full rounded-lg skeleton"></div>
            </div>
        </div>
        <div class="flex flex-col gap-2">
            <!--card-->
            <div class="w-full h-20 rounded-lg skeleton"></div>
            <!--VAudioClipTools-->
            <div class="w-full h-10 grid grid-cols-6 gap-1">
                <div class="col-span-4 h-full rounded-full skeleton"></div>
                <div class="col-span-1 h-full rounded-full skeleton"></div>
                <div class="col-span-1 h-full rounded-full skeleton"></div>
            </div>
        </div>
    </div>
</template>