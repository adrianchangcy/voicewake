<template>
    <div class="relative w-full h-full">
        <TransitionGroup
            name="transition-group-fade-slow"
            enter-from-class="opacity-0"
            enter-active-class="absolute transition-opacity delay-500 duration-500 ease-in-out"
            enter-to-class="opacity-100"
            leave-from-class="opacity-100"
            leave-active-class="transition-opacity duration-500 ease-in-out"
            leave-to-class="opacity-0"
        >
            <slot></slot>
        </TransitionGroup>
    </div>
</template>