<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { 
  Settings, 
  Upload, 
  Type, 
  Youtube, 
  MessageCircle,
  Menu,
  X
} from 'lucide-vue-next'
import { useConfigStore } from '@/stores/config'
import ConfigTab from '@/components/ConfigTab.vue'
import FileUploadTab from '@/components/FileUploadTab.vue'
import TextInputTab from '@/components/TextInputTab.vue'
import YouTubeTab from '@/components/YouTubeTab.vue'
import ChatTab from '@/components/ChatTab.vue'

const configStore = useConfigStore()

// Tab management
const activeTab = ref('config')
const isMobileMenuOpen = ref(false)

const tabs = [
  {
    id: 'config',
    name: 'Config',
    icon: Settings,
    component: ConfigTab,
    description: 'API Settings'
  },
  {
    id: 'upload',
    name: 'Upload',
    icon: Upload,
    component: FileUploadTab,
    description: 'File Upload'
  },
  {
    id: 'text',
    name: 'Text',
    icon: Type,
    component: TextInputTab,
    description: 'Text Input'
  },
  {
    id: 'youtube',
    name: 'YouTube',
    icon: Youtube,
    component: YouTubeTab,
    description: 'YouTube Processing'
  },
  {
    id: 'chat',
    name: 'Chat',
    icon: MessageCircle,
    component: ChatTab,
    description: 'AI Chat'
  }
]

// Computed
const currentTab = computed(() => {
  return tabs.find(tab => tab.id === activeTab.value) || tabs[0]
})

const isExtensionMode = computed(() => {
  // Check if running as browser extension
  return typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.id
})

// Methods
const setActiveTab = (tabId: string) => {
  activeTab.value = tabId
  isMobileMenuOpen.value = false
}

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

// Lifecycle
onMounted(async () => {
  await configStore.initialize()
  
  // Auto-switch to upload tab if config is already set
  if (configStore.isConfigured && activeTab.value === 'config') {
    activeTab.value = 'upload'
  }
})
</script>

<template>
  <div class="h-screen flex flex-col bg-surface-50 dark:bg-surface-900">
    <!-- Header -->
    <header class="bg-white dark:bg-surface-800 border-b border-surface-200 dark:border-surface-700 px-4 py-3">
      <div class="flex items-center justify-between">
        <!-- Logo/Title -->
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
            <span class="text-white font-bold text-sm">LR</span>
          </div>
          <div>
            <h1 class="font-bold text-lg">LightRAG Preprocessor</h1>
            <p class="text-xs text-surface-500">
              {{ isExtensionMode ? 'Browser Extension' : 'Web Application' }}
            </p>
          </div>
        </div>

        <!-- Desktop Navigation -->
        <nav class="hidden md:flex items-center gap-1">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="setActiveTab(tab.id)"
            class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="
              activeTab === tab.id
                ? 'bg-primary-500 text-white'
                : 'text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-700'
            "
          >
            <component :is="tab.icon" class="w-4 h-4" />
            <span>{{ tab.name }}</span>
          </button>
        </nav>

        <!-- Mobile Menu Button -->
        <button
          @click="toggleMobileMenu"
          class="md:hidden p-2 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-700"
        >
          <Menu v-if="!isMobileMenuOpen" class="w-5 h-5" />
          <X v-else class="w-5 h-5" />
        </button>
      </div>

      <!-- Mobile Navigation -->
      <nav
        v-if="isMobileMenuOpen"
        class="md:hidden mt-3 pt-3 border-t border-surface-200 dark:border-surface-700"
      >
        <div class="grid grid-cols-2 gap-2">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="setActiveTab(tab.id)"
            class="flex items-center gap-2 p-3 rounded-lg text-sm font-medium transition-colors"
            :class="
              activeTab === tab.id
                ? 'bg-primary-500 text-white'
                : 'text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-700'
            "
          >
            <component :is="tab.icon" class="w-4 h-4" />
            <div class="text-left">
              <div>{{ tab.name }}</div>
              <div class="text-xs opacity-75">{{ tab.description }}</div>
            </div>
          </button>
        </div>
      </nav>
    </header>

    <!-- Main Content -->
    <main class="flex-1 overflow-hidden">
      <!-- Tab Content -->
      <div class="h-full">
        <component
          :is="currentTab?.component"
          :key="activeTab"
          class="h-full"
        />
      </div>
    </main>

    <!-- Status Bar (Extension Mode) -->
    <footer
      v-if="isExtensionMode"
      class="bg-surface-100 dark:bg-surface-800 border-t border-surface-200 dark:border-surface-700 px-4 py-2"
    >
      <div class="flex items-center justify-between text-xs">
        <div class="flex items-center gap-2">
          <div
            class="w-2 h-2 rounded-full"
            :class="configStore.isConfigured ? 'bg-success-500' : 'bg-warning-500'"
          ></div>
          <span class="text-surface-600 dark:text-surface-400">
            {{ configStore.isConfigured ? 'API Configured' : 'API Not Configured' }}
          </span>
        </div>
        <div class="text-surface-500">
          v1.0.0
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* Custom scrollbar for webkit browsers */
:deep(.scrollbar-thin) {
  scrollbar-width: thin;
  scrollbar-color: rgb(156 163 175) transparent;
}

:deep(.scrollbar-thin::-webkit-scrollbar) {
  width: 6px;
}

:deep(.scrollbar-thin::-webkit-scrollbar-track) {
  background: transparent;
}

:deep(.scrollbar-thin::-webkit-scrollbar-thumb) {
  background-color: rgb(156 163 175);
  border-radius: 3px;
}

:deep(.scrollbar-thin::-webkit-scrollbar-thumb:hover) {
  background-color: rgb(107 114 128);
}
</style>
