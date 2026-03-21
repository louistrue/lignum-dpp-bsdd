import { defineConfig } from 'vite';
import { readFileSync } from 'fs';

export default defineConfig({
  root: '.',
  base: '/enrich/',
  build: {
    outDir: '../api/static/enrich',
    emptyOutDir: true,
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
