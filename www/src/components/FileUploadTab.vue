<template>
  <div class="p-4 space-y-6 h-full overflow-y-auto">
    <!-- Header -->
    <div class="text-center">
      <h2 class="h3 font-bold">File Upload</h2>
      <p class="text-surface-500 text-sm">Upload documents and images for processing</p>
    </div>

    <!-- Configuration Check -->
    <div v-if="!configStore.isConfigured" class="card p-4 variant-outline-warning">
      <div class="flex items-center gap-3">
        <AlertTriangle class="w-5 h-5 text-warning-500" />
        <span>Please configure your API settings first</span>
      </div>
    </div>

    <!-- Upload Area -->
    <div
      @drop="handleDrop"
      @dragover.prevent
      @dragenter.prevent
      @dragleave="handleDragLeave"
      :class="[
        'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
        isDragging ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' : 'border-surface-300 dark:border-surface-600',
        configStore.isConfigured ? 'cursor-pointer hover:border-primary-400' : 'cursor-not-allowed opacity-50'
      ]"
      @click="configStore.isConfigured && fileInput?.click()"
    >
      <input
        ref="fileInput"
        type="file"
        multiple
        :accept="acceptedFileTypes"
        @change="handleFileSelect"
        class="hidden"
        :disabled="!configStore.isConfigured"
      />
      
      <div class="space-y-4">
        <div class="flex justify-center">
          <Upload class="w-12 h-12 text-surface-400" />
        </div>
        
        <div>
          <p class="text-lg font-medium">
            {{ isDragging ? 'Drop files here' : 'Drag & drop files here' }}
          </p>
          <p class="text-surface-500 text-sm mt-1">
            or click to browse files
          </p>
        </div>
        
        <div class="text-xs text-surface-400">
          <p>Supported formats:</p>
          <p>Documents: PDF, TXT, MD, DOCX</p>
          <p>Images: JPG, PNG, WEBP</p>
          <p>Max size: 10MB per file</p>
        </div>
      </div>
    </div>

    <!-- File List -->
    <div v-if="files.length > 0" class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="h4">Files ({{ files.length }})</h3>
        <button
          @click="clearAllFiles"
          class="btn btn-sm variant-outline-error"
        >
          <Trash2 class="w-4 h-4 mr-1" />
          Clear All
        </button>
      </div>

      <div class="space-y-3">
        <div
          v-for="file in files"
          :key="file.id"
          class="card p-4"
        >
          <div class="flex items-center gap-4">
            <!-- File Icon -->
            <div class="flex-shrink-0">
              <FileText v-if="isDocument(file.file)" class="w-8 h-8 text-primary-500" />
              <Image v-else class="w-8 h-8 text-secondary-500" />
            </div>

            <!-- File Info -->
            <div class="flex-1 min-w-0">
              <p class="font-medium truncate">{{ file.file.name }}</p>
              <p class="text-sm text-surface-500">
                {{ formatFileSize(file.file.size) }} • {{ getFileType(file.file) }}
              </p>
              
              <!-- Progress Bar -->
              <div v-if="file.status === 'uploading'" class="mt-2">
                <div class="w-full bg-surface-200 rounded-full h-2">
                  <div
                    class="bg-primary-500 h-2 rounded-full transition-all duration-300"
                    :style="{ width: `${file.progress}%` }"
                  ></div>
                </div>
                <p class="text-xs text-surface-500 mt-1">{{ file.progress }}% uploaded</p>
              </div>

              <!-- Status Messages -->
              <div v-if="file.status === 'completed'" class="mt-2">
                <div class="flex items-center gap-2 text-success-600">
                  <CheckCircle class="w-4 h-4" />
                  <span class="text-sm">Upload completed</span>
                </div>
                <div v-if="file.result" class="mt-2 p-2 bg-surface-100 dark:bg-surface-800 rounded text-xs">
                  <p class="font-medium">Result:</p>
                  <p class="text-surface-600 dark:text-surface-400">{{ file.result.message }}</p>
                </div>
              </div>

              <div v-if="file.status === 'error'" class="mt-2">
                <div class="flex items-center gap-2 text-error-600">
                  <XCircle class="w-4 h-4" />
                  <span class="text-sm">{{ file.error || 'Upload failed' }}</span>
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex items-center gap-2">
              <button
                v-if="file.status === 'pending'"
                @click="uploadFile(file)"
                class="btn btn-sm variant-filled-primary"
                :disabled="!configStore.isConfigured"
              >
                <Upload class="w-4 h-4" />
              </button>
              
              <button
                v-if="file.status === 'uploading'"
                @click="cancelUpload(file)"
                class="btn btn-sm variant-outline-error"
              >
                <X class="w-4 h-4" />
              </button>
              
              <button
                @click="removeFile(file.id)"
                class="btn btn-sm variant-outline-surface"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Batch Actions -->
      <div v-if="pendingFiles.length > 0" class="flex gap-3">
        <button
          @click="uploadAllFiles"
          :disabled="!configStore.isConfigured"
          class="btn variant-filled-primary flex-1"
        >
          <Upload class="w-4 h-4 mr-2" />
          Upload All ({{ pendingFiles.length }})
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-8">
      <FileText class="w-16 h-16 text-surface-300 mx-auto mb-4" />
      <p class="text-surface-500">No files selected</p>
      <p class="text-surface-400 text-sm">Upload files to get started</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Upload,
  FileText,
  Image,
  Trash2,
  CheckCircle,
  XCircle,
  X,
  AlertTriangle
} from 'lucide-vue-next'
import { useConfigStore } from '@/stores/config'
import { getApiClient } from '@/services/api'
import type { FileUpload } from '@/types'

