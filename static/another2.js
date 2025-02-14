let scene, camera, renderer, grid, gridVertices;
let container;

function init() {
    // Get container reference
    container = document.getElementById('canvas');
    
    // Ensure container has relative or absolute positioning
    if (getComputedStyle(container).position === 'static') {
        container.style.position = 'relative';
    }

    scene = new THREE.Scene();
    
    // Set up renderer with better quality and contained positioning
    renderer = new THREE.WebGLRenderer({ 
        alpha: true,
        antialias: true,
        powerPreference: "high-performance"
    });
    renderer.setPixelRatio(window.devicePixelRatio);
    
    // Position the renderer within the container
    renderer.domElement.style.position = 'absolute';
    renderer.domElement.style.top = '0';
    renderer.domElement.style.left = '0';
    renderer.domElement.style.width = '100%';
    renderer.domElement.style.height = '100%';
    renderer.domElement.style.zIndex = '-1'; // Place behind container content
    
    // Set initial size based on container
    updateSize();
    container.appendChild(renderer.domElement);
    
    // Camera setup based on container dimensions
    const aspectRatio = container.clientWidth / container.clientHeight;
    camera = new THREE.PerspectiveCamera(60, aspectRatio, 0.1, 1000);
    camera.position.set(0, 30, 70);
    camera.lookAt(0, 0, 0);

    // Create gradient background
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 1;
    canvas.height = 2;
    
    const gradient = context.createLinearGradient(0, 0, 0, 2);
    gradient.addColorStop(0, '#120025');
    gradient.addColorStop(1, '#000066');
    context.fillStyle = gradient;
    context.fillRect(0, 0, 1, 2);
    
    const texture = new THREE.CanvasTexture(canvas);
    scene.background = texture;

    // Create responsive grid based on container size
    const gridSize = Math.max(200, container.clientWidth / 10);
    createMainGrid(gridSize);
    createSecondaryGrid(gridSize);
}

function createMainGrid(gridSize) {
    const material = new THREE.LineBasicMaterial({ 
        color: 0xff1493,
        linewidth: 1.5,
        opacity: 0.8,
        transparent: true
    });
    
    const geometry = new THREE.BufferGeometry();
    const vertices = [];

    for (let i = -gridSize / 2; i <= gridSize / 2; i += 2) {
        for (let j = -gridSize / 2; j <= gridSize / 2; j += 2) {
            vertices.push(i*2, 0, j*2);
        }
    }

    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    grid = new THREE.LineSegments(geometry, material);
    scene.add(grid);
    gridVertices = geometry.attributes.position.array;
}

function createSecondaryGrid(gridSize) {
    const horizonMaterial = new THREE.LineBasicMaterial({
        color: 0x00ffff,
        opacity: 0.5,
        transparent: true
    });
    
    const horizonGeometry = new THREE.BufferGeometry();
    const horizonVertices = [];
    
    for (let i = -gridSize / 2; i <= gridSize / 2; i += 4) {
        horizonVertices.push(-gridSize, 0, i);
        horizonVertices.push(gridSize, 0, i);
    }
    
    horizonGeometry.setAttribute('position', new THREE.Float32BufferAttribute(horizonVertices, 3));
    const horizonGrid = new THREE.LineSegments(horizonGeometry, horizonMaterial);
    scene.add(horizonGrid);
}

function animate() {
    requestAnimationFrame(animate);

    const time = Date.now() * 0.001;
    
    // Wave animation
    for (let i = 0; i < gridVertices.length; i += 3) {
        const x = gridVertices[i];
        const z = gridVertices[i + 2];
        gridVertices[i + 1] = 
            Math.sin(time + x * 0.08) * 2 + 
            Math.cos(time + z * 0.08) * 2 +
            Math.sin(Math.sqrt(x * x + z * z) * 0.05 + time) * 1.5;
    }

    grid.geometry.attributes.position.needsUpdate = true;
    
    // Subtle camera movement
    camera.position.y = 30 + Math.sin(time * 0.5) * 2;
    camera.lookAt(0, 0, 0);
    
    renderer.render(scene, camera);
}

function updateSize() {
    const width = container.clientWidth;
    const height = container.clientHeight;
    renderer.setSize(width, height);
}

function onWindowResize() {
    // Update camera
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    
    // Update renderer
    updateSize();
    
    // Update grid size based on new container size
    const newGridSize = Math.max(100, container.clientWidth / 10);
    scene.remove(grid);
    createMainGrid(newGridSize);
}

// Create a ResizeObserver to watch container size changes
const resizeObserver = new ResizeObserver(() => {
    onWindowResize();
});

// Start animation when everything is loaded
document.addEventListener('DOMContentLoaded', () => {
    init();
    animate();
    
    // Start observing the container for size changes
    resizeObserver.observe(container);
});

// Cleanup function
function cleanup() {
    resizeObserver.disconnect();
    window.removeEventListener('resize', onWindowResize);
    renderer.dispose();
    scene.clear();
}
