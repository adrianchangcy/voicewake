<template>
    <!--parent div should look like:-->
    <!--<div class="relative">-->
    <TransitionGroup
        name="transition-group-fade-slow"
        enter-from-class="opacity-0"
        enter-active-class="transition-opacity delay-500 duration-500 ease-in-out"
        enter-to-class="opacity-100"
        leave-from-class="opacity-100"
        leave-active-class="transition-opacity duration-500 ease-in-out absolute"
        leave-to-class="opacity-0"
    >
        <slot></slot>
    </TransitionGroup>
</template>