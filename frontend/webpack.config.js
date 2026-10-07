/* eslint-disable @typescript-eslint/no-var-requires */
const path = require('path')
const { CleanWebpackPlugin } = require('clean-webpack-plugin')
const WebpackBar = require('webpackbar')
const CopyWebpackPlugin = require('copy-webpack-plugin')
const TerserPlugin = require('terser-webpack-plugin')
const ExtensionReloader = require('webpack-ext-reloader')

const isDev = process.env.NODE_ENV === 'development'

// Each entry becomes one script in dist/js, referenced by public/manifest.json.
const entries = {
  'js/content': './src/content/index.tsx', // the UI injected into GitHub
  'js/background': './src/background/index.ts', // service worker (used by dev auto-reload)
}

// Files copied into dist as-is.
const copyFiles = [
  { from: path.resolve('public/manifest.json'), to: path.resolve('dist') },
  { from: path.resolve('assets'), to: path.resolve('dist/assets') },
]

// In development, reload the extension whenever the code changes.
// https://github.com/SimplifyJobs/webpack-ext-reloader
const hotReload = isDev
  ? [
      new ExtensionReloader({
        reloadPage: true,
        manifest: path.resolve(__dirname, 'public/manifest.json'),
      }),
    ]
  : []

const babelOptions = {
  cacheDirectory: true,
  presets: ['@babel/preset-react', ['@babel/preset-env']],
}

module.exports = {
  mode: isDev ? 'development' : 'production',
  entry: entries,
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name].js',
    publicPath: '/',
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        use: { loader: 'babel-loader', options: babelOptions },
        exclude: /node_modules/,
      },
      {
        test: /\.ts(x?)$/,
        use: [{ loader: 'babel-loader', options: babelOptions }, { loader: 'ts-loader' }],
        exclude: /node_modules/,
      },
      // Import "file.css?raw" as a plain string. The UI lives in a Shadow DOM,
      // so its styles are injected there as text instead of into the page.
      { test: /\.css$/, resourceQuery: /raw/, type: 'asset/source' },
    ],
  },
  plugins: [
    new CleanWebpackPlugin(),
    ...hotReload,
    new CopyWebpackPlugin({ patterns: copyFiles }),
    new WebpackBar(),
  ],
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
  },
  optimization: {
    minimize: !isDev,
    minimizer: [
      new TerserPlugin({
        terserOptions: { format: { comments: false } },
        extractComments: false,
      }),
    ],
  },
}
