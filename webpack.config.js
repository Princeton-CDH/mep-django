const path = require('path')
const BundleTracker = require('webpack-bundle-tracker');
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const globImporter = require('node-sass-glob-importer');
const TerserPlugin = require('terser-webpack-plugin')
const devMode = process.env.NODE_ENV !== 'production' // i.e. not prod or qa

module.exports = env => ({
    context: path.resolve(__dirname, 'srcmedia'),
    mode: devMode ?  'development' : 'production',
    entry: {
        main: [
            './ts/main.ts', // main site script
            './scss/main.scss' // site styles
        ],
        memberSearch: './ts/members-search.ts',
        memberMap: [
            path.resolve(__dirname, 'node_modules/leaflet/dist/leaflet.css'),
            './ts/members-map.ts',
        ],
        membershipGraphs: './ts/membership-graphs.ts',
        booksSearch: './ts/books-search.ts',
        activities: './ts/activities.ts',
        cardSearch: './ts/cards-search.ts',
        landing: './ts/pages/landing.ts',
        cardViewer: './ts/pages/card-viewer.ts',
        pdf: './js/controllers/pdf.js', // wagtail stimulus extension for PDF generation
        print: './scss/print.scss' // print styles
    },
    output: {
        path: path.resolve(__dirname, 'bundles'), // where to output bundles
        publicPath: devMode ? 'http://localhost:3000/' : '/static/', // tell Django where to serve bundles from
        filename: devMode ? 'js/[name].js' : 'js/[name]-[hash].min.js', // append hashes in prod/qa
    },
    module: {
        rules: [
            { // compile TypeScript to js
                test: /\.tsx?$/,
                loader: 'ts-loader',
                exclude: /node_modules/, // don't transpile dependencies
            },
            { // ensure output js has preserved sourcemaps
                enforce: "pre",
                test: /\.js$/,
                loader: "source-map-loader"
            },
            { // transpile ES6+ to ES5 using Babel
                test: /\.js$/,
                loader: 'babel-loader',
                exclude: /node_modules/, // don't transpile dependencies
            },
            { // load and compile styles to CSS
                test: /\.(sa|sc|c)ss$/,
                use: [
                    devMode ? 'style-loader' : MiniCssExtractPlugin.loader, // use style-loader for hot reload in dev
                    { loader: 'css-loader', options: { url: false } },
                    'postcss-loader', // for autoprefixer
                    "resolve-url-loader",
                    { loader: 'sass-loader', options: {
                        sassOptions: {
                                importer: globImporter()
                            }
                        }
                    }, // allow glob scss imports
                ],
            },
            { // load images
                test: /\.(png|jpg|gif|svg)$/,
                loader: 'file-loader',
                options: {
                  name: devMode ? 'img/[name].[ext]' : 'img/[name]-[hash].[ext]', // append hashes in prod/qa
                }
            }
        ]
    },
    plugins: [
        new BundleTracker({ path: __dirname, filename: 'webpack-stats.json' }), // tells Django where to find webpack output
        new MiniCssExtractPlugin({ // extracts CSS to a single file per entrypoint
            filename: devMode ? 'css/[name].css' : 'css/[name]-[hash].min.css', // append hashes in prod/qa
        }),
        ...(devMode ? [] : [new CleanWebpackPlugin({
            cleanOnceBeforeBuildPatterns: [ 'bundles/**'],  // clear out static when rebuilding in prod/qa
        })]),
    ],
    resolve: {
        extensions: ['.js', '.jsx', '.ts', '.tsx', '.json', '.scss'] // enables importing these without extensions
    },
    devServer: {
        // contentBase: path.join(__dirname, 'bundles'), // serve this as webroot
        // overlay: true,
        port: 3000,
        allowedHosts: ['localhost'],
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
            'Access-Control-Allow-Headers': 'X-Requested-With, content-type, Authorization',
        },
        // stats: { // hides file-level verbose output when server is running
        //     children: false,
        //     modules: false,
        // }
    },
    devtool: 'source-map', // allow sourcemaps in dev & qa
    optimization: {
        minimizer: [
            new TerserPlugin({ // minify JS in prod
                terserOptions: {
                   // cache: true, // cache unchanged assets
                    sourceMap: env.maps // preserve sourcemaps if env.maps was passed
                },
                parallel: true, // run in parallel (recommended)
            }),
          //   new OptimizeCSSAssetsPlugin({ // minify CSS in prod/qa
          //       ... (env.maps && { cssProcessorOptions: { // if env.maps was passed,
          //           map: { inline: false, annotation: true } // preserve sourcemaps
          //       }})
          //   }),
          new CssMinimizerPlugin(),
        ]
    }
})
