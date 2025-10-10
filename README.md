# LightRAG Preprocessing API

A FastAPI-based preprocessing service for LightRAG knowledge graphs that handles document upload, text processing, image analysis, and YouTube transcript extraction.

## Features

- **Document Processing**: Upload and index PDF, TXT, MD, and DOCX files
- **Text Processing**: Direct text input and indexing
- **Image Analysis**: Multimodal image description using OpenAI Vision models
- **YouTube Integration**: Automatic transcript extraction and processing
- **OpenAI-Compatible API**: Chat completions endpoint for LLM interactions
- **Knowledge Graph Querying**: Query indexed content through LightRAG
- **Health Monitoring**: Comprehensive health checks and service monitoring
- **Security**: API key authentication and CORS support
- **Structured Logging**: JSON-formatted logs with correlation IDs

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- LightRAG instance running
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd preprocessor
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t preprocessor .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 --env-file .env preprocessor
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `LIGHTRAG_BASE_URL` | LightRAG API URL | Required |
| `LIGHTRAG_API_KEY` | LightRAG API key | Required |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | OpenAI model for vision | `gpt-4-vision-preview` |
| `API_KEY` | API authentication key | Required |
| `SECRET_KEY` | Application secret key | Required |
| `MAX_FILE_SIZE` | Maximum file size (bytes) | `52428800` (50MB) |
| `MAX_IMAGE_SIZE` | Maximum image size (bytes) | `10485760` (10MB) |
| `ALLOWED_FILE_TYPES` | Allowed file extensions | `.pdf,.txt,.md,.docx` |
| `ALLOWED_IMAGE_TYPES` | Allowed image extensions | `.jpg,.jpeg,.png,.webp` |
| `YOUTUBE_LANGUAGES` | Preferred transcript languages | `de,en` |
| `LOG_LEVEL` | Logging level | `INFO` |

## API Endpoints

### Authentication

All endpoints require Bearer token authentication:
```bash
Authorization: Bearer YOUR_API_KEY
```

### Document Processing

#### Upload Document
```http
POST /documents/upload
Content-Type: multipart/form-data

file: <document-file>
```

#### Process Text
```http
POST /documents/text
Content-Type: application/json

{
  "text": "Your text content here",
  "title": "Optional title"
}
```

#### Process Image
```http
POST /images/process
Content-Type: multipart/form-data

file: <image-file>
```

#### Process YouTube Video
```http
POST /youtube/process
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "language": "de"
}
```

### Chat Completions

#### OpenAI-Compatible Chat
```http
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "lightrag-proxy",
  "messages": [
    {
      "role": "user",
      "content": "Your message here"
    }
  ],
  "stream": false
}
```

### Knowledge Graph

#### Query Knowledge Graph
```http
POST /query
Content-Type: application/x-www-form-urlencoded

query=Your search query&max_results=10
```

### Health Checks

#### Basic Health Check
```http
GET /health
```

#### Detailed Health Check
```http
GET /health/detailed
Authorization: Bearer YOUR_API_KEY
```

## Response Formats

### Success Response
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "timestamp": "2024-01-01T12:00:00Z",
  "document_id": "uuid-here",
  "processing_time": 1.23
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description",
  "timestamp": "2024-01-01T12:00:00Z",
  "error": {
    "code": "ERROR_CODE",
    "details": {}
  }
}
```

## Development

### Project Structure
```
preprocessor/
├── app/
│   ├── api/                 # API route handlers
│   ├── core/               # Core application logic
│   ├── models/             # Pydantic models
│   │   ├── base.py         # Base response models
│   │   ├── chat.py         # Chat completion models
│   │   └── documents.py    # Document processing models
│   ├── services/           # Business logic services
│   │   ├── openai_service.py    # OpenAI integration
│   │   ├── lightrag_service.py  # LightRAG integration
│   │   └── youtube_service.py   # YouTube processing
│   └── utils/              # Utility functions
├── config/
│   └── settings.py         # Configuration management
├── tests/                  # Test files
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
└── .env.example           # Environment template
```

### Running Tests
```bash
pytest
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Monitoring and Logging

### Structured Logging
The application uses structured JSON logging with the following fields:
- `timestamp`: ISO format timestamp
- `level`: Log level (INFO, WARNING, ERROR)
- `logger`: Logger name
- `message`: Log message
- `request_id`: Correlation ID for request tracking
- Additional context fields

### Health Monitoring
- Basic health check at `/health`
- Detailed service status at `/health/detailed`
- Docker health check included
- External service dependency monitoring

### Metrics
The application exposes metrics for:
- Request processing times
- File upload sizes
- Error rates
- Service availability

## Security

### Authentication
- Bearer token authentication required for all endpoints
- API key validation on each request
- Secure headers and CORS configuration

### File Validation
- File type validation based on extensions
- File size limits enforced
- Content type verification
- Malicious file detection

### Rate Limiting
- Configurable rate limits per API key
- Protection against abuse and DoS attacks

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   - Verify API key is valid
   - Check rate limits and quotas
   - Ensure model availability

2. **LightRAG Connection Issues**
   - Verify LightRAG service is running
   - Check network connectivity
   - Validate API key and URL

3. **YouTube Processing Failures**
   - Verify video is publicly accessible
   - Check if transcripts are available
   - Ensure language is supported

4. **File Upload Issues**
   - Check file size limits
   - Verify file type is allowed
   - Ensure proper encoding

### Logs and Debugging
- Enable debug mode with `DEBUG=true`
- Check application logs for detailed error information
- Use health check endpoints to verify service status

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting guide