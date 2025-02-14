let scene, camera, renderer, points;

function init() {
    // Scene setup
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    renderer = new THREE.WebGLRenderer();
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);

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

        const vx = (x / n) + 0.5;
        const vy = (y / n) + 0.5;
        const vz = (z / n) + 0.5;

        colors[i] = vx;
        colors[i + 1] = vy;
        colors[i + 2] = vz;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
        size: 2,
        vertexColors: true,
        blending: THREE.AdditiveBlending,
        transparent: true,
        opacity: 0.5
    });

    points = new THREE.Points(geometry, material);
    scene.add(points);

    camera.position.z = 750;
}

function animate() {
    requestAnimationFrame(animate);

    const positions = points.geometry.attributes.position.array;
    const time = Date.now() * 0.001;

    for (let i = 0; i < positions.length; i += 3) {
        const x = positions[i];
        const y = positions[i + 1];
        const z = positions[i + 2];

        positions[i + 1] = y + Math.sin(time + x * 0.005) * 0.5;
    }

    points.geometry.attributes.position.needsUpdate = true;
    renderer.render(scene, camera);
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

window.addEventListener('resize', onWindowResize, false);

init();
animate();