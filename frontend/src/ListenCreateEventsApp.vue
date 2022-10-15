<template>
    <ListenCreateEvents>
        <template v-slot:emojiPicker>
            <EmojiPicker/>
        </template>
    </ListenCreateEvents>
</template>


<script>
    import ListenCreateEvents from './components/ListenCreateEvents.vue';
    import EmojiPicker from './components/EmojiPicker.vue';

    export default{
        name: 'ListenCreateEventsApp',
        components: {
            ListenCreateEvents,
            EmojiPicker,
        }
    };
</script>


