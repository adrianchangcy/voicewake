<template>

    <div class="flex flex-col gap-12 text-theme-black">

        <div v-for="reply_event in 3" :key="reply_event">

            <div
                class="w-full block border-2 border-theme-light-gray rounded-lg px-4 py-6 transition-colors duration-200 ease-in-out"
                @click.stop="redirectToThisPost(reply_event, $event)"
            >
                <!--title-->
                <div class="h-fit pb-4">
                    <!--title from user 1-->
                    <p class="text-xl">
                        I have something to tell you!!
                    </p>
                    <!--last updated-->
                    <p class="when-created      text-base font-light">
                        10 minutes ago
                    </p>
                </div>
                
                <div class="w-full h-fit flex flex-col gap-8">

                    <!--user 1-->
                    <div ref="user_1_card">
                        <VEventCard
                            propUsername="carlj101"
                            @isSelected="handleSelectedCard(reply_event)"
                            :propIsSelected="reply_event === selected_card"
                        />
                    </div>

                    <!--user 2-->
                    <div ref="user_2_card">
                        <VEventReplyButton
                            :propIsSelected="reply_event === selected_card"
                            @click.stop="redirectToThisPost(reply_event, $event)"
                            class="w-full"
                        />
                    </div>
                </div>
            </div>
        </div>
    </div>


</template>


<script setup lang="ts">

    import VEventCard from '/src/components/small/VEventCard.vue';
    import VEventReplyButton from '/src/components/small/VEventReplyButton.vue';
</script>


<script lang="ts">

    import { defineComponent } from 'vue';
    
    export default defineComponent({
        data() {
            return {
                selected_card: null as number | null,
            };
        },
        methods: {
            handleSelectedCard(card_id:number): void {
            
                if(this.selected_card === card_id){
                
                    return;
                }
            
                this.selected_card = card_id;
            },
            redirectToThisPost(key:number, event:MouseEvent|TouchEvent) : void {
                
                //readjust to array
                key = key = 1;
            
                if(((this.$refs.user_1_card as HTMLElement[])[key]).contains(event.target as Node)){
                
                    return;
                
                }else if(((this.$refs.user_2_card as HTMLElement[])[key]).contains(event.target as Node)){
                
                    return;
                
                }else{
                
                    console.log('wtf');
                }
            }
        },
    });
</script>