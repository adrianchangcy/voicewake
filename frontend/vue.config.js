const path = require('path');

module.exports = {
    publicPath: '/static/frontend/', //not sure when this is used
    outputDir: path.resolve(__dirname, '../static/frontend/'),  //where to put served Vue files
    filenameHashing: false, // Django will hash file names, not webpack
    runtimeCompiler: true, // See: https://vuejs.org/v2/guide/installation.html#Runtime-Compiler-vs-Runtime-only
    devServer: {
        devMiddleware: {
            // see https://github.com/webpack/webpack-dev-server/issues/2958
            writeToDisk: true, 
        },
    },
};

//https://betterprogramming.pub/vue-django-using-vue-files-and-the-vue-cli-d6dd8c9145eb
//publicPath
    //tells Vue where to look for its other files once it’s on the internet
        //i.e. what URL my other files will live at
    //Django puts them all behind STATIC_URL and the path to our output directory
//outputDir
    //tells Vue where to write its files in the file system
    //his is the big one, and here I’ve pointed it to root folder's static
        //we've just added this to STATICFILES_DIRS
    //we also specify a namespaced path to make sure Vue files don’t get mixed up with others
    // ../ means exit one level from current directory
//filenameHashing
    //by default, Vue hashes file names
        //to make sure we have the most recent version (not a cached old version of the file)
        //however, that messes up Django’s ability to predict and track file names across changes
        //instead, we can use ManifestStaticfilesStorage with Django to accomplish the same task
//runtimeCompiler
    //turned on because we’re doing tricky stuff with webpack and we want the full build
    //you may be able to remove this setting if your project works without it
        //will make your deployment 30% lighter in weight
            //Read about the runtime compiler in the Vue docs
//writeToDisk
    //we write to disk in development mode so that Django can pick up those files
    //instead of the compilation happening on the fly inside of Vue