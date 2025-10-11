<template>
  <div class="p-4 space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h2 class="h3 font-bold">API Configuration</h2>
      <p class="text-surface-500 text-sm">Configure your LightRAG API connection</p>
    </div>

    <!-- Connection Status -->
    <div class="card p-4" :class="connectionStatusClass">
      <div class="flex items-center gap-3">
        <div class="w-3 h-3 rounded-full" :class="connectionIndicatorClass"></div>
        <span class="font-medium">{{ connectionStatusText }}</span>
      </div>
    </div>

    <!-- Configuration Form -->
    <form @submit.prevent="handleSave" class="space-y-4">
      <!-- API URL -->
      <div class="space-y-2">
        <label for="apiUrl" class="label">
          <span>API URL</span>
          <span class="text-error-500">*</span>
        </label>
        <input
          id="apiUrl"
          v-model="formData.apiUrl"
          type="url"
          class="input"
          :class="{ 'input-error': errors.apiUrl }"
          placeholder="http://localhost:8000"
          required
        />
        <div v-if="errors.apiUrl" class="text-error-500 text-sm">
          {{ errors.apiUrl }}
        </div>
      </div>

      <!-- API Key -->
      <div class="space-y-2">
        <label for="apiKey" class="label">
          <span>API Key</span>
          <span class="text-error-500">*</span>
        </label>
        <div class="relative">
          <input
            id="apiKey"
            v-model="formData.apiKey"
            :type="showApiKey ? 'text' : 'password'"
            class="input pr-10"
            :class="{ 'input-error': errors.apiKey }"
            placeholder="Enter your API key"
            required
          />
          <button
            type="button"
            @click="showApiKey = !showApiKey"
            class="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-surface-200 rounded"
          >
            <Eye v-if="!showApiKey" class="w-4 h-4" />
            <EyeOff v-else class="w-4 h-4" />
          </button>
        </div>
        <div v-if="errors.apiKey" class="text-error-500 text-sm">
          {{ errors.apiKey }}
        </div>
      </div>

      <!-- Chat API Key (Bearer for chat endpoints) -->
      <div class="space-y-2">
        <label for="chatApiKey" class="label">
          <span>Chat API Key</span>
          <span class="text-surface-400 text-xs">(used as Bearer for chat)</span>
        </label>
        <div class="relative">
          <input
            id="chatApiKey"
            v-model="formData.chatApiKey"
            :type="showChatApiKey ? 'text' : 'password'"
            class="input pr-10"
            placeholder="Optional: separate key for chat endpoints"
          />
          <button
            type="button"
            @click="showChatApiKey = !showChatApiKey"
            class="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-surface-200 rounded"
          >
            <Eye v-if="!showChatApiKey" class="w-4 h-4" />
            <EyeOff v-else class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex gap-3">
        <button
          type="button"
          @click="handleTest"
          :disabled="isLoading || !isFormValid"
          class="btn variant-outline-primary flex-1"
        >
          <div v-if="isLoading" class="flex items-center gap-2">
            <div class="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
            Testing...
          </div>
          <div v-else class="flex items-center gap-2">
            <Wifi class="w-4 h-4" />
            Test Connection
          </div>
        </button>
        
        <button
          type="submit"
          :disabled="isLoading || !isFormValid"
          class="btn variant-filled-primary flex-1"
        >
          <div v-if="isLoading" class="flex items-center gap-2">
            <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            Saving...
          </div>
          <div v-else class="flex items-center gap-2">
            <Save class="w-4 h-4" />
            Save Config
          </div>
        </button>
      </div>

      <!-- Reset Button -->
      <button
        type="button"
        @click="handleReset"
        class="btn variant-outline-error w-full"
      >
        <RotateCcw class="w-4 h-4 mr-2" />
        Reset to Defaults
      </button>
    </form>

    <!-- Help Section -->
    <div class="card p-4 bg-surface-100 dark:bg-surface-800">
      <h4 class="h4 mb-2">Quick Setup</h4>
      <ul class="list-disc list-inside space-y-1 text-sm text-surface-600 dark:text-surface-400">
        <li>Make sure your LightRAG API server is running</li>
        <li>Default URL is <code class="code">http://localhost:8000</code></li>
        <li>Get your API key from the server configuration</li>
        <li>Test the connection before saving</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Eye, EyeOff, Wifi, Save, RotateCcw } from 'lucide-vue-next'
