import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { viteStaticCopy } from 'vite-plugin-static-copy'

// https://vite.dev/config/
export default defineConfig(() => {
  const isExtension = process.env.BUILD_TARGET === 'extension'
  
  const plugins = [vue()]
  
  if (isExtension) {
    plugins.push(
      viteStaticCopy({
        targets: [
          {
            src: 'manifest.json',
            dest: '.'
          },
          {
            src: 'background.js',
            dest: '.'
          },
          {
            src: 'public/icons',
            dest: '.'
          }
        ]
      }) as any
    )
  }
  
  return {
    plugins,
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      },
    },
    build: {
      rollupOptions: {
        input: {
          main: resolve(__dirname, 'index.html'),
          popup: resolve(__dirname, 'popup.html'),
        },
        output: {
          entryFileNames: (chunkInfo) => {
            // Keep main entry as main.js for popup.html
            if (chunkInfo.name === 'popup') {
              return 'main.js'
            }
            return '[name]-[hash].js'
          },
        },
      },
    },
    define: {
      // Define global constants for extension detection
      __IS_EXTENSION__: JSON.stringify(isExtension),
    },
    server: {
      port: 3000,
      host: true,
    },
  }
})
