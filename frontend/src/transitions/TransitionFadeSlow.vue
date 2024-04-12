<template>
    <!--for v-if and v-else-if, particularly with more than 1 single variable, mode="out-in" seems unreliable-->
    <!--next element consistently appears early before current element disappears-->
    <!--solution is to create custom <Transition> and add delay for enter-active, but only for these cases, not for generic-->
    <Transition
        name="transition-fade-slow"
        mode="out-in"
        enter-from-class="opacity-0"
        enter-active-class="transition-opacity duration-500 ease-in-out"
        enter-to-class="opacity-100"
        leave-from-class="opacity-100"
        leave-active-class="transition-opacity duration-500 ease-in-out"
        leave-to-class="opacity-0"
    >
        <slot></slot>
    </Transition>
</template>