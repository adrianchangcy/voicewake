<template>
    <div class="pt-8 pb-8 px-2">
        <p class="text-xl font-medium block">
            What's your username?
        </p>

        <VInput
            propElementId="set-username"
            propLabel="Username"
            propPlaceholder=""
            :propMaxLength="propUsernameMaxLength"
            :propHasTextCounter="true"
            :propIsRequired="true"
            :propHasStatusText="true"
            :propStatusText="username_validation_status_text"
            :propIsError="username_validation_has_error"
            :propIsOk="username_is_ok === true"
            :propAllowWhitespace="false"
            @hasNewValue="validateUsername($event)"
            class="mt-6"
        />

        <div class="mt-6 pl-2">
            <p class="text-base">You can use full stops ('.') and underscores ('_') among letters and numbers.</p>
        </div>

        <!--main action-->
        <div class="mt-6 h-fit">
            <VActionSpecial
                @click.stop="submitUsernameChange()"
                :propIsEnabled="canSubmitNewUsername"
                propElement="button"
                type="button"
                propElementSize="m"
                propFontSize="m"
                class="w-full"
            >
                <span class="mx-auto">Set username</span>
            </VActionSpecial>
        </div>
    </div>
</template>


<script setup lang="ts">
    import VInput from '@/components/small/VInput.vue';
    import VActionSpecial from '../small/VActionSpecial.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    const bad_usernames = require( '../../../../voicewake/static/json/bad_usernames.en.json')['usernames'];
    const axios = require('axios');

    export default defineComponent({
        name: "UserOptionsApp",
        data() {
            return {
                username_string:"",
                username_validation_status_text: "",
                username_validation_has_error: false,
                username_is_ok: false,
                username_check_timeout: null as number|null,

                is_loading: false,
            };
        },
        props: {
            propUsernameMaxLength: {
                type: Number,
                default: 30
            },
        },
        computed: {
            canSubmitNewUsername() : boolean {

                return this.is_loading === false;
            },
        },
        emits: [
            'newUsername',
        ],
        methods: {
            newRegExp() : RegExp {

                //either entirely letters and numbers only,
                //or start and end with letters and numbers with possible '_' and '.' in between
                //with the addition of {1,30} for condition 1, constant 120+ steps becomes 6 steps
                //if '_' or '.', cannot continue with another '_' nor '.'

                //remember to remove '\' from string below if deciding to use as literal RegExp

                const default_regex = "(^[a-zA-Z0-9]{1," +
                    this.propUsernameMaxLength.toString() +
                    "}$)|(^[a-zA-Z0-9](_(?!(\\.|_))|\\.(?!(_|\\.))|[a-zA-Z0-9]){0," +
                    (this.propUsernameMaxLength - 2).toString() +
                    "}[a-zA-Z0-9]$)";

                //we use global flag, even though irrelevant, to gain access to .lastIndex on match for showing character error
                //is always >= 0, but it will never restart from 0, so we must restart it ourselves
                return new RegExp(default_regex, "g");
            },
            checkRegExpForDetailedErrorMessage(new_value:string) : string {

                //directly related to newRegExp()
                //because these are not mentioned to keep the tip simple, we only share these as errors when encountered

                if(/^\./.test(new_value) === true){

                    return "Cannot start with '.' for usernames.";

                }else if(/\.$/.test(new_value) === true){

                    return "Cannot end with '.' for usernames.";

                }else if(/^_/.test(new_value) === true){

                    return "Cannot start with '_' for usernames.";

                }else if(/_$/.test(new_value) === true){

                    return "Cannot end with '_' for usernames.";

                }else if(/\._/.test(new_value) === true){

                    return "'.' and '_' cannot be next to each other.";

                }else if(/_\./.test(new_value) === true){

                    return "'_' and '.' cannot be next to each other.";

                }else if(/\.\./.test(new_value) === true){

                    return "'.' and '.' cannot be next to each other.";

                }else if(/__/.test(new_value) === true){

                    return "'_' and '_' cannot be next to each other.";

                }else{

                    //here, '.' does not need '\'
                    const bad_char_index = new_value.search(/[^a-zA-Z0-9._]/);
                    const bad_char = new_value.charAt(bad_char_index);

                    return "Cannot use '" + bad_char + "' in usernames.";
                }
            },
            resetUsernameRelatedValues() : void {

                this.username_string = "";
                this.username_validation_status_text = "";
                this.username_validation_has_error = false;
                this.username_is_ok = false;

                this.username_check_timeout !== null ? window.clearTimeout(this.username_check_timeout) : null;
                this.username_check_timeout = null;
            },
            validateUsername(new_value:string) : void {

                this.resetUsernameRelatedValues();

                //do nothing if there is no text
                if(new_value.length === 0){

                    this.is_loading = false;
                    return;
                }

                this.is_loading = true;

                //has text
                this.username_check_timeout = window.setTimeout(() => {

                    //must not have any whitespace
                    //do not make this too complicated, it is easier to just send email and see if user receives it
                    if(bad_usernames.includes(new_value) === false && this.newRegExp().test(new_value) === true){

                        this.username_string = new_value;
                        this.username_is_ok = false;
                        this.username_validation_has_error = false;
                        this.username_validation_status_text = "";

                        this.checkUsernameExists();

                    }else if(bad_usernames.includes(new_value) === true){
                    
                        this.username_string = "";
                        this.username_is_ok = false;
                        this.username_validation_has_error = true;
                        this.username_validation_status_text = "That username is not allowed.";
                        this.is_loading = false;

                    }else if(/\s+/g.test(new_value) === true){

                        this.username_string = "";
                        this.username_is_ok = false;
                        this.username_validation_has_error = true;
                        this.username_validation_status_text = "Please remove all spaces.";
                        this.is_loading = false;

                    }else{

                        //will reach here if the problem is from regex
                        this.username_string = "";
                        this.username_is_ok = false;
                        this.username_validation_has_error = true;
                        this.username_validation_status_text = this.checkRegExpForDetailedErrorMessage(new_value);
                        this.is_loading = false;
                    }

                }, 400);
            },
            async checkUsernameExists() : Promise<void> {

                this.username_is_ok = false;
                this.is_loading = true;

                await axios.get(window.location.origin + "/api/users/username/get/" + this.username_string)
                .then((response:any) => {

                    if(response.data['data']['username'] !== this.username_string){

                        //don't do anything with stale requests
                        //luckily this edge case was caught
                        return;

                    }else if(response.data['data']['exists'] === false){

                        this.username_is_ok = true;
                        this.username_validation_has_error = false;
                        this.username_validation_status_text = "That username is available!";

                    }else{

                        this.username_is_ok = false;
                        this.username_validation_has_error = true;
                        this.username_validation_status_text = "That username is already taken.";
                    }

                    this.is_loading = false;
                })
                .catch((error: any) => {

                    this.username_is_ok = false;
                    this.username_validation_has_error = true;
                    this.username_validation_status_text = "An error had occurred. Try again later.";
                    console.log(error);

                    this.is_loading = false;
                });
            },
            async submitUsernameChange() : Promise<void> {

                //no need to proceed if error on validating username
                if(this.username_is_ok === false){

                    if(this.username_string.length === 0){

                        this.username_validation_has_error = true;
                        this.username_validation_status_text = "Please enter a username.";
                    }

                    return;
                }

                this.is_loading = true;

                let data = new FormData();
                data.append("username", this.username_string);

                await axios.post(window.location.origin + "/api/users/username/set", data)
                .then((response:any) => {

                    if(response.data['data']['exists'] === false){

                        console.log(response.data['message']);
                        this.$emit('newUsername', response.data['data']['username']);

                    }else{

                        //username is taken
                        this.username_is_ok = false;
                        this.username_validation_has_error = true;
                        this.username_validation_status_text = response.data['message'];
                        console.log(response.data['message']);
                    }

                    this.is_loading = false;
                })
                .catch((error: any) => {

                    console.log(error.response.data['message']);

                    this.is_loading = false;
                });
            },
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
        },
        mounted(){

            this.axiosSetup();
        }
    });
</script>