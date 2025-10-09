import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Config } from '@/types'

const STORAGE_KEY = 'lightrag-config'
const DEFAULT_CONFIG: Config = {
  apiUrl: 'http://localhost:8000',
  apiKey: ''
}

// Storage utility functions
const isExtension = () => {
  return typeof chrome !== 'undefined' && chrome.storage
}

const saveToStorage = async (config: Config) => {
  try {
    if (isExtension()) {
      // Use chrome.storage for browser extension
      await chrome.storage.local.set({ [STORAGE_KEY]: config })
    } else {
      // Use localStorage for web app
      localStorage.setItem(STORAGE_KEY, JSON.stringify(config))
    }
  } catch (error) {
    console.error('Failed to save config to storage:', error)
  }
}

const loadFromStorage = async (): Promise<Config> => {
  try {
    if (isExtension()) {
      // Use chrome.storage for browser extension
      const result = await chrome.storage.local.get(STORAGE_KEY)
      return result[STORAGE_KEY] || DEFAULT_CONFIG
    } else {
      // Use localStorage for web app
      const stored = localStorage.getItem(STORAGE_KEY)
      return stored ? JSON.parse(stored) : DEFAULT_CONFIG
    }
  } catch (error) {
    console.error('Failed to load config from storage:', error)
    return DEFAULT_CONFIG
  }
}

export const useConfigStore = defineStore('config', () => {
  const config = ref<Config>({ ...DEFAULT_CONFIG })
  const isLoading = ref(false)
  const isConfigured = computed(() => {
    return config.value.apiUrl.trim() !== '' && config.value.apiKey.trim() !== ''
  })

  // Initialize store with saved config
  const initialize = async () => {
    isLoading.value = true
    try {
      const savedConfig = await loadFromStorage()
      config.value = { ...savedConfig }
    } catch (error) {
      console.error('Failed to initialize config store:', error)
    } finally {
      isLoading.value = false
    }
  }

  // Update configuration
  const updateConfig = async (newConfig: Partial<Config>) => {
    const updatedConfig = { ...config.value, ...newConfig }
    config.value = updatedConfig
    await saveToStorage(updatedConfig)
  }

  // Reset configuration
  const resetConfig = async () => {
    config.value = { ...DEFAULT_CONFIG }
    await saveToStorage(config.value)
  }

  // Validate API URL format
  const validateApiUrl = (url: string): boolean => {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  }

  // Validate API key format (basic check)
  const validateApiKey = (key: string): boolean => {
    return key.trim().length > 0
  }

  // Validate entire configuration
  const validateConfig = (configToValidate: Config): { valid: boolean; errors: string[] } => {
    const errors: string[] = []
    
    if (!validateApiUrl(configToValidate.apiUrl)) {
      errors.push('Invalid API URL format')
    }
    
    if (!validateApiKey(configToValidate.apiKey)) {
      errors.push('API key is required')
    }
    
    return {
      valid: errors.length === 0,
      errors
    }
  }

  return {
    config: computed(() => config.value),
    isLoading: computed(() => isLoading.value),
    isConfigured,
    initialize,
    updateConfig,
    resetConfig,
    validateApiUrl,
    validateApiKey,
    validateConfig
  }
})