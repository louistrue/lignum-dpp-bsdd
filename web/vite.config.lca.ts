import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  root: '.',
  base: '/emissions/',
  build: {
    outDir: '../public/emissions',
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, 'lca.html'),
    },
  },
});
