'use client';

import dynamic from 'next/dynamic';

const Background3D = dynamic(() => import('./Background3D').then(mod => mod.Background3D), {
    ssr: false
});

export function Background3DWrapper() {
    return <Background3D />;
}
