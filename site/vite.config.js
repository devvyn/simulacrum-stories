import { defineConfig } from 'vite';
import { resolve } from 'path';
import { readdirSync } from 'fs';

// Discover all HTML files in read/ directory
function getReadPages() {
  const readDir = resolve(__dirname, 'read');
  try {
    const files = readdirSync(readDir).filter(f => f.endsWith('.html'));
    const entries = {};

    files.forEach(file => {
      const name = file.replace('.html', '');
      entries[`read/${name}`] = resolve(readDir, file);
    });

    return entries;
  } catch (e) {
    console.warn('Could not read read/ directory:', e.message);
    return {};
  }
}

export default defineConfig({
  root: '.',
  publicDir: 'public',

  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        ...getReadPages()
      }
    },
    // Keep readable output for debugging
    minify: 'esbuild',
    sourcemap: true
  },

  server: {
    port: 3000,
    open: true,
    // Proxy Netlify Functions during dev
    proxy: {
      '/.netlify/functions': {
        target: 'http://localhost:8888',
        changeOrigin: true
      }
    }
  },

  preview: {
    port: 4173
  },

  // Resolve aliases for cleaner imports
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  }
});
