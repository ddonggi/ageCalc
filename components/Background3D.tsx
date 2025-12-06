'use client';

import { Canvas, useFrame } from '@react-three/fiber';
import { useRef, useState, useMemo } from 'react';
import * as THREE from 'three';
import { Torus, Icosahedron, Octahedron, Dodecahedron, Sphere, Box } from '@react-three/drei';

const SHAPES = ['torus', 'icosahedron', 'octahedron', 'dodecahedron', 'sphere', 'box'] as const;
type ShapeType = typeof SHAPES[number];

function FloatingShape({ position, color, speed, shape = 'icosahedron', scale = 1 }: { position: [number, number, number], color: string, speed: number, shape?: ShapeType, scale?: number }) {
    const meshRef = useRef<THREE.Group>(null);
    const [hovered, setHover] = useState(false);

    useFrame((state, delta) => {
        if (meshRef.current) {
            meshRef.current.rotation.x += delta * speed * 0.5;
            meshRef.current.rotation.y += delta * speed * 0.3;
            // Gentle floating
            meshRef.current.position.y += Math.sin(state.clock.elapsedTime * speed * 0.5) * 0.005;
        }
    });

    const Material = (
        <meshPhysicalMaterial
            color={color}
            roughness={0.1}
            metalness={0.2}
            transmission={0.4}
            thickness={2}
            clearcoat={1}
            clearcoatRoughness={0.1}
            ior={1.5}
            reflectivity={0.5}
        />
    );

    return (
        <group
            ref={meshRef}
            position={position}
            onPointerOver={() => setHover(true)}
            onPointerOut={() => setHover(false)}
            scale={hovered ? scale * 1.2 : scale}
        >
            {shape === 'torus' && <Torus args={[0.8, 0.3, 32, 64]}>{Material}</Torus>}
            {shape === 'icosahedron' && <Icosahedron args={[1, 1]}>{Material}</Icosahedron>}
            {shape === 'octahedron' && <Octahedron args={[1, 0]}>{Material}</Octahedron>}
            {shape === 'dodecahedron' && <Dodecahedron args={[1, 0]}>{Material}</Dodecahedron>}
            {shape === 'sphere' && <Sphere args={[0.8, 64, 64]}>{Material}</Sphere>}
            {shape === 'box' && <Box args={[1.2, 1.2, 1.2]}>{Material}</Box>}
        </group>
    );
}

export function Background3D() {
    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            zIndex: -1,
            background: 'linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)' // Trendy pastel gradient
        }}>
            <Canvas camera={{ position: [0, 0, 15], fov: 45 }}>
                <ambientLight intensity={0.8} />
                <pointLight position={[10, 10, 10]} intensity={2} color="#ffffff" />
                <pointLight position={[-10, -10, -10]} intensity={1} color="#ff9ff3" />
                <spotLight position={[0, 10, 0]} angle={0.5} penumbra={1} intensity={1.5} castShadow />

                <FloatingShape position={[-9, 5, -6]} color="#a29bfe" speed={0.6} shape="torus" scale={1.5} />
                <FloatingShape position={[9, -5, -6]} color="#74b9ff" speed={0.9} shape="dodecahedron" scale={1.8} />
                <FloatingShape position={[0, 7, -9]} color="#ff7675" speed={0.5} shape="octahedron" scale={1.4} />
                <FloatingShape position={[-7, -7, -8]} color="#55efc4" speed={0.8} shape="box" scale={1.3} />
                <FloatingShape position={[7, 7, -5]} color="#dfe6e9" speed={0.3} shape="sphere" scale={1.2} />
                <FloatingShape position={[0, -9, -12]} color="#ffeaa7" speed={0.4} shape="icosahedron" scale={1.6} />
                <FloatingShape position={[-12, 0, -14]} color="#fd79a8" speed={0.6} shape="torus" scale={2.0} />
                <FloatingShape position={[12, 2, -10]} color="#00cec9" speed={0.7} shape="dodecahedron" scale={1.5} />

                {/* Small floating particles */}
                <FloatingShape position={[-3, 3, 2]} color="#fab1a0" speed={0.2} shape="sphere" scale={0.4} />
                <FloatingShape position={[3, -3, 3]} color="#81ecec" speed={0.3} shape="box" scale={0.3} />
            </Canvas>
        </div>
    );
}
