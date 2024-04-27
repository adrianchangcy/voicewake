<template>
    <div class="relative w-full h-full">
        <TransitionGroup
            name="transition-group-fade"
            enter-from-class="opacity-0"
            enter-active-class="absolute transition-opacity delay-150"
            enter-to-class="opacity-100"
            leave-from-class="opacity-100"
            leave-active-class="transition-opacity"
            leave-to-class="opacity-0"
        >
            <slot></slot>
        </TransitionGroup>
    </div>
</template>