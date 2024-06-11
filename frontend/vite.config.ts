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
});