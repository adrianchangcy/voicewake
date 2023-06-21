<template>
    <Transition
        name="transition-fade"
        mode="out-in"
        enter-from-class="transition-opacity opacity-0"
        enter-active-class="transition-opacity duration-500 ease-in-out"
        enter-to-class="transition-opacity opacity-100"
        leave-from-class="transition-opacity opacity-100"
        leave-active-class="transition-opacity duration-500 ease-in-out"
        leave-to-class="transition-opacity opacity-0"
    >
        <slot></slot>
    </Transition>
</template>