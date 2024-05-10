<template>
    <VNavBar
        :propUsername="username"
    />

    <!--extra popups can belong here so we can ensure that only one shows at a time-->
    <div class="w-full h-0 relative">
    </div>

    <!--toasts-->
    <!--if pop-ups clash with toasts, do v-if here-->
    <div
        class="w-0 h-0"
    >
        <VNotiwind/>
        <VAudioClipProcessings/>
    </div>
</template>


<script setup lang="ts">
    import VNotiwind from '../components/medium/VNotiwind.vue';
    import VAudioClipProcessings from '@/components/medium/VAudioClipProcessings.vue';
    import VNavBar from '../components/main/VNavBar.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    import { getDataFromTemplateJSONScript } from '@/helper_functions';
    import { usePageRefreshTriggerStore } from '@/stores/PageRefreshTriggerStore';
    import { usePopUpManagerStore } from '@/stores/PopUpManagerStore';
    import { useRedrawCanvasesStore } from '@/stores/RedrawCanvasesStore';
    import { notify } from '@/wrappers/notify_wrapper';
    import { axiosCSRFSetup } from '@/helper_functions';

    export default defineComponent({
        name: 'BaseApp',
        data(){
            return {
                page_refresh_trigger_store: usePageRefreshTriggerStore(),
                pop_up_manager_store: usePopUpManagerStore(),
                redraw_canvases_store: useRedrawCanvasesStore(),

                username: "",
            };
        },
        computed: {
        },
        methods: {
            checkHasCookiesConsent() : void {

                //currently not used
                //only need consent if collecting user data

                if(this.pop_up_manager_store.isLoggedIn === false || localStorage.getItem('user_consents_to_cookies') !== null){

                    return;
                }

                notify({
                    type: 'generic',
                    title: 'Cookies Consent',
                    text: 'We use cookies so you can stay logged in.',
                    icon: {'font_awesome': 'fas fa-cookie-bite'},
                    actions: [{
                        type: 'button',
                        style: 'primary',
                        text: 'Accept',
                        callback: this.setCookiesConsent,
                    }]
                }, -1);
            },
            setCookiesConsent() : void {

                localStorage.setItem('user_consents_to_cookies', JSON.stringify(true));
            },
            closeAllPopUpsOnEsc(event:KeyboardEvent) : void {

                if(event.key === 'Escape'){

                    this.pop_up_manager_store.closeAllPopUps();
                }
            },
        },
        beforeMount(){

            axiosCSRFSetup();

            //is logged in
            this.pop_up_manager_store.setIsLoggedIn(
                getDataFromTemplateJSONScript("data-user-is-authenticated") as boolean
            );

            //username
            const username = getDataFromTemplateJSONScript("data-user-username") as string|null;

            if(username !== null){

                this.username = username;
            }

            //refresh all tabs when necessary
            //provided that every tab has BaseApp.vue
            this.page_refresh_trigger_store.$subscribe(()=>{

                this.page_refresh_trigger_store.resetRefreshContext();

                window.location.replace(window.location.href);
            });

            //allow use of ESC key to close popups
            window.addEventListener('keydown', this.closeAllPopUpsOnEsc);
            window.addEventListener('resize', this.redraw_canvases_store.redrawAllAudioVolumePeakCanvases);

        },
        beforeUnmount(){

            window.removeEventListener('keydown', this.closeAllPopUpsOnEsc);
            window.removeEventListener('resize', this.redraw_canvases_store.redrawAllAudioVolumePeakCanvases);
        }
    });
</script>


