import { defineConfig } from 'vite';
import { fileURLToPath, URL } from 'node:url';
import vue from '@vitejs/plugin-vue';
// import tailwindcss from '@tailwindcss/vite';


//using --env as custom option, this is the build command example:
//vite build --emptyOutDir -- --env=dev


//determine dev/stage/prod based on value passed into custom option --env during vite build
function determineEnv() : 'dev'|'stage'|'prod' {

    //if "build" exists, then --env is required
    //if "build" does not exist, just use "dev"

    let arg_build_exists = false;

    for(let x = 0; x < process.argv.length; x++){

        if(process.argv[x] === "build"){

            arg_build_exists = true;
        }
    }

    if(arg_build_exists === false){

        return 'dev';
    }

    const accepted_values = ['dev', 'stage', 'prod'];
    let build_env = "";

    for(let x = 0; x < process.argv.length; x++){

        if(process.argv[x].startsWith('--env=', 0) === false){

            continue;

        }else{

            //found arg that has string "--env="
            build_env = process.argv[x].split('--env=')[1];
            break;
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
        //currently not using tailwind v4 + Vite, because it doesn't edit output.css
        // tailwindcss(),
    ],
    server: {
        host: true,
        //these are from /nginx/Dockerfile creating SSL via openSSL and exporting to /nginx, with bind mount to /nginx
        //cannot use mkcert() from vite-plugins-mkcert, since it only accounts for direct visit, and not nginx->server->vite
        https: {
            cert: '/nginx/dev-nginx-ssl.crt',
            key: '/nginx/dev-nginx-ssl.key',
        },
        //needed this for nginx <-> django + URL to vue dev
        //https://vite.dev/config/server-options#server-cors
        cors: {
            origin: ['https://127.0.0.1:8080', 'https://192.168.1.200:8080'],
        },
    },
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