const ShareCodec = (() => {
    const encoder = new TextEncoder();
    const decoder = new TextDecoder();

    const toBase64Url = (bytes) => {
        let binary = '';
        bytes.forEach((b) => { binary += String.fromCharCode(b); });
        return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
    };

    const fromBase64Url = (str) => {
        const pad = str.length % 4 ? '='.repeat(4 - (str.length % 4)) : '';
        const base64 = str.replace(/-/g, '+').replace(/_/g, '/') + pad;
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
        return bytes;
    };

    const compress = async (bytes) => {
        if (!('CompressionStream' in window)) return bytes;
        const cs = new CompressionStream('gzip');
        const stream = new Blob([bytes]).stream().pipeThrough(cs);
        const buf = await new Response(stream).arrayBuffer();
        return new Uint8Array(buf);
    };

    const decompress = async (bytes) => {
        if (!('DecompressionStream' in window)) return bytes;
        try {
            const ds = new DecompressionStream('gzip');
            const stream = new Blob([bytes]).stream().pipeThrough(ds);
            const buf = await new Response(stream).arrayBuffer();
            return new Uint8Array(buf);
        } catch {
            return bytes;
        }
    };

    return {
        async encode(obj) {
            const json = JSON.stringify(obj);
            const raw = encoder.encode(json);
            const compressed = await compress(raw);
            return toBase64Url(compressed);
        },
        async decode(str) {
            const bytes = fromBase64Url(str);
            const raw = await decompress(bytes);
            return JSON.parse(decoder.decode(raw));
        }
    };
})();
