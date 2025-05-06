# Architecture Overview: PDF Translation Application

## 1. Overview

This application is a web-based PDF translation service that allows users to upload PDF documents, automatically detect the source language, translate the content to a selected target language, and download the translated document. The system handles both text-based PDFs and scanned documents requiring OCR (Optical Character Recognition).

The application follows a client-server architecture with a React frontend, Express.js backend, and PostgreSQL database. The system utilizes Python scripts for PDF processing, OCR, and language detection capabilities.

## 2. System Architecture

The application follows a modern web application architecture with clear separation of concerns:

```
┌─────────────────┐      ┌─────────────────────┐      ┌─────────────────┐
│                 │      │                     │      │                 │
│  React Frontend │<────>│  Express.js Backend │<────>│   PostgreSQL    │
│  (Vite + ShadCN)│      │                     │      │    Database     │
│                 │      │                     │      │                 │
└─────────────────┘      └─────────────────────┘      └─────────────────┘
                                    ^
                                    │
                                    v
                          ┌─────────────────────┐
                          │                     │
                          │   Python Services   │
                          │  (PDF Processing,   │
                          │    OCR, Language    │
                          │      Detection)     │
                          │                     │
                          └─────────────────────┘
```

### Key Architectural Decisions:

1. **Fullstack TypeScript**: The application uses TypeScript for both frontend and backend to ensure type safety across the entire stack.

2. **Hybrid Processing**: The system combines Node.js for the web server and API with Python for specialized document processing tasks.

3. **Modular Design**: The codebase is organized into distinct modules (client, server, shared) with clear responsibilities.

4. **RESTful API**: Communication between frontend and backend is implemented through RESTful API endpoints.

5. **Database Abstraction**: Drizzle ORM provides type-safe database access with schema definitions shared between frontend and backend.

## 3. Key Components

### 3.1 Frontend Architecture

- **Framework**: React with TypeScript
- **Build Tool**: Vite
- **UI Library**: ShadCN UI (based on Radix UI primitives)
- **State Management**: React Query for server state management
- **Styling**: Tailwind CSS for utility-first styling
- **Routing**: Wouter for lightweight routing

The frontend follows a component-based architecture with reusable UI components. The main user flow includes:
1. Document upload
2. Language selection 
3. Translation processing
4. Result download

### 3.2 Backend Architecture

- **Framework**: Express.js with TypeScript
- **API Structure**: RESTful endpoints for document upload, translation, and retrieval
- **File Storage**: Local file system storage for uploaded and processed documents
- **Services**:
  - PDF Service: Handles PDF text extraction and manipulation
  - Python Service: Interface to Python scripts for OCR and language detection

### 3.3 Database Structure

The application uses PostgreSQL with Drizzle ORM for database operations. The schema includes:

- **Users**: Authentication and user management
- **Documents**: Stores metadata about uploaded documents and their translation status
- **Languages**: Supported languages for translation

### 3.4 Python Integration

Python scripts provide specialized functionality:
- Language detection for uploaded documents
- OCR processing for scanned documents
- Text extraction from PDFs
- PDF generation for translated content

## 4. Data Flow

### 4.1 Document Translation Flow

1. **Upload**: User uploads a PDF document through the frontend
2. **Processing**:
   - Backend stores the document and creates a record in the database
   - PDF text extraction is performed (with OCR if needed)
   - Source language is detected automatically
3. **Translation**:
   - User selects target language and output format
   - Backend initiates translation process
   - Progress is tracked in the database
4. **Output Generation**:
   - Translated text is formatted into the selected output format
   - Result document is stored on the server
5. **Download**: User can download the translated document

### 4.2 API Structure

- **`/api/upload`**: Handles document uploads
- **`/api/translate`**: Manages translation requests
- **`/api/documents`**: CRUD operations for documents
- **`/api/languages`**: Retrieves supported languages
- **`/api/download/:id`**: Downloads translated documents

## 5. External Dependencies

### 5.1 Core Dependencies

- **Frontend**:
  - React and React DOM
  - TanStack Query (React Query)
  - Radix UI components
  - Tailwind CSS
  - Lucide Icons

- **Backend**:
  - Express.js
  - Drizzle ORM
  - Multer (file upload handling)
  - Zod (schema validation)
  - UUID for generating unique identifiers

- **Python Dependencies**:
  - PyPDF2 for PDF parsing
  - pytesseract for OCR
  - pdf2image for PDF to image conversion
  - langdetect for language detection
  - reportlab for PDF generation
  - deep_translator for translation services

### 5.2 Infrastructure Dependencies

- PostgreSQL database
- Tesseract OCR engine
- Node.js runtime environment
- Python 3 runtime environment

## 6. Deployment Strategy

The application is configured for deployment on Replit's platform with the following approach:

### 6.1 Development Environment

- Vite development server for hot reloading during development
- Express server handling both API and serving static assets
- TypeScript compilation for both client and server code

### 6.2 Production Deployment

- Client code is built using Vite and output to the `dist/public` directory
- Server code is bundled using esbuild with external dependencies
- The application is deployed as a Node.js service that serves both the API and static frontend assets
- Environment variables are used for configuration differences between environments

### 6.3 Database Deployment

- The application connects to a PostgreSQL database provided by the deployment platform
- Database connection is established using the `DATABASE_URL` environment variable
- Database schema is managed through Drizzle ORM migrations

## 7. Future Considerations

- **Scaling**: Current architecture would benefit from separating file storage to a dedicated service (e.g., S3)
- **Authentication**: Implement full user authentication for document privacy and management
- **Monitoring**: Add logging and monitoring for document processing pipelines 
- **Performance**: Implement caching strategies for improved performance
- **Translation Quality**: Support additional translation services and customization options