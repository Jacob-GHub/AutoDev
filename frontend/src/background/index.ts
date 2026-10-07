// Background service worker.
//
// AutoDev's UI runs entirely in the content script, so there is nothing to do here yet.
// The file exists because the manifest declares a service worker, and the development
// auto-reload (webpack-ext-reloader) works through it.

chrome.runtime.onInstalled.addListener(() => {
  // Runs once when the extension is installed or updated.
})
