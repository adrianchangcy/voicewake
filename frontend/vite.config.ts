import { defineConfig } from 'vite';
import { fileURLToPath, URL } from 'node:url';
import vue from '@vitejs/plugin-vue';

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
                dir: '../static/frontend/js/',
                //during dev, Vite serves main.ts with correct MIME
                //with build, the file ending with .ts is resolved to MIME "video/mp2t", as per NGINX mime.types, so we should use .js instead
                entryFileNames: '[name].js',
            },
        },
    },
    //influences import.meta.url, e.g. web workers
    //in production, since we call main.js via CloudFront URL, it will reference cloudfront.net
    //we fetch files via cloudfront.net/static, but import.meta.url knows nothing about build output dir, so it does .net/assets and fails
    //if not './', must be absolute path, i.e. no './', as it is warned during build
    base: process.env.NODE_ENV === 'production' ? '/static/frontend/js/' : './',
});