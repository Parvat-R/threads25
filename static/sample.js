// First, install required dependencies:
// npm install @studio-freight/lenis

// Import Lenis
import Lenis from '@studio-freight/lenis'

// Initialize smooth scroll
const lenis = new Lenis({
  duration: 1.2,
  easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
  direction: 'vertical',
  gestureDirection: 'vertical',
  smooth: true,
  smoothTouch: false,
  touchMultiplier: 2
})

// Sync with requestAnimationFrame
function raf(time) {
  lenis.raf(time)
  requestAnimationFrame(raf)
}

requestAnimationFrame(raf)

// Dark theme styles
const styles = `
:root {
  --background: #121212;
  --text-primary: #e0e0e0;
  --text-secondary: #a0a0a0;
  --accent: #bb86fc;
}

body {
  background-color: var(--background);
  color: var(--text-primary);
  font-family: system-ui, -apple-system, sans-serif;
  line-height: 1.6;
  margin: 0;
  padding: 0;
  transition: background-color 0.3s ease;
}

/* Darkroom-inspired section styling */
.section {
  min-height: 100vh;
  padding: 4rem 2rem;
  position: relative;
  overflow: hidden;
}

.section::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at center, 
    rgba(187, 134, 252, 0.03) 0%,
    rgba(18, 18, 18, 0) 70%);
  pointer-events: none;
}

/* Typography */
h1, h2, h3 {
  color: var(--accent);
  font-weight: 700;
  letter-spacing: -0.02em;
}

p {
  margin-bottom: 1.5em;
  max-width: 65ch;
}

/* Links */
a {
  color: var(--accent);
  text-decoration: none;
  transition: opacity 0.2s ease;
}

a:hover {
  opacity: 0.8;
}

/* Images */
img {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  opacity: 0.9;
  transition: opacity 0.3s ease;
}

img:hover {
  opacity: 1;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: var(--background);
}

::-webkit-scrollbar-thumb {
  background: var(--accent);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: color-mix(in srgb, var(--accent) 80%, white);
}
`

// Add styles to document
const styleSheet = document.createElement('style')
styleSheet.textContent = styles
document.head.appendChild(styleSheet)