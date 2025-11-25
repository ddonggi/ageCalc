
// 3D Background with Three.js - Life Stream Concept

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('canvas-container');
    if (!container) return;

    // Scene Setup
    const scene = new THREE.Scene();
    // Soft fog for depth
    scene.fog = new THREE.FogExp2(0xffffff, 0.002);

    // Camera
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 5;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x667eea, 1.5); // Soft Blue
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);

    const pointLight2 = new THREE.PointLight(0x764ba2, 1.5); // Soft Purple
    pointLight2.position.set(-5, -5, 5);
    scene.add(pointLight2);

    // Geometry - Organic Blob (Icosahedron with noise)
    const geometry = new THREE.IcosahedronGeometry(2, 64); // High detail
    
    // Material - Glass-like / Iridescent
    const material = new THREE.MeshPhysicalMaterial({
        color: 0xffffff,
        roughness: 0.1,
        metalness: 0.1,
        transmission: 0.2, // Glass-like
        thickness: 1.0,
        clearcoat: 1.0,
        clearcoatRoughness: 0.1,
        side: THREE.DoubleSide
    });

    const blob = new THREE.Mesh(geometry, material);
    scene.add(blob);

    // Store original positions for noise animation
    const positionAttribute = geometry.attributes.position;
    const originalPositions = [];
    
    for (let i = 0; i < positionAttribute.count; i++) {
        originalPositions.push(
            positionAttribute.getX(i),
            positionAttribute.getY(i),
            positionAttribute.getZ(i)
        );
    }

    // Animation Variables
    let time = 0;
    const noiseScale = 0.5;
    const noiseSpeed = 0.002;
    const noiseStrength = 0.3;

    // Simple Perlin-like noise function (approximation for performance)
    function simpleNoise(x, y, z, time) {
        return Math.sin(x * noiseScale + time) * 
               Math.cos(y * noiseScale + time) * 
               Math.sin(z * noiseScale + time);
    }

    // Animation Loop
    function animate() {
        requestAnimationFrame(animate);

        time += 0.01;

        // Rotate Blob
        blob.rotation.x += 0.001;
        blob.rotation.y += 0.002;

        // Deform Geometry
        for (let i = 0; i < positionAttribute.count; i++) {
            const x = originalPositions[i * 3];
            const y = originalPositions[i * 3 + 1];
            const z = originalPositions[i * 3 + 2];

            // Calculate noise displacement
            const displacement = simpleNoise(x, y, z, time) * noiseStrength;
            
            // Apply displacement along normal (simplified as position vector for sphere)
            const factor = 1 + displacement;
            
            positionAttribute.setXYZ(i, x * factor, y * factor, z * factor);
        }
        
        positionAttribute.needsUpdate = true;
        geometry.computeVertexNormals(); // Recompute normals for correct lighting

        // Mouse Interaction (Parallax)
        const targetX = (mouseX - window.innerWidth / 2) * 0.001;
        const targetY = (mouseY - window.innerHeight / 2) * 0.001;
        
        blob.rotation.x += 0.05 * (targetY - blob.rotation.x);
        blob.rotation.y += 0.05 * (targetX - blob.rotation.y);

        renderer.render(scene, camera);
    }

    // Mouse Movement Tracking
    let mouseX = 0;
    let mouseY = 0;

    document.addEventListener('mousemove', (event) => {
        mouseX = event.clientX;
        mouseY = event.clientY;
    });

    // Resize Handler
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });

    animate();
});
