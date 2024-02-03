const path = require('path');

const static_dir = '/static/frontend/';
const output_dir = '../static/frontend/';

function getPublicPath(){
    if(process.env.NODE_ENV === 'production'){
        //AWS_S3_CUSTOM_DOMAIN, i.e. CloudFront, can get from project root env/.env
        return 'https://d3cej2n7sifsea.cloudfront.net' + static_dir;
    }
    return static_dir;
}

module.exports = {
    publicPath: getPublicPath(), //where to get files from, via URL
    outputDir: path.resolve(__dirname, output_dir),  //where to put Vue files
    filenameHashing: false, // Django will hash file names, not webpack
    runtimeCompiler: true, // See: https://vuejs.org/v2/guide/installation.html#Runtime-Compiler-vs-Runtime-only
    devServer: {
        devMiddleware: {
            // see https://github.com/webpack/webpack-dev-server/issues/2958
            writeToDisk: true, 
        },
    },
};