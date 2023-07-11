<template>
    <!--parent div should look like:-->
    <!--<div class="overflow-hidden relative">-->
    <TransitionGroup
        name="transition-group-fade"
        enter-from-class="opacity-0"
        enter-active-class="transition-opacity delay-500 duration-500 ease-in-out"
        enter-to-class="opacity-100"
        leave-from-class="opacity-100"
        leave-active-class="transition-opacity duration-500 ease-in-out absolute"
        leave-to-class="opacity-0"
    >
        <!--child should look like:-->
        <!--<div class="w-full p-2">-->
        <!--p-2 is needed because overflow-hidden has inward clipping for some reason-->
        <slot></slot>
    </TransitionGroup>
</template>