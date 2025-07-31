/* eslint-disable */
//
// Patch Worker to allow loading scripts from remote URLs
//credits:
    //https://github.com/jantimon/remote-web-worker/tree/main
//
//original issue:
    //Worker() does not accept URL that is from another origin, i.e. cross-origin
//
//context:
    //we are trying to import web worker script from AWS Cloudfront domain name, and running it on voicewake.com domain
        //we are already importing all Vue code from Cloudfront, but CORS fails for web worker only
    //through tests, native Worker requests for passed URL without required headers by CloudFront CORS
        //Access-Control-Requests-Headers
        //Access-Control-Requests-Method
    //cannot add headers manually for the Worker
//
//successful solution:
    //create a Blob that represents <link type="text/javascript">
    //Blob is created, and is considered as same-origin
    //use backtick (`) for template literal, i.e. code in it is treated as script and executed at runtime
    //run importScripts() in the <link> Blob to get Worker JS file, located in another domain, i.e. cross-origin
    //create URL.createObjectURL() for Blob
    //this solution overrides native Worker when imported
    //use eslint-disable to silence warning for this entire file during compiling
    //Webpack recognises "Worker(new URL())", and compiles files correctly, with correct static linking
    //Worker accepts local URL, JS file for Worker is cached, and everything is ok
//
//previous failed solutions:
    //enabled CORS at S3 and CloudFront
        //did not work, due to Worker's own lack of headers
        //self-testing curl at Windows cmd, with headers set, has proven this
    //NGINX proxy_pass from own domain to CloudFront
        //simply did not work
    //create own class that returns Worker, then import the class via alias to replace native Worker
        //failed because:
            //TS sees that new Worker has no native Worker's functions
        //class extends also didn't work
    //use same solution as this solution, but do it all in the same place that creates the Worker
        //requires some processing, which ultimately leads to "new Worker(val_with_url)"
        //failed because:
            //Webpack sees your variable that stores URL(), and the Worker file created ends up with wrong MIME type
            //Webpack only recognises "new Worker(new URL())"
//
//untested solutions:
    //data URL, e.g. passes "data: ..."
        //different browsers argue about the validity of this
    //add listener to message, and run a script
        //seems hacky
    //change Webpack configs
        //seems hacky, and potentially extra maintenance on every update
//
//references
    //https://developer.mozilla.org/en-US/docs/Web/API/Worker/Worker
    //https://developer.mozilla.org/en-US/docs/Web/API/WorkerGlobalScope/importScripts
//
//Compatibility: Chrome 4+, Firefox 4+, Safari 4+
//
//Usage:
    // ```ts
    //place this file at vue_app@/...
    //then at vue_app@/components/small/comp.vue:
        //<script lang="ts">
            //import '@/patches/cors_worker_patch';
            //...
    // ```
typeof window !== "undefined" &&
    (Worker = ((BaseWorker: typeof Worker) =>
        class Worker extends BaseWorker {
            constructor(scriptURL: string | URL, options?: WorkerOptions) {
                const url = String(scriptURL);
                super(
                    // Check if the URL is remote
                    url.includes("://") && !url.startsWith(location.origin)
                    ? // Launch the worker with an inline script that will use `importScripts`
                    // to bootstrap the actual script to work around the same origin policy.
                    URL.createObjectURL(
                        new Blob(
                            [
                                // Replace the `importScripts` function with
                                // a patched version that will resolve relative URLs
                                // to the remote script URL.
                                //
                                // Without a patched `importScripts` Webpack 5 generated worker chunks will fail with the following error:
                                //
                                // Uncaught (in promise) DOMException: Failed to execute 'importScripts' on 'WorkerGlobalScope':
                                // The script at 'http://some.domain/worker.1e0e1e0e.js' failed to load.
                                //
                                // For minification, the inlined variable names are single letters:
                                // i = original importScripts
                                // a = arguments
                                // u = URL
                                `importScripts=((i)=>(...a)=>i(...a.map((u)=>''+new URL(u,"${url}"))))(importScripts);importScripts("${url}")`,
                            ],
                            { type: "text/javascript" }
                        )
                    )
                    : scriptURL,
                    options
                );
            }
        })(Worker)
    );

export {};