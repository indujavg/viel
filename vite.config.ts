import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VIEL_');
  return {
    server: {
      host: '127.0.0.1',
      proxy: {
        '/api': {
          target: env.VIEL_BACKEND_URL || 'http://127.0.0.1:8000',
          changeOrigin: true,
          rewrite: path => path.replace(/^\/api/, ''),
          headers: env.VIEL_API_TOKEN ? { Authorization: `Bearer ${env.VIEL_API_TOKEN}` } : {},
          timeout: 270000,
          proxyTimeout: 270000,
        },
      },
    },
  };
});
