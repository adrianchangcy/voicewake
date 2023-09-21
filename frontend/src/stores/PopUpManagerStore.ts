import { defineStore } from 'pinia';

type IsOpenType = {
    [key:string]: boolean
}


//helps us manage pop-ups
//currently using redundant way of ensuring other pop-ups are closed when one opens
//still manageable because we have limited pop-ups
export const usePopUpManagerStore = defineStore('pop_up_manager', {
    state: ()=>({
        is_logged_in: false,
        requested_section: "log-in-section" as "log-in-section"|"sign-up-section",

        is_open: {
            is_login_required_prompt_open: false,
            is_nav_menu_open: false,
            is_user_log_in_sign_up_open: false,
        } as IsOpenType,

    }),    
    getters: {
        getIsLoggedIn: (state)=>{

            return state.is_logged_in;
        },
        getHasPopUpOpen: (state)=>{

            return (
                state.is_open.is_login_required_prompt_open === true ||
                state.is_open.is_nav_menu_open === true ||
                state.is_open.is_user_log_in_sign_up_open === true
            );
        },
        getIsUserLogInSignUpOpen: (state)=>{

            return state.is_open.is_user_log_in_sign_up_open;
        },
        getIsLoginRequiredPromptOpen: (state)=>{

            return state.is_open.is_login_required_prompt_open;
        },
        getIsNavMenuOpen: (state)=>{

            return state.is_open.is_nav_menu_open;
        },
        getRequestedSection: (state)=>{
            
            return state.requested_section;
        },
    },
    actions: {
        setIsLoggedIn(new_value:boolean) : void {
            
            this.is_logged_in = new_value;
        },
        forceCloseOtherPopUps(current_key:string) : void {

            for(const key in this.is_open){

                if(key !== current_key){

                    this.is_open[key] = false;
                }
            }
        },
        toggleIsUserLogInSignUpOpen(new_value:boolean|null=null, section:"log-in-section"|"sign-up-section"|null=null) : void {

            const new_store_value = new_value === null ? !this.is_open.is_user_log_in_sign_up_open : new_value;

            if(new_store_value === true){

                this.forceCloseOtherPopUps('is_user_log_in_sign_up_open');
            }

            this.is_open.is_user_log_in_sign_up_open = new_store_value;

            if(section !== null){

                this.requested_section = section;
            }
        },
        toggleIsLoginRequiredPromptOpen(new_value:boolean|null=null) : void {

            const new_store_value = new_value === null ? !this.is_open.is_login_required_prompt_open : new_value;

            if(new_store_value === true){

                this.forceCloseOtherPopUps('is_login_required_prompt_open');
            }

            this.is_open.is_login_required_prompt_open = new_store_value;
        },
        toggleIsNavMenuOpen(new_value:boolean|null=null) : void {

            const new_store_value = new_value === null ? !this.is_open.is_nav_menu_open : new_value;

            //this is bad at scaling
            if(new_store_value === true){

                this.forceCloseOtherPopUps('is_nav_menu_open');
            }

            this.is_open.is_nav_menu_open = new_store_value;
        },
    },
    persist: false,
    share: {
        //array of fields that the plugin will ignore
        omit: [],
        //override global config for this store
        enable: false,
        initialize: false,
    },
});