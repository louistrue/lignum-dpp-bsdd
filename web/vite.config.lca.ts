import { defineConfig } from 'vite';
import { resolve } from 'path';
import { readFileSync } from 'fs';

export default defineConfig({
  root: '.',
  base: '/emissions/',
  build: {
    outDir: '../api/static/emissions',
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, 'lca.html'),
    },
  },
  plugins: [{
    name: 'jsonld-loader',
    transform(_code, id) {
      if (id.endsWith('.jsonld')) {
        const json = readFileSync(id, 'utf-8');
        return { code: `export default ${json}`, map: null };
      }
    },
  }],
});
