export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bloomberg: {
          black: "#000000",
          gray: "#1a1a1a",
          lightGray: "#2a2a2a",
          emerald: "#00ff9f",
          teal: "#00d1b2",
          orange: "#ff8c00",
          yellow: "#ffd700",
          red: "#ff3860",
          blue: "#209cee",
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}
