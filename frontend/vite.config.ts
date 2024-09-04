import { defineConfig } from 'vite';
import { fileURLToPath, URL } from 'node:url';
import vue from '@vitejs/plugin-vue';


//using --env as custom option, this is the build command example:
//vite build --emptyOutDir -- --env=dev


//determine dev/stage/prod based on value passed into custom option --env during vite build
function determineEnv() : 'dev'|'stage'|'prod' {

    const accepted_values = ['dev', 'stage', 'prod'];
    let build_env = "";

    for(let x = 0; x < process.argv.length; x++){

        if(process.argv[x].startsWith('--env=', 0) === false){

            continue;

        }else{

            //found arg that has string "--env="
            build_env = process.argv[x].split('--env=')[1];
        }
    }

    if(build_env === ""){

        throw new Error("Required arg '--env=' was not found.");
    }

    if(accepted_values.includes(build_env) === false){

        throw new Error("Value for arg '--env=' is invalid.");
    }

    return build_env as 'dev'|'stage'|'prod';
}


//depends on what we specify for STATICFILES_LOCATION at Django settings that collectstatic will then use
function determineBaseURL(env_value:'dev'|'stage'|'prod'){

    switch(env_value){

        case 'dev':

            return './';

        case 'stage':

            return '/static/stage/frontend/js/';

        case 'prod':

            return '/static/prod/frontend/js/';

        default:

            throw new Error('Invalid env_value');
    }
}


// https://vitejs.dev/config/
export default defineConfig({
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url)),
        },
    },
    plugins: [
        vue(),
        //if you get hydration mismatch error at console using files from production build, refer to this URL:
            //https://vuejs.org/api/compile-time-flags#vite
    ],
    build: {
        rollupOptions: {
            input: {
                main: './src/main.ts',
            },
            output: {
                //output to local static
                dir: '../static/frontend/js/',
                //during dev, Vite serves main.ts with correct MIME
                //with build, the file ending with .ts is resolved to MIME "video/mp2t", as per NGINX mime.types, so we should use .js instead
                entryFileNames: '[name].js',
            },
        },
        cssCodeSplit: false,
    },
    //influences import.meta.url, e.g. web workers
    //in production, since we call main.js via CloudFront URL, it will reference cloudfront.net
    //we fetch files via cloudfront.net/static, but import.meta.url knows nothing about build output dir, so it does .net/assets and fails
    //if not './', must be absolute path, i.e. no './', as it is warned during build
    base: determineBaseURL(determineEnv()),
});