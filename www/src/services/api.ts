import type {
  Config,
  ApiResponse,
  DocumentUploadResponse,
  TextInputRequest,
  TextInputResponse,
  ImageProcessingResponse,
  YouTubeRequest,
  YouTubeResponse,
  ChatCompletionRequest,
  ChatCompletionResponse,
  HealthStatus
} from '@/types'

export class ApiClient {
  private config: Config

  constructor(config: Config) {
    this.config = config
  }

  // Update configuration
  updateConfig(config: Config) {
    this.config = config
  }

  // Base fetch method with error handling
  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.config.apiUrl.replace(/\/$/, '')}${endpoint}`
      
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.config.apiKey,
          ...options.headers,
        },
      })

      if (!response.ok) {
        const errorText = await response.text()
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`
        
        try {
          const errorJson = JSON.parse(errorText)
          errorMessage = errorJson.detail || errorJson.message || errorMessage
        } catch {
          // If not JSON, use the text as error message
          errorMessage = errorText || errorMessage
        }
        
        return {
          success: false,
          error: errorMessage
        }
      }

      const data = await response.json()
      return {
        success: true,
        data
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error'
      }
    }
  }

  // Health check endpoint
  async healthCheck(): Promise<ApiResponse<HealthStatus>> {
    return this.fetch<HealthStatus>('/health')
  }

  // Document upload endpoint
  async uploadDocument(file: File): Promise<ApiResponse<DocumentUploadResponse>> {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const url = `${this.config.apiUrl.replace(/\/$/, '')}/documents/upload`
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'X-API-Key': this.config.apiKey,
        },
        body: formData,
      })

      if (!response.ok) {
        const errorText = await response.text()
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`
        
        try {
          const errorJson = JSON.parse(errorText)
          errorMessage = errorJson.detail || errorJson.message || errorMessage
        } catch {
          errorMessage = errorText || errorMessage
        }
        
        return {
          success: false,
          error: errorMessage
        }
      }

      const data = await response.json()
      return {
        success: true,
        data
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error'
      }
    }
  }

  // Text input endpoint
  async processText(request: TextInputRequest): Promise<ApiResponse<TextInputResponse>> {
    return this.fetch<TextInputResponse>('/documents/text', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  // Image processing endpoint
  async processImage(file: File): Promise<ApiResponse<ImageProcessingResponse>> {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const url = `${this.config.apiUrl.replace(/\/$/, '')}/images/process`
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
        },
        body: formData,
      })

      if (!response.ok) {
        const errorText = await response.text()
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`
        
        try {
          const errorJson = JSON.parse(errorText)
          errorMessage = errorJson.detail || errorJson.message || errorMessage
        } catch {
          errorMessage = errorText || errorMessage
        }
        
        return {
          success: false,
          error: errorMessage
        }
      }

      const data = await response.json()
      return {
        success: true,
        data
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error'
      }
    }
  }

  // YouTube processing endpoint
  async processYouTube(request: YouTubeRequest): Promise<ApiResponse<YouTubeResponse>> {
    return this.fetch<YouTubeResponse>('/youtube/process', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  // Chat completion endpoint
  async chatCompletion(request: ChatCompletionRequest): Promise<ApiResponse<ChatCompletionResponse>> {
    try {
      const url = `${this.config.apiUrl.replace(/\/$/, '')}/v1/chat/completions`

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.chatApiKey || this.config.apiKey}`,
        },
        body: JSON.stringify({ ...request, stream: false }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`

        try {
          const errorJson = JSON.parse(errorText)
          errorMessage = errorJson.detail || errorJson.message || errorMessage
        } catch {
          errorMessage = errorText || errorMessage
        }

        return {
          success: false,
          error: errorMessage
        }
      }

      const data = await response.json()
      return {
        success: true,
        data
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error'
      }
    }
  }

  // Streaming chat completion endpoint
  async chatCompletionStream(
    request: ChatCompletionRequest,
    onChunk: (chunk: string) => void,
    onError: (error: string) => void,
    onComplete: () => void
  ): Promise<void> {
    try {
      const url = `${this.config.apiUrl.replace(/\/$/, '')}/v1/chat/completions`
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.chatApiKey || this.config.apiKey}`,
        },
        body: JSON.stringify({ ...request, stream: true }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`
        
        try {
          const errorJson = JSON.parse(errorText)
          errorMessage = errorJson.detail || errorJson.message || errorMessage
        } catch {
          errorMessage = errorText || errorMessage
        }
        
        onError(errorMessage)
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        onError('Failed to get response reader')
        return
      }

      const decoder = new TextDecoder()
      
      try {
        while (true) {
          const { done, value } = await reader.read()
          
          if (done) {
            onComplete()
            break
          }

          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split('\n')
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim()
              
              if (data === '[DONE]') {
                onComplete()
                return
              }
              
              try {
                const parsed = JSON.parse(data)
                const content = parsed.choices?.[0]?.delta?.content
                if (content) {
                  onChunk(content)
                }
              } catch (e) {
                // Ignore parsing errors for individual chunks
              }
            }
          }
        }
      } finally {
        reader.releaseLock()
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Network error')
    }
  }

  // Test connection
  async testConnection(): Promise<{ success: boolean; message: string }> {
    try {
      const result = await this.healthCheck()
      if (result.success) {
        return {
          success: true,
          message: 'Connection successful'
        }
      } else {
        return {
          success: false,
          message: result.error || 'Connection failed'
        }
      }
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Connection failed'
      }
    }
  }
}

// Singleton instance
let apiClient: ApiClient | null = null

export const getApiClient = (config: Config): ApiClient => {
  if (!apiClient) {
    apiClient = new ApiClient(config)
  } else {
    apiClient.updateConfig(config)
  }
  return apiClient
}

export default ApiClient