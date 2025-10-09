<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="p-4 border-b border-surface-300 dark:border-surface-700">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="h3 font-bold">Chat Interface</h2>
          <p class="text-surface-500 text-sm">OpenAI-compatible chat with multimodal support</p>
        </div>
        <button
          @click="clearChat"
          :disabled="messages.length === 0"
          class="btn btn-sm variant-outline-surface"
        >
          <Trash2 class="w-4 h-4 mr-1" />
          Clear
        </button>
      </div>
    </div>

    <!-- Configuration Check -->
    <div v-if="!configStore.isConfigured" class="p-4">
      <div class="card p-4 variant-outline-warning">
        <div class="flex items-center gap-3">
          <AlertTriangle class="w-5 h-5 text-warning-500" />
          <span>Please configure your API settings first</span>
        </div>
      </div>
    </div>

    <!-- Chat Messages -->
    <div
      ref="messagesContainer"
      class="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin"
    >
      <!-- Welcome Message -->
      <div v-if="messages.length === 0" class="text-center py-8">
        <MessageCircle class="w-16 h-16 text-surface-300 mx-auto mb-4" />
        <p class="text-surface-500">Start a conversation</p>
        <p class="text-surface-400 text-sm">Send text messages or upload images to chat</p>
      </div>

      <!-- Messages -->
      <div
        v-for="(message, index) in messages"
        :key="index"
        class="flex gap-3"
        :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <!-- Avatar -->
        <div
          v-if="message.role === 'assistant'"
          class="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center flex-shrink-0"
        >
          <Bot class="w-4 h-4 text-white" />
        </div>

        <!-- Message Content -->
        <div
          class="max-w-[80%] rounded-lg p-3"
          :class="
            message.role === 'user'
              ? 'bg-primary-500 text-white'
              : 'bg-surface-100 dark:bg-surface-800 text-surface-900 dark:text-surface-100'
          "
        >
          <!-- Text Content -->
          <div v-if="message.content" class="space-y-2">
            <div
              v-for="(content, contentIndex) in Array.isArray(message.content) ? message.content : [message.content]"
              :key="contentIndex"
            >
              <!-- Text -->
              <div v-if="typeof content === 'string' || content.type === 'text'" class="whitespace-pre-wrap">
                {{ typeof content === 'string' ? content : content.text }}
              </div>
              
              <!-- Image -->
              <div v-else-if="content.type === 'image_url' && content.image_url" class="space-y-2">
                <img
                  :src="content.image_url.url"
                  :alt="content.image_url.detail || 'Uploaded image'"
                  class="max-w-full h-auto rounded border"
                  style="max-height: 200px;"
                />
                <div v-if="content.image_url.detail" class="text-xs opacity-75">
                  Detail: {{ content.image_url.detail }}
                </div>
              </div>
            </div>
          </div>

          <!-- Timestamp -->
          <div
            class="text-xs mt-2 opacity-75"
            :class="message.role === 'user' ? 'text-white' : 'text-surface-500'"
          >
            {{ formatTimestamp(message.timestamp) }}
          </div>
        </div>

        <!-- User Avatar -->
        <div
          v-if="message.role === 'user'"
          class="w-8 h-8 rounded-full bg-surface-300 dark:bg-surface-700 flex items-center justify-center flex-shrink-0"
        >
          <User class="w-4 h-4 text-surface-600 dark:text-surface-400" />
        </div>
      </div>

      <!-- Loading Message -->
      <div v-if="isLoading" class="flex gap-3 justify-start">
        <div class="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center flex-shrink-0">
          <Bot class="w-4 h-4 text-white" />
        </div>
        <div class="bg-surface-100 dark:bg-surface-800 rounded-lg p-3">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 bg-primary-500 rounded-full animate-pulse"></div>
            <div class="w-2 h-2 bg-primary-500 rounded-full animate-pulse" style="animation-delay: 0.2s"></div>
            <div class="w-2 h-2 bg-primary-500 rounded-full animate-pulse" style="animation-delay: 0.4s"></div>
            <span class="text-sm text-surface-500 ml-2">Thinking...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="p-4 border-t border-surface-300 dark:border-surface-700">
      <!-- Image Preview -->
      <div v-if="selectedImages.length > 0" class="mb-3">
        <div class="flex items-center gap-2 mb-2">
          <ImageIcon class="w-4 h-4 text-surface-500" />
          <span class="text-sm font-medium">Selected Images</span>
          <button
            @click="clearImages"
            class="text-error-500 hover:text-error-600 text-sm"
          >
            Clear all
          </button>
        </div>
        <div class="flex gap-2 flex-wrap">
          <div
            v-for="(image, index) in selectedImages"
            :key="index"
            class="relative group"
          >
            <img
              :src="image.preview"
              :alt="image.file.name"
              class="w-16 h-16 object-cover rounded border"
            />
            <button
              @click="removeImage(index)"
              class="absolute -top-1 -right-1 w-5 h-5 bg-error-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <X class="w-3 h-3" />
            </button>
            <div class="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs p-1 rounded-b truncate">
              {{ image.file.name }}
            </div>
          </div>
        </div>
      </div>

      <!-- Input Form -->
      <form @submit.prevent="sendMessage" class="space-y-3">
        <!-- Message Input -->
        <div class="flex gap-2">
          <div class="flex-1 relative">
            <textarea
              v-model="messageText"
              ref="messageInput"
              placeholder="Type your message..."
              class="textarea resize-none pr-20"
              :class="{ 'textarea-error': error }"
              rows="1"
              :disabled="!configStore.isConfigured || isLoading"
              @keydown="handleKeydown"
              @input="adjustTextareaHeight"
            ></textarea>
            
            <!-- Input Actions -->
            <div class="absolute right-2 bottom-2 flex items-center gap-1">
              <!-- Image Upload -->
              <label class="btn btn-sm variant-ghost-surface p-1 cursor-pointer">
                <ImageIcon class="w-4 h-4" />
                <input
                  ref="imageInput"
                  type="file"
                  accept="image/*"
                  multiple
                  class="hidden"
                  @change="handleImageSelect"
                  :disabled="!configStore.isConfigured || isLoading"
                />
              </label>
              
              <!-- Send Button -->
              <button
                type="submit"
                :disabled="!canSendMessage"
                class="btn btn-sm variant-filled-primary p-1"
              >
                <Send class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- Error Display -->
        <div v-if="error" class="text-error-500 text-sm">
          {{ error }}
        </div>

        <!-- Chat Options -->
        <div class="flex items-center gap-4 text-sm">
          <label class="flex items-center gap-2">
            <input
              v-model="streamResponse"
              type="checkbox"
              class="checkbox"
              :disabled="!configStore.isConfigured || isLoading"
            />
            <span>Stream response</span>
          </label>
          
          <div class="flex items-center gap-2">
            <label for="maxTokens" class="text-surface-600 dark:text-surface-400">Max tokens:</label>
            <input
              id="maxTokens"
              v-model.number="maxTokens"
              type="number"
              min="1"
              max="4096"
              class="input w-20 text-sm"
              :disabled="!configStore.isConfigured || isLoading"
            />
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import {
  MessageCircle,
  Bot,
  User,
  Send,
  ImageIcon,
  X,
  Trash2,
  AlertTriangle
} from 'lucide-vue-next'
import { useConfigStore } from '@/stores/config'
import { getApiClient } from '@/services/api'
import type { ChatMessage, ChatCompletionRequest } from '@/types'

