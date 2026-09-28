import { defineConfig } from 'vite';
import path from 'node:path';

export default defineConfig({
  root: __dirname,
  base: './',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: path.resolve(__dirname, '../../build/desktop-v2/frontend'),
    emptyOutDir: true,
    rollupOptions: {
      input: path.resolve(__dirname, 'desktop-v2.html'),
      output: {
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
    },
    target: 'es2022',
    minify: false,
  },
});
