// Import Lenis at the top of your JavaScript file
import Lenis from '@studio-freight/lenis'

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lenis for each events track
    const eventTracks = document.querySelectorAll('.events-track')
    
    eventTracks.forEach(track => {
        const lenis = new Lenis({
            wrapper: track,
            content: track.querySelector('.events-wrapper'),
            duration: 1.2,
            easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
            direction: 'horizontal',
            gestureDirection: 'horizontal',
            smooth: true,
            mouseMultiplier: 1,
            smoothTouch: false,
            touchMultiplier: 2,
            infinite: false,
        })

        // RAF for this specific track
        function raf(time) {
            lenis.raf(time)
            requestAnimationFrame(raf)
        }

        requestAnimationFrame(raf)

        // Optional: Add drag scrolling
        let isDown = false
        let startX
        let scrollLeft

        track.addEventListener('mousedown', (e) => {
            isDown = true
            track.classList.add('active')
            startX = e.pageX - track.offsetLeft
            scrollLeft = track.scrollLeft
        })

        track.addEventListener('mouseleave', () => {
            isDown = false
            track.classList.remove('active')
        })

        track.addEventListener('mouseup', () => {
            isDown = false
            track.classList.remove('active')
        })

        track.addEventListener('mousemove', (e) => {
            if (!isDown) return
            e.preventDefault()
            const x = e.pageX - track.offsetLeft
            const walk = (x - startX) * 2
            track.scrollLeft = scrollLeft - walk
        })
    })
})