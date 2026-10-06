import { defineConfig } from 'vite';
import path from 'node:path';
export default defineConfig({
  root: __dirname, base: './', publicDir: false,
  build: {
    outDir: process.env.MC_PAGES_OUT || path.resolve(__dirname, '../../build/pages'),
    emptyOutDir: false, target: 'es2022',
    manifest: true, assetsInlineLimit: 0,
    rollupOptions: { input: path.resolve(__dirname, 'pages.html') },
  },
});
