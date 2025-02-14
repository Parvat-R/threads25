let scene, camera, renderer, points;
let mouseX = 0, mouseY = 0;
let targetX = 0, targetY = 0;
let windowHalfX = window.innerWidth / 2;
let windowHalfY = window.innerHeight / 2;
let originalPositions = []; // Store original positions

function init() {
    // Scene setup
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    renderer = new THREE.WebGLRenderer({ alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.getElementById('canvas').appendChild(renderer.domElement);

    // Create particles
    const particles = 50000;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particles * 3);
    const colors = new Float32Array(particles * 3);

    const n = 1000, n2 = n / 2;
    for (let i = 0; i < positions.length; i += 3) {
        const x = Math.random() * n - n2;
        const y = Math.random() * n - n2;
        const z = Math.random() * n - n2;

        positions[i] = x;
        positions[i + 1] = y;
        positions[i + 2] = z;
        
        // Store original positions
        originalPositions.push(x, y, z);

        // Create gradient from pink to cyan
        const vx = (x / n) + 0.5;
        colors[i] = 1; // R (pink)
        colors[i + 1] = 0; // G
        colors[i + 2] = vx; // B (cyan)
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
        size: 2,
        vertexColors: true,
        blending: THREE.AdditiveBlending,
        transparent: true,
        opacity: 0.6
    });

    points = new THREE.Points(geometry, material);
    scene.add(points);

    camera.position.z = 750;

    // Add mouse event listeners
    document.addEventListener('mousemove', onDocumentMouseMove);
    document.addEventListener('touchstart', onDocumentTouchStart);
    document.addEventListener('touchmove', onDocumentTouchMove);
}

function onDocumentMouseMove(event) {
    mouseX = (event.clientX - windowHalfX) * 0.05;
    mouseY = (event.clientY - windowHalfY) * 0.05;
}

function onDocumentTouchStart(event) {
    if (event.touches.length === 1) {
        event.preventDefault();
        mouseX = event.touches[0].pageX - windowHalfX;
        mouseY = event.touches[0].pageY - windowHalfY;
    }
}

function onDocumentTouchMove(event) {
    if (event.touches.length === 1) {
        event.preventDefault();
        mouseX = event.touches[0].pageX - windowHalfX;
        mouseY = event.touches[0].pageY - windowHalfY;
    }
}

function animate() {
    requestAnimationFrame(animate);

    // Smooth camera movement
    targetX = mouseX * 0.5;
    targetY = mouseY * 0.5;
    camera.position.x += (targetX - camera.position.x) * 0.05;
    camera.position.y += (-targetY - camera.position.y) * 0.05;
    camera.lookAt(scene.position);

    const positions = points.geometry.attributes.position.array;
    const time = Date.now() * 0.0001;

    for (let i = 0; i < positions.length; i += 3) {
        const origX = originalPositions[i];
        const origY = originalPositions[i + 1];
        const origZ = originalPositions[i + 2];
        
        // Calculate current position using original wave pattern
        let newY = origY + Math.sin(time * 5 + origX * 0.005 + mouseX * 0.001) * 2;
        let newX = origX + Math.cos(time * 5 + origY * 0.005 + mouseY * 0.001) * 2;
        
        // Apply soft constraint to keep particles from drifting too far
        const maxDrift = 20;
        if (Math.abs(newX - origX) > maxDrift) {
            newX = origX + (Math.sign(newX - origX) * maxDrift);
        }
        if (Math.abs(newY - origY) > maxDrift) {
            newY = origY + (Math.sign(newY - origY) * maxDrift);
        }
        
        positions[i] = newX;
        positions[i + 1] = newY;
        positions[i + 2] = origZ;
    }

    points.geometry.attributes.position.needsUpdate = true;
    points.rotation.y += 0.001;

    renderer.render(scene, camera);
}

function onWindowResize() {
    windowHalfX = window.innerWidth / 2;
    windowHalfY = window.innerHeight / 2;
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

window.addEventListener('resize', onWindowResize, false);

init();
animate();