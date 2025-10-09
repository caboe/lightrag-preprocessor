// Configuration types
export interface Config {
  apiUrl: string
  apiKey: string
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

// Document processing types
export interface DocumentUploadResponse {
  success: boolean
  message: string
  document_id?: string
  content?: string
}

export interface TextInputRequest {
  content: string
  metadata?: Record<string, any>
}

export interface TextInputResponse {
  success: boolean
  message: string
  processed_content?: string
}

// Image processing types
export interface ImageProcessingResponse {
  success: boolean
  description: string
  analysis?: Record<string, any>
}

// YouTube types
export interface YouTubeRequest {
  url: string
  language?: string
}

export interface YouTubeResponse {
  success: boolean
  message: string
  transcript?: string
  metadata?: Record<string, any>
}

// Chat types
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string | ChatContent[]
}

export interface ChatContent {
  type: 'text' | 'image_url'
  text?: string
  image_url?: {
    url: string
    detail?: 'low' | 'high' | 'auto'
  }
}

export interface ChatCompletionRequest {
  model: string
  messages: ChatMessage[]
  temperature?: number
  max_tokens?: number
  stream?: boolean
}

export interface ChatRequest {
  messages: ChatMessage[]
  max_tokens?: number
  stream?: boolean
}

export interface ChatCompletionResponse {
  id: string
  object: string
  created: number
  model: string
  choices: ChatChoice[]
  usage?: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
}

export interface ChatChoice {
  index: number
  message: ChatMessage
  finish_reason: string
}

// File types
export interface FileUpload {
  file: File
  id: string
  progress: number
  status: 'pending' | 'uploading' | 'completed' | 'error'
  result?: any
  error?: string
}

// Health check types
export interface HealthStatus {
  status: 'healthy' | 'unhealthy'
  timestamp: string
  services: Record<string, any>
}

// Tab types
export type TabType = 'config' | 'upload' | 'text' | 'youtube' | 'chat'

export interface Tab {
  id: TabType
  label: string
  icon: string
  component: string
}