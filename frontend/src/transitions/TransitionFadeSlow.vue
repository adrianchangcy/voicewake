<template>
    <!--your v-if and v-else-if or v-else must be straightforward-->
    <!--at GetEventsApp, v-if="isReplying" and v-else-if="!isReplying && dialog_context !== ''" made mode out-in fail-->
    <!--might have been due to dialog_context race condition being at .finally(), while isReplying was updated at .then()-->
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