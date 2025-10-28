<template>
  <div class="p-4 space-y-6 h-full overflow-y-auto">
    <!-- Header -->
    <div class="text-center">
      <h2 class="h3 font-bold">YouTube Processing</h2>
      <p class="text-surface-500 text-sm">Extract and process YouTube video transcripts</p>
    </div>

    <!-- Configuration Check -->
    <div v-if="!configStore.isConfigured" class="card p-4 variant-outline-warning">
      <div class="flex items-center gap-3">
        <AlertTriangle class="w-5 h-5 text-warning-500" />
        <span>Please configure your API settings first</span>
      </div>
    </div>

    <!-- YouTube URL Form -->
    <form @submit.prevent="handleSubmit" class="space-y-4">
      <!-- URL Input -->
      <div class="space-y-2">
        <label for="youtubeUrl" class="label">
          <span>YouTube URL</span>
          <span class="text-error-500">*</span>
        </label>
        <div class="relative">
          <input
            id="youtubeUrl"
            v-model="youtubeUrl"
            type="url"
            class="input pl-10"
            :class="{ 'input-error': error }"
            placeholder="https://www.youtube.com/watch?v=..."
            :disabled="!configStore.isConfigured || isLoading"
            required
          />
          <Youtube class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
        </div>
        <div v-if="error" class="text-error-500 text-sm">
          {{ error }}
        </div>
        <div class="text-xs text-surface-500">
          Supports YouTube video URLs and YouTube Shorts
        </div>
      </div>

      <!-- Language Selection -->
      <div class="space-y-2">
        <label for="language" class="label">Language (Optional)</label>
        <select
          id="language"
          v-model="selectedLanguage"
          class="select"
          :disabled="!configStore.isConfigured || isLoading"
        >
          <option value="">Auto-detect</option>
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="de">German</option>
          <option value="it">Italian</option>
          <option value="pt">Portuguese</option>
          <option value="ru">Russian</option>
          <option value="ja">Japanese</option>
          <option value="ko">Korean</option>
          <option value="zh">Chinese</option>
        </select>
        <div class="text-xs text-surface-500">
          Leave empty for automatic language detection
        </div>
      </div>

      <!-- Submit Button -->
      <button
        type="submit"
        :disabled="!configStore.isConfigured || isLoading || !isValidYouTubeUrl"
        class="btn variant-filled-primary w-full"
      >
        <div v-if="isLoading" class="flex items-center gap-2">
          <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          Processing...
        </div>
        <div v-else class="flex items-center gap-2">
          <Download class="w-4 h-4" />
          Extract Transcript
        </div>
      </button>
    </form>

    <!-- Quick Examples -->
    <div class="card p-4 bg-surface-100 dark:bg-surface-800">
      <h4 class="h4 mb-3">Example URLs</h4>
      <div class="space-y-2 text-sm">
        <div class="flex items-center gap-2">
          <button
            @click="setExampleUrl('https://www.youtube.com/watch?v=dQw4w9WgXcQ')"
            class="text-primary-600 hover:text-primary-700 underline"
            :disabled="isLoading"
          >
            Standard YouTube video
          </button>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="setExampleUrl('https://youtu.be/dQw4w9WgXcQ')"
            class="text-primary-600 hover:text-primary-700 underline"
            :disabled="isLoading"
          >
            Short YouTube URL
          </button>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="setExampleUrl('https://www.youtube.com/shorts/dQw4w9WgXcQ')"
            class="text-primary-600 hover:text-primary-700 underline"
            :disabled="isLoading"
          >
            YouTube Shorts
          </button>
        </div>
      </div>
    </div>

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
                {{ result.language || 'Auto' }}
              </div>
            </div>

            <!-- URL Display -->
            <div class="flex items-center gap-2 text-sm">
              <Youtube class="w-4 h-4 text-red-500" />
              <a
                :href="result.url"
                target="_blank"
                rel="noopener noreferrer"
                class="text-primary-600 hover:text-primary-700 underline truncate"
              >
                {{ result.url }}
              </a>
              <ExternalLink class="w-3 h-3 text-surface-400" />
            </div>

            <!-- Success Result -->
            <div v-if="result.success" class="space-y-3">
              <div class="flex items-center gap-2 text-success-600">
                <CheckCircle class="w-4 h-4" />
                <span class="text-sm font-medium">Transcript extracted successfully</span>
              </div>
              
              <!-- Metadata -->
              <div v-if="result.data?.metadata" class="bg-surface-100 dark:bg-surface-800 rounded p-3">
                <p class="text-sm font-medium mb-2">Video Information:</p>
                <div class="grid grid-cols-2 gap-2 text-xs">
                  <div v-if="result.data.metadata.title">
                    <span class="font-medium">Title:</span>
                    <span class="text-surface-600 dark:text-surface-400 ml-1">
                      {{ result.data.metadata.title }}
                    </span>
                  </div>
                  <div v-if="result.data.metadata.duration">
                    <span class="font-medium">Duration:</span>
                    <span class="text-surface-600 dark:text-surface-400 ml-1">
                      {{ result.data.metadata.duration }}
                    </span>
                  </div>
                  <div v-if="result.data.metadata.author">
                    <span class="font-medium">Channel:</span>
                    <span class="text-surface-600 dark:text-surface-400 ml-1">
                      {{ result.data.metadata.author }}
                    </span>
                  </div>
                  <div v-if="result.data.metadata.view_count">
                    <span class="font-medium">Views:</span>
                    <span class="text-surface-600 dark:text-surface-400 ml-1">
                      {{ formatNumber(result.data.metadata.view_count) }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Transcript -->
              <div v-if="result.data?.transcript" class="space-y-2">
                <div class="flex items-center justify-between">
                  <p class="text-sm font-medium">Transcript:</p>
                  <button
                    @click="copyTranscript(result.data.transcript)"
                    class="btn btn-sm variant-outline-surface"
                  >
                    <Copy class="w-3 h-3 mr-1" />
                    Copy
                  </button>
                </div>
                <div class="bg-surface-50 dark:bg-surface-900 rounded p-3 max-h-64 overflow-y-auto scrollbar-thin">
                  <p class="text-sm text-surface-700 dark:text-surface-300 whitespace-pre-wrap">
                    {{ result.data.transcript }}
                  </p>
                </div>
                <div class="text-xs text-surface-500">
                  {{ result.data.transcript.length }} characters
                </div>
              </div>
            </div>

            <!-- Error Result -->
            <div v-else class="space-y-2">
              <div class="flex items-center gap-2 text-error-600">
                <XCircle class="w-4 h-4" />
                <span class="text-sm font-medium">Extraction failed</span>
              </div>
              
              <div class="bg-error-50 dark:bg-error-900/20 rounded p-3">
                <p class="text-sm text-error-700 dark:text-error-300">
                  {{ result.error || 'Unknown error occurred' }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!isLoading" class="text-center py-8">
      <Youtube class="w-16 h-16 text-surface-300 mx-auto mb-4" />
      <p class="text-surface-500">No transcripts extracted yet</p>
      <p class="text-surface-400 text-sm">Enter a YouTube URL above to get started</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Youtube,
  Download,
  CheckCircle,
  XCircle,
  Trash2,
  AlertTriangle,
  ExternalLink,
  Copy
} from 'lucide-vue-next'
import { useConfigStore } from '@/stores/config'
import { getApiClient } from '@/services/api'
import type { YouTubeResponse } from '@/types'

const configStore = useConfigStore()

// Form state
const youtubeUrl = ref('')
const selectedLanguage = ref('')

// Processing state
const isLoading = ref(false)
const error = ref('')

// Results
interface ProcessingResult {
  timestamp: Date
  success: boolean
  url: string
  language?: string
  data?: YouTubeResponse
  error?: string
}

const results = ref<ProcessingResult[]>([])

// Computed
const isValidYouTubeUrl = computed(() => {
  if (!youtubeUrl.value.trim()) return false
  
  const url = youtubeUrl.value.trim()
  const patterns = [
    /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
    /^https?:\/\/(www\.)?youtube\.com\/shorts\/[\w-]+/,
    /^https?:\/\/youtu\.be\/[\w-]+/,
    /^https?:\/\/(www\.)?youtube\.com\/embed\/[\w-]+/
  ]
  
  return patterns.some(pattern => pattern.test(url))
})

// Utilities
const formatTimestamp = (timestamp: Date): string => {
  return timestamp.toLocaleString()
}

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const copyTranscript = async (transcript: string) => {
  try {
    await navigator.clipboard.writeText(transcript)
    // Could add a toast notification here
  } catch (err) {
    console.error('Failed to copy transcript:', err)
  }
}

// Handlers
const setExampleUrl = (url: string) => {
  youtubeUrl.value = url
  error.value = ''
}

const handleSubmit = async () => {
  if (!configStore.isConfigured || !isValidYouTubeUrl.value) return

  isLoading.value = true
  error.value = ''

  try {
    const apiClient = getApiClient(configStore.config)
    
    const request = {
      url: youtubeUrl.value.trim(),
      language: selectedLanguage.value || undefined
    }

    const result = await apiClient.processYouTube(request)

    // Add result to history
    results.value.unshift({
      timestamp: new Date(),
      success: result.success,
      url: youtubeUrl.value.trim(),
      language: selectedLanguage.value || undefined,
      data: result.success ? result.data : undefined,
      error: result.success ? undefined : result.error
    })

    // Clear form on success
    if (result.success) {
      youtubeUrl.value = ''
      selectedLanguage.value = ''
    } else {
      error.value = result.error || 'Processing failed'
    }

  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Processing failed'
    
    // Add error result to history
    results.value.unshift({
      timestamp: new Date(),
      success: false,
      url: youtubeUrl.value.trim(),
      language: selectedLanguage.value || undefined,
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