import { useConfigStore } from '@/stores/config'
import { getApiClient } from '@/services/api'
import type { Config } from '@/types'

const configStore = useConfigStore()

// Form state
const formData = ref<Config>({
  apiUrl: '',
  apiKey: '',
  chatApiKey: ''
})

const showApiKey = ref(false)
const showChatApiKey = ref(false)
const isLoading = ref(false)
const errors = ref<Partial<Record<keyof Config, string>>>({})
const connectionStatus = ref<'unknown' | 'connected' | 'error'>('unknown')
const connectionMessage = ref('')

// Computed properties
const isFormValid = computed(() => {
  return formData.value.apiUrl.trim() !== '' && 
         formData.value.apiKey.trim() !== '' &&
         Object.keys(errors.value).length === 0
})

const connectionStatusClass = computed(() => {
  switch (connectionStatus.value) {
    case 'connected':
      return 'variant-outline-success'
    case 'error':
      return 'variant-outline-error'
    default:
      return 'variant-outline-surface'
  }
})

const connectionIndicatorClass = computed(() => {
  switch (connectionStatus.value) {
    case 'connected':
      return 'bg-success-500'
    case 'error':
      return 'bg-error-500'
    default:
      return 'bg-surface-400'
  }
})

const connectionStatusText = computed(() => {
  switch (connectionStatus.value) {
    case 'connected':
      return 'Connected to API'
    case 'error':
      return connectionMessage.value || 'Connection failed'
    default:
      return 'Connection status unknown'
  }
})

// Validation
const validateForm = () => {
  errors.value = {}
  
  if (!configStore.validateApiUrl(formData.value.apiUrl)) {
    errors.value.apiUrl = 'Please enter a valid URL'
  }
  
  if (!configStore.validateApiKey(formData.value.apiKey)) {
    errors.value.apiKey = 'API key is required'
  }
}

// Watch for form changes to validate
watch(formData, validateForm, { deep: true })

// Handlers
const handleTest = async () => {
  if (!isFormValid.value) return
  
  isLoading.value = true
  connectionStatus.value = 'unknown'
  
  try {
    const apiClient = getApiClient(formData.value)
    const result = await apiClient.testConnection()
    
    if (result.success) {
      connectionStatus.value = 'connected'
      connectionMessage.value = result.message
    } else {
      connectionStatus.value = 'error'
      connectionMessage.value = result.message
    }
  } catch (error) {
    connectionStatus.value = 'error'
    connectionMessage.value = error instanceof Error ? error.message : 'Connection failed'
  } finally {
    isLoading.value = false
  }
}

const handleSave = async () => {
  if (!isFormValid.value) return
  
  isLoading.value = true
  
  try {
    await configStore.updateConfig(formData.value)
    
    // Test connection after saving
    await handleTest()
  } catch (error) {
    console.error('Failed to save config:', error)
  } finally {
    isLoading.value = false
  }
}

const handleReset = async () => {
  if (confirm('Are you sure you want to reset to default settings?')) {
    await configStore.resetConfig()
    formData.value = { ...configStore.config }
    connectionStatus.value = 'unknown'
    connectionMessage.value = ''
  }
}

// Initialize
onMounted(async () => {
  await configStore.initialize()
  formData.value = { ...configStore.config }
  
  // Test connection if config is already set
  if (configStore.isConfigured) {
    await handleTest()
  }
})
</script>