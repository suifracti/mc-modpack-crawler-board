import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
  root: __dirname,
  base: './',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: path.resolve(__dirname, '../../build/frontend_preview'),
    emptyOutDir: false, // Preserved so data/ and vendor/ sidecars remain available
    rollupOptions: {
      input: path.resolve(__dirname, 'index.html'),
      output: {
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name].[ext]',
      },
    },
    target: 'es2022',
    minify: false, // Keep readable during development/preview inspection
  },
  server: {
    port: 5173,
    open: false,
  },
});
