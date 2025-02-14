let scene, camera, renderer, points;

function init() {
    // Get the container element
    const container = document.getElementById('canvas');
    
    // Scene setup
    scene = new THREE.Scene();
    
    // Use container dimensions instead of window
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    renderer = new THREE.WebGLRenderer({ alpha: true }); // Enable transparency
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);

    // Create particles
    const particles = 25000; // Reduced for better performance
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particles * 3);
    const colors = new Float32Array(particles * 3);

    // Adjust particle spread based on container size
    const spread = Math.min(width, height) / 2;
    const halfSpread = spread / 2;

    for (let i = 0; i < positions.length; i += 3) {
        const x = Math.random() * spread - halfSpread;
        const y = Math.random() * spread - halfSpread;
        const z = Math.random() * spread - halfSpread;

        positions[i] = x;
        positions[i + 1] = y;
        positions[i + 2] = z;

        // Normalize colors based on position
        const vx = (x / spread) + 0.5;
        const vy = (y / spread) + 0.5;
        const vz = (z / spread) + 0.5;

        colors[i] = vx;
        colors[i + 1] = vy;
        colors[i + 2] = vz;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
        size: 1.5, // Reduced size for container
        vertexColors: true,
        blending: THREE.AdditiveBlending,
        transparent: true,
        opacity: 0.6
    });

    points = new THREE.Points(geometry, material);
    scene.add(points);

    // Adjust camera position based on container size
    camera.position.z = spread;
}

function animate() {
    requestAnimationFrame(animate);

    const positions = points.geometry.attributes.position.array;
    const time = Date.now() * 0.0005; // Slowed down animation

    for (let i = 0; i < positions.length; i += 3) {
        const x = positions[i];
        const y = positions[i + 1];
        const z = positions[i + 2];

        // Gentler wave movement
        positions[i + 1] = y + Math.sin(time + x * 0.003) * 0.3;
    }

    points.geometry.attributes.position.needsUpdate = true;
    renderer.render(scene, camera);
}

function onWindowResize() {
    const container = document.getElementById('canvas');
    const width = container.clientWidth;
    const height = container.clientHeight;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
}

// Handle both window and container resize
window.addEventListener('resize', onWindowResize, false);

// Create a ResizeObserver to handle container size changes
const resizeObserver = new ResizeObserver(entries => {
    for (let entry of entries) {
        if (entry.target.id === 'canvas') {
            onWindowResize();
        }
    }
});

// Start observing the container
const container = document.getElementById('canvas');
resizeObserver.observe(container);

// Initialize only after DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    init();
    animate();
});