const configStore = useConfigStore()

// Refs
const messagesContainer = ref<HTMLElement>()
const messageInput = ref<HTMLTextAreaElement>()
const imageInput = ref<HTMLInputElement>()

// Chat state
const messages = ref<(ChatMessage & { timestamp: Date })[]>([])
const messageText = ref('')
const isLoading = ref(false)
const error = ref('')

// Chat options
const streamResponse = ref(true)
const maxTokens = ref(1000)

// Image handling
interface SelectedImage {
  file: File
  preview: string
  base64: string
}

const selectedImages = ref<SelectedImage[]>([])

// Computed
const canSendMessage = computed(() => {
  return (
    configStore.isConfigured &&
    !isLoading.value &&
    (messageText.value.trim() || selectedImages.value.length > 0)
  )
})

// Utilities
const formatTimestamp = (timestamp: Date): string => {
  return timestamp.toLocaleTimeString()
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const adjustTextareaHeight = () => {
  if (messageInput.value) {
    messageInput.value.style.height = 'auto'
    messageInput.value.style.height = Math.min(messageInput.value.scrollHeight, 120) + 'px'
  }
}

// Image handling
const handleImageSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  
  if (!files) return

  for (const file of Array.from(files)) {
    if (file.type.startsWith('image/')) {
      try {
        const preview = URL.createObjectURL(file)
        const base64 = await fileToBase64(file)
        
        selectedImages.value.push({
          file,
          preview,
          base64
        })
      } catch (err) {
        console.error('Error processing image:', err)
      }
    }
  }

  // Clear input
  target.value = ''
}

