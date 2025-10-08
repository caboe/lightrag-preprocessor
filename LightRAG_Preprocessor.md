# Requirements Document: Preprocessing API for LightRAG

**Version:** 1.0  
**Date:** May 24, 2024  
**Author:** [Your Name/Organization]

---

## 1. Project Overview

This project aims to develop a stateless Preprocessing API (acting as a "Gateway" or "Middleware" service) that serves as an interface between various user inputs and a LightRAG backend. The goal is to extend the capabilities of LightRAG by supporting additional data sources and formats (images, YouTube videos) and to provide a unified, OpenAI-compatible chat interface.

## 2. Objectives

*   **Centralization:** Consolidate all data preparation processes into a single service.
*   **Extending Capabilities:** Enable the indexing of images and video transcripts within LightRAG.
*   **Standardization:** Provide an OpenAI-compatible chat API to simplify integration with existing frontends.
*   **Decoupling:** Separate the data preparation logic from the core LightRAG system.

## 3. Architecture & Technologies

*   **Main Service:** A web API that exposes the endpoints described below.
*   **Recommended Technology Stack:** Python with a framework like `FastAPI` or `Flask`, due to its strong integration with the Python ecosystem for AI/ML.
*   **Dependencies:**
    *   A running **LightRAG system** with a defined API for document indexing and querying.
    *   Access to a **Multimodal LLM** (e.g., OpenAI GPT-4V, Google Gemini Pro Vision) via its API for image description.
    *   A library for **extracting YouTube captions** (e.g., `youtube-transcript-api`).
    *   A library for **processing PDF files** (e.g., `PyMuPDF`), should advanced image processing be desired in the future.

---

## 4. Functional Requirements

### 4.1. Document Upload

*   **Endpoint:** `POST /api/documents/upload`
*   **Description:** Accepts a file from the user and forwards it to the LightRAG system for indexing.
*   **Input:** `multipart/form-data` with a field named `file`.
    *   Supported file types: `.pdf`, `.txt`, `.md`, `.docx` (etc.).
*   **Processing Logic:**
    1.  Validate the uploaded file (type, size).
    2.  Send the file to the LightRAG indexing endpoint.
    3.  **Note:** For PDFs, embedded images are ignored in this basic version. The logic should be as simple as possible.
    4.  Return the response from LightRAG to the client.
*   **Success Response:** `200 OK` with a JSON body, e.g., `{ "status": "success", "document_id": "xyz123" }`.
*   **Error Handling:** `400 Bad Request` for invalid files, `500 Internal Server Error` for issues with LightRAG communication.

### 4.2. Text Input

*   **Endpoint:** `POST /api/documents/text`
*   **Description:** Accepts a plain text string, creates a temporary document, and indexes it in LightRAG.
*   **Input:** JSON body, e.g., `{ "text": "This is a sample text to be indexed." }`.
*   **Processing Logic:**
    1.  Receive the text string.
    2.  (Optional) Create a `.txt` file in memory or pass the text directly to LightRAG if its API supports it.
    3.  Send the text/document to the LightRAG indexing endpoint.
    4.  Return the response from LightRAG.
*   **Success Response:** `200 OK` with `{ "status": "success", "document_id": "abc456" }`.
*   **Error Handling:** `400 Bad Request` if the text field is missing or empty.

### 4.3. Image Input

*   **Endpoint:** `POST /api/documents/image`
*   **Description:** Accepts an image file, generates a text description using a multimodal LLM, and indexes this description in LightRAG.
*   **Input:** `multipart/form-data` with a field named `image`.
    *   Supported file types: `.jpg`, `.jpeg`, `.png`, `.webp`.
*   **Processing Logic:**
    1.  Validate the image file.
    2.  Send the image to a multimodal LLM's API with a prompt like: "Describe this image in detail and with precision."
    3.  Receive the text description from the LLM.
    4.  Send this text description to the LightRAG indexing endpoint (as in 4.2).
    5.  Return the response from LightRAG.
*   **Success Response:** `200 OK` with `{ "status": "success", "document_id": "def789", "description": "..." }`.
*   **Error Handling:** `400` for invalid image, `502 Bad Gateway` for issues with the LLM.

### 4.4. YouTube URL Input

*   **Endpoint:** `POST /api/documents/youtube`
*   **Description:** Extracts captions from a YouTube video, creates a document, and indexes it in LightRAG.
*   **Input:** JSON body, e.g., `{ "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ" }`.
*   **Processing Logic:**
    1.  Validate the YouTube URL.
    2.  Use a library to extract the available captions (transcript). German language is preferred, with English as a fallback.
    3.  If no captions are found, return an error message.
    4.  Send the extracted transcript text to the LightRAG indexing endpoint.
    5.  Return the response from LightRAG.
*   **Success Response:** `200 OK` with `{ "status": "success", "document_id": "ghi012", "video_title": "..." }`.
*   **Error Handling:** `400` for invalid URL, `404 Not Found` if no captions are available.

### 4.5. Chat API (OpenAI Compatible)

*   **Endpoint:** `POST /v1/chat/completions`
*   **Description:** An endpoint that accepts requests in the OpenAI chat format, processes them, and returns the response from LightRAG in the OpenAI format.
*   **Input:** JSON body conforming to the OpenAI `chat/completions` request format.
    *   The key is the `messages` array containing `role` and `content`.
*   **Processing Logic:**
    1.  Parse the incoming request.
    2.  Iterate through the `messages` array and the `content` of each message.
    3.  **If a `content` object of type `image_url` is found:**
        a. Download the image.
        b. Generate a text description using the multimodal LLM (as in 4.3).
        c. Replace the `image_url` block in the `content` with this text description.
    4.  Summarize the entire (now text-only) chat history into a single search query for LightRAG (e.g., "Context: [Previous messages]. Current question: [Last message]").
    5.  Send this search query to the LightRAG query API.
    6.  Receive the response from LightRAG.
    7.  Wrap the response from LightRAG into the OpenAI `chat/completions` response format.
        ```json
        {
          "id": "chatcmpl-xyz",
          "object": "chat.completion",
          "created": 1677652288,
          "model": "lightrag-proxy",
          "choices": [{
            "index": 0,
            "message": {
              "role": "assistant",
              "content": "[Response from LightRAG]"
            },
            "finish_reason": "stop"
          }]
        }
        ```
*   **Success Response:** `200 OK` with the JSON body as shown above.
*   **Error Handling:** Appropriate HTTP status codes for errors in the request or during communication with LightRAG/LLM.

---

## 5. Non-Functional Requirements

*   **Configuration:** API keys for LightRAG, the multimodal LLM, and other services must be managed via environment variables or a configuration file (not hardcoded).
*   **Logging:** The service must log detailed information about incoming requests, processing steps, and errors.
*   **Error Messages:** All error responses must contain clear, machine-readable JSON messages.
*   **Asynchronous Processing (Optional, but recommended):** For long-running tasks like image or video processing, an asynchronous pattern (e.g., Task Queue with Celery/RQ) should be considered to prevent the API endpoint from blocking.

## 6. Assumptions

*   A functional LightRAG system exists with accessible APIs for indexing and querying.
*   The AI agent is responsible for setting up the development environment, selecting the specific libraries, and deploying the final service.

---