const configStore = useConfigStore()

// State
const files = ref<FileUpload[]>([])
const isDragging = ref(false)
const fileInput = ref<HTMLInputElement>()

// Constants
const acceptedFileTypes = '.pdf,.txt,.md,.docx,.jpg,.jpeg,.png,.webp'
const maxFileSize = 10 * 1024 * 1024 // 10MB

// Computed
const pendingFiles = computed(() => files.value.filter(f => f.status === 'pending'))

// Utilities
const generateId = () => Math.random().toString(36).substr(2, 9)

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getFileType = (file: File): string => {
  const extension = file.name.split('.').pop()?.toUpperCase()
  return extension || 'Unknown'
}

const isDocument = (file: File): boolean => {
  const documentTypes = ['pdf', 'txt', 'md', 'docx']
  const extension = file.name.split('.').pop()?.toLowerCase()
  return documentTypes.includes(extension || '')
}

const isValidFile = (file: File): { valid: boolean; error?: string } => {
  // Check file size
  if (file.size > maxFileSize) {
    return { valid: false, error: 'File size exceeds 10MB limit' }
  }

  // Check file type
  const extension = file.name.split('.').pop()?.toLowerCase()
  const allowedTypes = ['pdf', 'txt', 'md', 'docx', 'jpg', 'jpeg', 'png', 'webp']
  
  if (!extension || !allowedTypes.includes(extension)) {
    return { valid: false, error: 'Unsupported file type' }
  }

  return { valid: true }
}

// File handling
const addFiles = (fileList: FileList | File[]) => {
  const newFiles = Array.from(fileList).map(file => {
    const validation = isValidFile(file)
    
    return {
      id: generateId(),
      file,
      progress: 0,
      status: validation.valid ? 'pending' as const : 'error' as const,
      error: validation.error
    }
  })

  files.value.push(...newFiles)
}

const removeFile = (id: string) => {
  const index = files.value.findIndex(f => f.id === id)
  if (index > -1) {
    files.value.splice(index, 1)
  }
}

const clearAllFiles = () => {
  files.value = []
}

// Upload handling
const uploadFile = async (fileUpload: FileUpload) => {
  if (!configStore.isConfigured) return

  fileUpload.status = 'uploading'
  fileUpload.progress = 0

  try {
    const apiClient = getApiClient(configStore.config)
    
    // Simulate progress for better UX
    const progressInterval = setInterval(() => {
      if (fileUpload.progress < 90) {
        fileUpload.progress += Math.random() * 20
      }
    }, 200)

    let result
    if (isDocument(fileUpload.file)) {
      result = await apiClient.uploadDocument(fileUpload.file)
    } else {
      result = await apiClient.processImage(fileUpload.file)
    }

    clearInterval(progressInterval)
    fileUpload.progress = 100

    if (result.success) {
      fileUpload.status = 'completed'
      fileUpload.result = result.data
    } else {
      fileUpload.status = 'error'
      fileUpload.error = result.error || 'Upload failed'
    }
  } catch (error) {
    fileUpload.status = 'error'
    fileUpload.error = error instanceof Error ? error.message : 'Upload failed'
  }
}

const uploadAllFiles = async () => {
  const pending = pendingFiles.value
  for (const file of pending) {
    await uploadFile(file)
  }
}

const cancelUpload = (fileUpload: FileUpload) => {
  fileUpload.status = 'pending'
  fileUpload.progress = 0
}

// Drag and drop handlers
const handleDrop = (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = false

  if (!configStore.isConfigured) return

  const files = e.dataTransfer?.files
  if (files) {
    addFiles(files)
  }
}

const handleDragLeave = (e: DragEvent) => {
  // Only set isDragging to false if we're leaving the drop zone entirely
  const currentTarget = e.currentTarget as Element
  const relatedTarget = e.relatedTarget as Node
  if (!currentTarget?.contains(relatedTarget)) {
    isDragging.value = false
  }
}

// File input handler
const handleFileSelect = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files) {
    addFiles(target.files)
    target.value = '' // Reset input
  }
}

// Drag events
document.addEventListener('dragover', (e) => {
  e.preventDefault()
  isDragging.value = true
})

document.addEventListener('drop', (e) => {
  e.preventDefault()
  isDragging.value = false
})
</script>