<template>
    <!--putting TransitionFade at VUserLogInSignUp v-if v-else seems to break things-->
    <!--i.e. renders v-if and v-else once then permanently disappearing-->

    <Transition
        name="transition-fade"
        mode="out-in"
        enter-from-class="opacity-0"
        enter-active-class="transition-opacity"
        enter-to-class="opacity-100"
        leave-from-class="opacity-100"
        leave-active-class="transition-opacity"
        leave-to-class="opacity-0"
    >
        <slot></slot>
    </Transition>
</template>