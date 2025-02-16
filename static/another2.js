let scene, camera, renderer, grid;
let SEPARATION = 100, AMOUNTX = 50, AMOUNTY = 50;

let mouseX = 0;
let mouseY = 0;

let windowHalfX = window.innerWidth / 2;
let windowHalfY = window.innerHeight / 2;

function onDocumentMouseMove(event) {
    mouseX = event.clientX - windowHalfX;
    mouseY = event.clientY - windowHalfY;
}

// Add this event listener to track mouse movement
document.addEventListener('mousemove', onDocumentMouseMove, false);

function init() {
    scene = new THREE.Scene();
    
    renderer = new THREE.WebGLRenderer({ 
        antialias: true,
        powerPreference: "high-performance"
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    
    const container = document.getElementById('canvas');
    if (!container) return;
    
    container.style.position = 'fixed';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.zIndex = '-1';
    
    updateRendererSize();
    container.appendChild(renderer.domElement);

    // Camera setup
    const aspectRatio = container.clientWidth / container.clientHeight;
    camera = new THREE.PerspectiveCamera(75, aspectRatio, 1, 10000);
    camera.position.set(0, 1000, 1500);
    camera.lookAt(0, 0, 0);

    // Create gradient background
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 1;
    canvas.height = 2;
    
    const gradient = context.createLinearGradient(0, 0, 0, 2);
    gradient.addColorStop(0, '#1a0033');
    gradient.addColorStop(1, '#000066');
    context.fillStyle = gradient;
    context.fillRect(0, 0, 1, 2);
    
    const texture = new THREE.CanvasTexture(canvas);
    scene.background = texture;

    createGrid();
}

function createGrid() {
    const isMobile = window.innerWidth < 768;
    // Adjust grid density based on device
    AMOUNTX = isMobile ? 30 : 50;
    AMOUNTY = isMobile ? 30 : 50;
    SEPARATION = isMobile ? 80 : 100;

    // Create grid geometry
    const geometry = new THREE.BufferGeometry();
    const material = new THREE.LineBasicMaterial({
        color: 0xff1493, // Deep pink color
        opacity: 0.8,
        transparent: true
    });

    const positions = [];
    const indices = [];
    let vertexIndex = 0;

    // Create vertices
    for (let iy = 0; iy < AMOUNTY; iy++) {
        for (let ix = 0; ix < AMOUNTX; ix++) {
            const x = ix * SEPARATION - ((AMOUNTX * SEPARATION) / 2);
            const z = iy * SEPARATION - ((AMOUNTY * SEPARATION) / 2);
            positions.push(x*2, 0, z*2);
            
            // Create horizontal lines
            if (ix < AMOUNTX - 1) {
                indices.push(vertexIndex, vertexIndex + 1);
            }
            // Create vertical lines
            if (iy < AMOUNTY - 1) {
                indices.push(vertexIndex, vertexIndex + AMOUNTX);
            }
            
            vertexIndex++;
        }
    }

    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setIndex(indices);

    grid = new THREE.LineSegments(geometry, material);
    scene.add(grid);
}

// function animate() {
//     requestAnimationFrame(animate);

//     const positions = grid.geometry.attributes.position.array;
//     const time = Date.now() * 0.001;

//     let i = 1; // y-coordinate index
//     for (let ix = 0; ix < AMOUNTX; ix++) {
//         for (let iy = 0; iy < AMOUNTY; iy++) {
//             positions[i] = (Math.sin((ix + time) * 0.3) * 70) +
//                           (Math.sin((iy + time) * 0.5) * 70);
//             i += 3;
//         }
//     }

//     grid.geometry.attributes.position.needsUpdate = true;

//     // Smooth camera movement
//     camera.position.x = Math.sin(time * 0.8) * 200;
//     camera.position.z = 1500 + Math.sin(time * 0.1) * 200;
//     camera.lookAt(scene.position);

//     renderer.render(scene, camera);
// }


let scrollY = 0;
let targetZ = 1500; // Initial z position
const scrollSpeed = 0.05; // Controls how quickly the camera responds to scrolling

// Add scroll event listener
window.addEventListener('scroll', () => {
    // Calculate normalized scroll position (0 to 1)
    scrollY = window.scrollY / (document.body.scrollHeight - window.innerHeight);
});

function animate() {
    requestAnimationFrame(animate);
    
    const positions = grid.geometry.attributes.position.array;
    const time = Date.now() * 0.001;
    
    let i = 1; // y-coordinate index
    for (let ix = 0; ix < AMOUNTX; ix++) {
        for (let iy = 0; iy < AMOUNTY; iy++) {
            positions[i] = (Math.sin((ix + time) * 0.3) * 70) +
                          (Math.sin((iy + time) * 0.5) * 70);
            i += 3;
        }
    }

    grid.geometry.attributes.position.needsUpdate = true;
    
    // Calculate target Z position based on scroll (move forward when scrolling down)
    targetZ = 1500 - (scrollY * 1000); // Move 1000 units forward at full scroll
    
    // Smoothly interpolate current position toward target position
    camera.position.z += (targetZ - camera.position.z) * scrollSpeed;
    
    // Keep the original X position animation
    camera.position.x = Math.sin(time * 0.8) * 200;
    camera.lookAt(scene.position);
    
    renderer.render(scene, camera);
}


function updateRendererSize() {
    const container = document.getElementById('canvas');
    if (!container) return;
    
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    if (camera) {
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
    }
    
    renderer.setSize(width, height);
    
    // Recreate grid with appropriate density for device
    if (grid) {
        scene.remove(grid);
        createGrid();
    }
}

const onWindowResize = debounce(updateRendererSize, 250);

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

window.addEventListener('resize', onWindowResize);
window.addEventListener('orientationchange', onWindowResize);

document.addEventListener('DOMContentLoaded', () => {
    init();
    animate();
    ScrollReveal({ reset: false }).reveal(".event", {
        delay: 50,
        distance: "120%" ,
        origin: 'left',
        duration: 600
    });
});

function cleanup() {
    window.removeEventListener('resize', onWindowResize);
    renderer.dispose();
    scene.clear();
}