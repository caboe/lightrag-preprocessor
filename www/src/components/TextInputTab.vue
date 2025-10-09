<template>
  <div class="p-4 space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h2 class="h3 font-bold">Text Processing</h2>
      <p class="text-surface-500 text-sm">Process text content directly with LightRAG</p>
    </div>

    <!-- Configuration Check -->
    <div v-if="!configStore.isConfigured" class="card p-4 variant-outline-warning">
      <div class="flex items-center gap-3">
        <AlertTriangle class="w-5 h-5 text-warning-500" />
        <span>Please configure your API settings first</span>
      </div>
    </div>

    <!-- Text Input Form -->
    <form @submit.prevent="handleSubmit" class="space-y-4">
      <!-- Text Area -->
      <div class="space-y-2">
        <label for="textContent" class="label">
          <span>Text Content</span>
          <span class="text-error-500">*</span>
        </label>
        <textarea
          id="textContent"
          v-model="textContent"
          class="textarea scrollbar-thin"
          :class="{ 'input-error': error }"
          placeholder="Enter your text content here..."
          rows="12"
          :disabled="!configStore.isConfigured || isLoading"
          required
        ></textarea>
        <div class="flex justify-between text-xs text-surface-500">
          <span v-if="error" class="text-error-500">{{ error }}</span>
          <span class="ml-auto">{{ textContent.length }} characters</span>
        </div>
      </div>

      <!-- Metadata (Optional) -->
      <details class="space-y-2">
        <summary class="cursor-pointer text-sm font-medium text-surface-600 hover:text-surface-800">
          Advanced Options (Optional)
        </summary>
        <div class="mt-3 space-y-3 pl-4 border-l-2 border-surface-200">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label for="title" class="label text-sm">Title</label>
              <input
                id="title"
                v-model="metadata.title"
                type="text"
                class="input input-sm"
                placeholder="Document title"
                :disabled="!configStore.isConfigured || isLoading"
              />
            </div>
            <div>
              <label for="author" class="label text-sm">Author</label>
              <input
                id="author"
                v-model="metadata.author"
                type="text"
                class="input input-sm"
                placeholder="Author name"
                :disabled="!configStore.isConfigured || isLoading"
              />
            </div>
          </div>
          <div>
            <label for="tags" class="label text-sm">Tags</label>
            <input
              id="tags"
              v-model="metadata.tags"
              type="text"
              class="input input-sm"
              placeholder="tag1, tag2, tag3"
              :disabled="!configStore.isConfigured || isLoading"
            />
            <p class="text-xs text-surface-500 mt-1">Separate tags with commas</p>
          </div>
        </div>
      </details>

      <!-- Submit Button -->
      <button
        type="submit"
        :disabled="!configStore.isConfigured || isLoading || !textContent.trim()"
        class="btn variant-filled-primary w-full"
      >
        <div v-if="isLoading" class="flex items-center gap-2">
          <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          Processing...
        </div>
        <div v-else class="flex items-center gap-2">
          <Send class="w-4 h-4" />
          Process Text
        </div>
      </button>
    </form>

    <!-- Results Section -->
    <div v-if="results.length > 0" class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="h4">Processing Results</h3>
        <button
          @click="clearResults"
          class="btn btn-sm variant-outline-surface"
        >
          <Trash2 class="w-4 h-4 mr-1" />
          Clear
        </button>
      </div>

      <div class="space-y-3">
        <div
          v-for="(result, index) in results"
          :key="index"
          class="card p-4"
        >
          <div class="space-y-3">
            <!-- Result Header -->
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full" :class="result.success ? 'bg-success-500' : 'bg-error-500'"></div>
                <span class="text-sm font-medium">
                  {{ formatTimestamp(result.timestamp) }}
                </span>
              </div>
              <div class="text-xs text-surface-500">
                {{ result.textLength }} characters
              </div>
            </div>

            <!-- Success Result -->
            <div v-if="result.success" class="space-y-2">
              <div class="flex items-center gap-2 text-success-600">
                <CheckCircle class="w-4 h-4" />
                <span class="text-sm font-medium">Processing completed</span>
              </div>
              
              <div class="bg-surface-100 dark:bg-surface-800 rounded p-3">
                <p class="text-sm font-medium mb-2">Response:</p>
                <p class="text-sm text-surface-700 dark:text-surface-300">
                  {{ result.data?.message || 'Text processed successfully' }}
                </p>
                
                <div v-if="result.data?.processed_content" class="mt-3">
                  <p class="text-sm font-medium mb-2">Processed Content:</p>
                  <div class="bg-surface-50 dark:bg-surface-900 rounded p-2 text-xs font-mono max-h-32 overflow-y-auto scrollbar-thin">
                    {{ result.data.processed_content }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Error Result -->
            <div v-else class="space-y-2">
              <div class="flex items-center gap-2 text-error-600">
                <XCircle class="w-4 h-4" />
                <span class="text-sm font-medium">Processing failed</span>
              </div>
              
              <div class="bg-error-50 dark:bg-error-900/20 rounded p-3">
                <p class="text-sm text-error-700 dark:text-error-300">
                  {{ result.error || 'Unknown error occurred' }}
                </p>
              </div>
            </div>

            <!-- Original Text Preview -->
            <details class="text-sm">
              <summary class="cursor-pointer text-surface-600 hover:text-surface-800">
                View original text
              </summary>
              <div class="mt-2 bg-surface-50 dark:bg-surface-900 rounded p-2 text-xs font-mono max-h-24 overflow-y-auto scrollbar-thin">
                {{ result.originalText }}
              </div>
            </details>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!isLoading" class="text-center py-8">
      <FileText class="w-16 h-16 text-surface-300 mx-auto mb-4" />
      <p class="text-surface-500">No processing results yet</p>
      <p class="text-surface-400 text-sm">Enter text above and click process to get started</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import {
  Send,
  FileText,
  CheckCircle,
  XCircle,
  Trash2,
  AlertTriangle
} from 'lucide-vue-next'
import { useConfigStore } from '@/stores/config'
import { getApiClient } from '@/services/api'
import type { TextInputResponse } from '@/types'

const configStore = useConfigStore()

// Form state
const textContent = ref('')
const metadata = reactive({
  title: '',
  author: '',
  tags: ''
})

// Processing state
const isLoading = ref(false)
const error = ref('')

// Results
interface ProcessingResult {
  timestamp: Date
  success: boolean
  originalText: string
  textLength: number
  data?: TextInputResponse
  error?: string
}

const results = ref<ProcessingResult[]>([])

// Utilities
const formatTimestamp = (timestamp: Date): string => {
  return timestamp.toLocaleString()
}

const parseMetadata = () => {
  const meta: Record<string, any> = {}
  
  if (metadata.title.trim()) {
    meta.title = metadata.title.trim()
  }
  
  if (metadata.author.trim()) {
    meta.author = metadata.author.trim()
  }
  
  if (metadata.tags.trim()) {
    meta.tags = metadata.tags.split(',').map(tag => tag.trim()).filter(Boolean)
  }
  
  return Object.keys(meta).length > 0 ? meta : undefined
}

// Handlers
const handleSubmit = async () => {
  if (!configStore.isConfigured || !textContent.value.trim()) return

  isLoading.value = true
  error.value = ''

  try {
    const apiClient = getApiClient(configStore.config)
    
    const request = {
      content: textContent.value.trim(),
      metadata: parseMetadata()
    }

    const result = await apiClient.processText(request)

    // Add result to history
    results.value.unshift({
      timestamp: new Date(),
      success: result.success,
      originalText: textContent.value.trim(),
      textLength: textContent.value.trim().length,
      data: result.success ? result.data : undefined,
      error: result.success ? undefined : result.error
    })

    // Clear form on success
    if (result.success) {
      textContent.value = ''
      metadata.title = ''
      metadata.author = ''
      metadata.tags = ''
    } else {
      error.value = result.error || 'Processing failed'
    }

  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Processing failed'
    
    // Add error result to history
    results.value.unshift({
      timestamp: new Date(),
      success: false,
      originalText: textContent.value.trim(),
      textLength: textContent.value.trim().length,
      error: error.value
    })
  } finally {
    isLoading.value = false
  }
}

const clearResults = () => {
  results.value = []
}
</script>