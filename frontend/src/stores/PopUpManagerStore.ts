import { defineStore } from 'pinia';

type IsOpenTypes = {
    [key:string]: boolean
}


//helps us manage pop-ups
//currently using redundant way of ensuring other pop-ups are closed when one opens
//still manageable because we have limited pop-ups
export const usePopUpManagerStore = defineStore('pop_up_manager', {
    state: ()=>({
        is_logged_in: false,

        is_open: {
            is_login_required_prompt_open: false,
            is_nav_menu_open: true,

            //two identical components, but separate state
            //allows for <keep-alive> and better UX
            is_user_log_in_open: false,
            is_user_sign_up_open: false,
        } as IsOpenTypes,

        login_required_prompt_text: "",

    }),    
    getters: {
        isLoggedIn: (state)=>{

            return state.is_logged_in;
        },
        hasPopUpOpen: (state)=>{

            return (
                state.is_open.is_login_required_prompt_open === true ||
                state.is_open.is_nav_menu_open === true ||
                state.is_open.is_user_log_in_open === true ||
                state.is_open.is_user_sign_up_open === true
            );
        },
        isUserLogInOpen: (state)=>{

            return state.is_open.is_user_log_in_open;
        },
        isUserSignUpOpen: (state)=>{

            return state.is_open.is_user_sign_up_open;
        },
        isLoginRequiredPromptOpen: (state)=>{

            return state.is_open.is_login_required_prompt_open;
        },
        isNavMenuOpen: (state)=>{

            return state.is_open.is_nav_menu_open;
        },
        getLoginRequiredPromptText: (state)=>{

            return state.login_required_prompt_text;
        },
    },
    actions: {
        async setIsLoggedIn(new_value:boolean) : Promise<void> {
            
            this.is_logged_in = new_value;
        },
        async forceCloseAllPopUps(event:KeyboardEvent|null=null) : Promise<void> {

            if(event !== null && event.key !== 'Escape'){

                return;
            }

            for(const key in this.is_open){

                this.is_open[key] = false;
            }
        },
        forceCloseOtherPopUps(current_key:string) : void {

            for(const key in this.is_open){

                if(key !== current_key){

                    this.is_open[key] = false;
                }
            }
        },
        async toggleIsUserLogInOpen(is_open:boolean|null=null) : Promise<void> {

            const new_store_value = is_open === null ? !this.is_open.is_user_log_in_open : is_open;

            if(new_store_value === true){

                this.forceCloseOtherPopUps('is_user_log_in_open');
            }

            this.is_open.is_user_log_in_open = new_store_value;
        },
        async toggleIsUserSignUpOpen(is_open:boolean|null=null) : Promise<void> {

            const new_store_value = is_open === null ? !this.is_open.is_user_sign_up_open : is_open;

            if(new_store_value === true){

                this.forceCloseOtherPopUps('is_user_sign_up_open');
            }

            this.is_open.is_user_sign_up_open = new_store_value;
        },
        async toggleIsLoginRequiredPromptOpen(
            forced_state:boolean|null=null,
            prompt_text:string="",
        ) : Promise<void> {

            const new_store_value = forced_state === null ? !this.is_open.is_login_required_prompt_open : forced_state;

            if(new_store_value === true){

                this.forceCloseOtherPopUps('is_login_required_prompt_open');
            }

            this.is_open.is_login_required_prompt_open = new_store_value;

            if(prompt_text === ""){

                this.login_required_prompt_text = "Log in to perform that action.";

            }else{

                this.login_required_prompt_text = prompt_text;
            }
        },
        async toggleIsNavMenuOpen(forced_state:boolean|null=null) : Promise<void> {

            const new_store_value = forced_state === null ? !this.is_open.is_nav_menu_open : forced_state;

            //this is bad at scaling
            if(new_store_value === true){

                this.forceCloseOtherPopUps('is_nav_menu_open');
            }

            this.is_open.is_nav_menu_open = new_store_value;
        },
    },
});