// Tells TypeScript that importing "something.css?raw" gives the file's text.
declare module '*.css?raw' {
  const css: string
  export default css
}
