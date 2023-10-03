<template>
    <div>


        <TransitionFade>
            <VDialogPlain
                v-show="canShowEmptyMessage || canShowEndOfPageMessage"
                :prop-has-border="false"
                :prop-has-auto-spacing="false"
                class="w-full py-8"
            >
                <template #title>
                    <span v-show="canShowEmptyMessage">No users blocked.</span>
                    <span v-show="canShowEndOfPageMessage">You've reached the end of this page.</span>
                </template>
            </VDialogPlain>
        </TransitionFade>

        <div id="load-more-user-blocks-observer-target"></div>
    </div>
</template>


<script setup lang="ts">
    import TransitionFade from '@/transitions/TransitionFade.vue';
    import VDialogPlain from '@/components/small/VDialogPlain.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { notify } from 'notiwind';
    const axios = require('axios');

    interface UserBlocksTypes {
        user: {
            id: number,
            username: string
        },
        is_blocked: boolean
    }

    export default defineComponent({
        name: 'ListUserBlocksApp',
        data(){
            return {
                user_blocks: [] as UserBlocksTypes[],

                is_fetching: false,
                can_observer_fetch: false,
                has_no_user_blocks_left_to_fetch: false,
                current_page: 1,
            };
        },
        computed: {
            canShowEmptyMessage() : boolean {

                return (
                    this.is_fetching === false &&
                    this.user_blocks.length === 0 &&
                    this.has_no_user_blocks_left_to_fetch === true
                );
            },
            canShowEndOfPageMessage() : boolean {

                return (
                    this.is_fetching === false &&
                    this.user_blocks.length > 0 &&
                    this.has_no_user_blocks_left_to_fetch === true
                );
            },
        },
        methods: {
            axiosSetup() : boolean {

                //your template must have {% csrf_token %}
                let token = document.getElementsByName("csrfmiddlewaretoken")[0];

                if(token === undefined){

                    console.log('CSRF not found.');
                    return false;
                }

                axios.defaults.headers.common['X-CSRFToken'] = (token as HTMLFormElement).value;
                axios.defaults.headers.post['Content-Type'] = 'multipart/form-data';
                return true;
            },
            async doUserBlocksAction(user_block_index:number) : Promise<void> {

                //your template must have {% csrf_token %}
                let token = document.getElementsByName("csrfmiddlewaretoken")[0];

                if(token === undefined){

                    console.log('CSRF not found.');
                    return;
                }

                const url = window.location.origin + '/api/users/blocks';

                let data = new FormData();
                data.append('user_id', JSON.stringify(this.user_blocks[user_block_index].user.id));
                data.append('to_block', JSON.stringify(!this.user_blocks[user_block_index].is_blocked));

                const config = {
                    headers: {
                        common: {
                            'X-CSRFToken': (token as HTMLFormElement).value
                        },
                        post: {
                            'Content-Type': 'multipart/form-data'
                        }
                    }
                };

                await axios.post(url, data, config).then((result:any)=>{
                    console.log(result);
                })

            },
            async getUserBlocks() : Promise<void> {

                this.is_fetching = true;
                this.can_observer_fetch = false;
                this.has_no_user_blocks_left_to_fetch = false;

                const url = window.location.origin + '/api/users/blocks/list/' + this.current_page.toString();

                await axios.get(url)
                .then((result:any) => {

                    console.log(result.data['data'].length);

                    result.data['data'].forEach((user_block:UserBlocksTypes)=>{

                        this.user_blocks.push(user_block);
                    });

                    if(result.data['data'].length > 0){

                        this.current_page += 1;

                    }else{

                        this.has_no_user_blocks_left_to_fetch = true;

                    }

                    this.can_observer_fetch = true;

                }).catch(() => {

                    notify({
                        title: 'Error',
                        text: 'Unable to retrieve your banned recordings.',
                        type: 'error'
                    });

                }).finally(() => {

                    this.is_fetching = false;
                });
            },
            setUpObserver() : void {

                //set up observer for infinite scroll
                const observer_target = document.querySelector('#load-more-user-banned-events-observer-target');

                const observer = new IntersectionObserver(()=>{

                    if(
                        this.can_observer_fetch === false ||
                        this.has_no_user_blocks_left_to_fetch === true
                    ){

                        return;
                    }

                    this.getUserBlocks();
                }, {
                    threshold: 1,
                });

                if(observer_target !== null){

                    observer.observe(observer_target);
                }
            },
        },
        beforeMount(){

            //set up Axios appropriately
            this.axiosSetup();

            this.getUserBlocks();
        },
        mounted(){

            this.setUpObserver();
        }
    });
</script>