const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result
      if (result && typeof result === 'string') {
        const base64Data = result.split(',')[1]
        if (base64Data) {
          resolve(base64Data) // Remove data:image/...;base64, prefix
        } else {
          reject(new Error('Invalid file format'))
        }
      } else {
        reject(new Error('Failed to read file'))
      }
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

const removeImage = (index: number) => {
  const image = selectedImages.value[index]
  if (image) {
    URL.revokeObjectURL(image.preview)
    selectedImages.value.splice(index, 1)
  }
}

const clearImages = () => {
  selectedImages.value.forEach(image => {
    URL.revokeObjectURL(image.preview)
  })
  selectedImages.value = []
}

// Message handling
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

const sendMessage = async () => {
  if (!canSendMessage.value) return

  const text = messageText.value.trim()
  const images = [...selectedImages.value]

  // Clear input
  messageText.value = ''
  clearImages()
  adjustTextareaHeight()

  // Create message content
  const content: any[] = []
  
  if (text) {
    content.push({ type: 'text', text })
  }
  
  for (const image of images) {
    content.push({
      type: 'image_url',
      image_url: {
        url: `data:${image.file.type};base64,${image.base64}`,
        detail: 'auto'
      }
    })
  }

  // Add user message
  const userMessage: ChatMessage & { timestamp: Date } = {
    role: 'user',
    content: content.length === 1 && content[0].type === 'text' ? content[0].text : content,
    timestamp: new Date()
  }

  messages.value.push(userMessage)
  await scrollToBottom()

  // Send to API
  isLoading.value = true
  error.value = ''

  try {
    const apiClient = getApiClient(configStore.config)
    
    const request: ChatCompletionRequest = {
      model: 'gpt-3.5-turbo',
      messages: messages.value.map(msg => ({
        role: msg.role,
        content: msg.content
      })),
      max_tokens: maxTokens.value,
      stream: streamResponse.value
    }

    if (streamResponse.value) {
      // Handle streaming response
      const assistantMessage: ChatMessage & { timestamp: Date } = {
        role: 'assistant',
        content: '',
        timestamp: new Date()
      }
      
      messages.value.push(assistantMessage)
      await scrollToBottom()

      await apiClient.chatCompletionStream(
        request, 
        (chunk: string) => {
          assistantMessage.content += chunk
          scrollToBottom()
        },
        (error: string) => {
          throw new Error(error)
        },
        () => {
          // Stream complete
        }
      )
    } else {
      // Handle regular response
      const response = await apiClient.chatCompletion(request)
      
      if (response.success && response.data?.choices?.[0]?.message) {
        const assistantMessage: ChatMessage & { timestamp: Date } = {
          role: 'assistant',
          content: response.data.choices[0].message.content || '',
          timestamp: new Date()
        }
        
        messages.value.push(assistantMessage)
        await scrollToBottom()
      } else {
        throw new Error(response.error || 'Failed to get response')
      }
    }

  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to send message'
    console.error('Chat error:', err)
  } finally {
    isLoading.value = false
  }
}

const clearChat = () => {
  messages.value = []
  clearImages()
  error.value = ''
}

// Lifecycle
onMounted(() => {
  adjustTextareaHeight()
})
</script>

<style scoped>
.scrollbar-thin {
  scrollbar-width: thin;
  scrollbar-color: rgb(156 163 175) transparent;
}

.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: rgb(156 163 175);
  border-radius: 3px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background-color: rgb(107 114 128);
}
</style>