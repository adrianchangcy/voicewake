<template>
    <!--apparently only suitable for v-for list-->
    <TransitionGroup
        name="transition-group-fade"
        enter-from-class="opacity-0"
        enter-active-class="transition-opacity duration-200 ease-in-out"
        enter-to-class="opacity-100"
        leave-from-class="opacity-100"
        leave-active-class="transition-opacity duration-200 ease-in-out"
        leave-to-class="opacity-0"
    >
        <slot></slot>
    </TransitionGroup>
</template>