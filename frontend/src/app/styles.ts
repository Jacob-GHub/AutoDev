// The "?raw" suffix imports each stylesheet as a plain string instead of injecting it
// into the page (webpack.config.js has a rule for this). A Shadow DOM can't see
// page stylesheets, so content/index.tsx puts this text in a <style> tag inside it.
import baseCss from './base.css?raw'
import gloopCss from '../components/gloop/gloop.css?raw'
import panelCss from '../components/panel/panel.css?raw'

export const appStyles = [baseCss, gloopCss, panelCss].join('\n')
