const path = require('path')
const BundleTracker = require('webpack-bundle-tracker')
const VueLoaderPlugin = require('vue-loader/lib/plugin')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const CleanWebpackPlugin = require('clean-webpack-plugin')
const prod = process.env.NODE_ENV === 'production'

module.exports = {
    context: __dirname,
    mode: prod ? 'production' : 'development',
    entry: {
        main: [
            './js/src/main.js', // main site js
            './scss/main.scss' // main site styles
        ],
        search: './js/src/search.js', // vue components & styles for search pages
    },
    output: {
        path: path.resolve(__dirname, 'static'), // where to output bundles
        publicPath: prod ? '/static/' : 'http://localhost:3000/', // tell Django where to serve bundles from
        filename: prod ? 'js/[name]-[hash].js' : 'js/[name].js', // append hashes in prod
    },
    module: {
        rules: [
            { // compile Vue Single-File Components (SFCs)
                test: /\.vue$/,
                loader: 'vue-loader',
                options: {
                    loaders: {
                        'scss': [ // compile <style lang=scss> blocks inside SFCs
                            prod ? MiniCssExtractPlugin.loader : 'vue-style-loader', // use vue-style-loader for hot reload in dev
                            'css-loader',
                            'postcss-loader', // for autoprefixer
                            'sass-loader',
                        ]
                    }
                }
            },
            { // transpile ES6+ to ES5 using Babel, including tests
                test: /^(?!.*\.spec\.js$).*\.js$/,
                use: prod ? ['babel-loader'] : [
                    { // use istanbul for coverage when developing
                        loader: 'istanbul-instrumenter-loader',
                        options: { esModules: true }
                    }, 'babel-loader'
                ],
                exclude: /node_modules/, // don't transpile dependencies
            },
            { // load and compile styles to CSS
                test: /\.(sa|sc|c)ss$/,
                use: [
                    prod ? MiniCssExtractPlugin.loader : 'style-loader', // use style-loader for hot reload in dev
                    'css-loader',
                    'postcss-loader', // for autoprefixer
                    'sass-loader',
                ],
            },
            { // load images
                test: /\.(png|jpg|gif|svg)$/,
                loader: 'file-loader',
                options: {
                  name: prod ? 'img/[name]-[hash].[ext]' : 'img/[name].[ext]', // append hashes in prod
                }
            }
        ]
    },
    plugins: [
        new BundleTracker({ filename: 'webpack-stats.json' }), // tells Django where to find webpack output
        new VueLoaderPlugin(), // necessary for vue-loader to work
        new MiniCssExtractPlugin({ // extracts CSS to a single file per entrypoint
            filename: prod ? 'css/[name]-[hash].css' : 'css/[name].css', // append hashes in prod
        }),
        ...(prod ? [new CleanWebpackPlugin('static')] : []), // clear out static when rebuilding
    ],
    resolve: {
        alias: { 'vue$': 'vue/dist/vue.esm.js' }, // use the esmodule version of Vue
        extensions: ['*', '.js', '.vue', '.json'] // enables importing these without extensions
    },
    devServer: {
        contentBase: path.join(__dirname, 'static'), // serve this as webroot
        overlay: true,
        port: 3000,
        allowedHosts: ['localhost'],
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
            'Access-Control-Allow-Headers': 'X-Requested-With, content-type, Authorization',
        },
        stats: { // hides file-level verbose output when server is running
            children: false, 
            modules: false,
        }
    },
    devtool: prod ? 'source-map' : 'eval-source-map', // enable sourcemaps
}
