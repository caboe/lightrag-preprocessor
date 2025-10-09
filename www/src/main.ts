import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'

const app = createApp(App)

// Add Pinia store
app.use(createPinia())

// Mount the app
app.mount('#app')
