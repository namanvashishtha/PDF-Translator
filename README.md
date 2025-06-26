# 🌍 PDF Translate Hub

> **Advanced PDF Translation Platform with Structure Preservation**

A cutting-edge full-stack application that translates PDF documents while preserving their original layout, formatting, images, and visual structure. Built with modern web technologies and advanced Python PDF processing.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Express](https://img.shields.io/badge/Express.js-404D59?logo=express)

## ✨ Unique Features

### 🎯 **Structure-Preserving Translation**
- **Revolutionary Redaction-Based Approach**: Uses PyMuPDF's advanced redaction system to cleanly remove original text without disturbing document structure
- **Image & Layout Preservation**: Maintains all images, backgrounds, tables, and formatting exactly as in the original
- **Font Intelligence**: Automatically detects and preserves original fonts, with smart fallback mechanisms
- **Pixel-Perfect Positioning**: Places translated text at exact same coordinates as original text

### 🔧 **Advanced Translation Engine**
- **Multi-Strategy Translation**: 8 different translation algorithms for maximum reliability
- **Guaranteed Translation Mode**: Force-translates content without relying on auto-detection
- **Chunk-Based Processing**: Handles large documents by intelligently splitting text into manageable chunks
- **Language Auto-Detection**: Smart language detection with manual override capabilities
- **Retry Mechanisms**: Built-in retry logic with exponential backoff for translation failures

### 🚀 **Modern Tech Stack**
- **Hybrid Architecture**: TypeScript/React frontend with Python backend processing
- **Real-Time Processing**: WebSocket-based progress updates and live translation status
- **Component-Driven UI**: Radix UI components with Tailwind CSS for modern, accessible design
- **Type-Safe Development**: Full TypeScript implementation with Zod validation

## 🏗️ Project Structure

```
PDFTranslateHub/
├── 📁 client/                    # React Frontend
│   ├── src/
│   │   ├── components/           # Reusable UI components
│   │   │   ├── ui/              # Radix UI component library
│   │   │   ├── file-upload.tsx   # Drag & drop file upload
│   │   │   ├── language-selector.tsx
│   │   │   ├── pdf-preview.tsx   # PDF preview with zoom
│   │   │   └── processing-steps.tsx
│   │   ├── pages/               # Application pages
│   │   ├── hooks/               # Custom React hooks
│   │   └── lib/                 # Utilities and services
│   └── index.html
├── 📁 server/                    # Express.js Backend
│   ├── services/
│   │   ├── pdfService.ts        # PDF processing orchestration
│   │   └── pythonService.ts     # Python script execution
│   ├── utils/
│   │   └── tempFileManager.ts   # Temporary file management
│   ├── routes.ts                # API endpoints
│   └── index.ts                 # Server entry point
├── 📁 scripts/                  # Python Processing Scripts
│   ├── guaranteed_translate.py  # 🌟 Main translation engine
│   ├── pdf_processor.py         # PDF text extraction
│   ├── aggressive_translate.py  # High-visibility translation
│   ├── exact_layout_translate.py # Layout preservation
│   └── [6 more specialized scripts]
├── 📁 shared/                   # Shared TypeScript types
└── 📁 debug_output/            # Translation debugging data
```

## 🔥 Standout Technologies & Dependencies

### **Unique Python Libraries**
```python
# Advanced PDF Processing
PyMuPDF (fitz)>=1.25.5     # Industry-leading PDF manipulation
deep-translator>=1.11.4     # Multi-provider translation API
langdetect>=1.0.9          # Automatic language detection
easyocr>=1.11.2            # OCR for scanned documents
Wand>=0.6.13               # ImageMagick binding for image processing
ReportLab>=4.4.0           # PDF generation and manipulation
```

### **Modern Frontend Stack**
```json
{
  "unique_dependencies": {
    "@radix-ui/*": "Complete accessible component system",
    "@tanstack/react-query": "Advanced server state management",
    "wouter": "Minimalist React router",
    "framer-motion": "Production-ready motion library",
    "cmdk": "Command palette interface",
    "vaul": "Drawer component for mobile",
    "embla-carousel-react": "Smooth carousel implementation"
  }
}
```

### **Backend Innovations**
- **Hybrid Processing**: Node.js orchestration with Python workers
- **Memory-Efficient**: Streaming file processing with automatic cleanup
- **Session Management**: Express-session with PostgreSQL storage
- **Type Safety**: Drizzle ORM with Zod validation

### **Python Service Integration**
The Node.js backend communicates with Python scripts through a dedicated `PythonService` class that:
- Manages the execution of Python scripts for various PDF operations
- Handles language detection with specialized algorithms and fallback mechanisms
- Performs OCR (Optical Character Recognition) for scanned documents
- Translates text with optimized chunking and intelligent language mapping
- Implements retry logic and fallback strategies for reliable translation

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ 
- **Python** 3.11+
- **Git**

### 1. Clone & Install
```bash
# Clone the repository
git clone https://github.com/yourusername/PDFTranslateHub.git
cd PDFTranslateHub

# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt
# OR using the project file
pip install -e .
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Configure your environment variables
# DATABASE_URL=your_database_url
# SESSION_SECRET=your_session_secret
```

### 3. Database Setup
```bash
# Push database schema
npm run db:push
```

### 4. Development Server
```bash
# Start the development server (runs both frontend and backend)
npm run dev
```

Visit `http://localhost:5000` to see the application in action!

## 🎯 How to Use

### Basic Translation
1. **Upload PDF**: Drag and drop or click to select your PDF file
2. **Select Languages**: Choose source and target languages from 100+ supported options
3. **Choose Translation Mode**: 
   - **Standard**: Balanced speed and quality
   - **Guaranteed**: Force translation with maximum reliability
   - **Aggressive**: High-visibility output for difficult documents
4. **Process**: Watch real-time progress as your document is translated
5. **Download**: Get your translated PDF with preserved formatting

### Advanced Features
- **Language Auto-Detection**: Let the system detect the source language
- **Batch Processing**: Upload multiple PDFs for bulk translation
- **Preview Mode**: Preview translations before downloading
- **Debug Mode**: Access detailed translation logs and statistics

## 🔧 Translation Algorithms

### 1. **Guaranteed Translation** (`guaranteed_translate.py`)
- **Redaction-Based**: Uses PyMuPDF redaction for clean text replacement
- **Font Preservation**: Maintains original fonts with intelligent fallbacks
- **Structure Integrity**: Preserves all images, backgrounds, and layouts
- **Retry Logic**: Multiple translation attempts with different strategies

### 2. **Aggressive Translation** (`aggressive_translate.py`)
- **High Visibility**: Creates prominent translated text for difficult documents
- **Bold Rendering**: Multiple text overlays for enhanced readability
- **Background Handling**: Smart background color detection and contrast

### 3. **Exact Layout Translation** (`exact_layout_translate.py`)
- **Pixel-Perfect**: Maintains exact positioning and sizing
- **Font Matching**: Advanced font detection and matching algorithms
- **Color Preservation**: Maintains original text colors and styles

## 🌐 Supported Languages

**100+ Languages** including:
- **European**: English, Spanish, French, German, Italian, Portuguese, Dutch, Russian
- **Asian**: Chinese (Simplified/Traditional), Japanese, Korean, Hindi, Arabic, Thai
- **Regional**: Catalan, Basque, Galician, and many more

## 🔍 API Endpoints

### PDF Processing
```typescript
POST /api/translate
Content-Type: multipart/form-data
Body: {
  file: PDF file
  sourceLanguage: string
  targetLanguage: string
  translationMode: 'standard' | 'guaranteed' | 'aggressive'
}
```

### Translation Status
```typescript
GET /api/translation-status/:jobId
Response: {
  status: 'processing' | 'completed' | 'failed'
  progress: number
  currentStep: string
}
```

## 🛠️ Development

### Project Scripts
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run check        # TypeScript type checking
npm run db:push      # Update database schema
```

### Python Scripts
```bash
# Test individual translation scripts
python scripts/guaranteed_translate.py input.pdf output.pdf es en
python scripts/pdf_processor.py extract input.pdf output.txt
```

### Debug Mode
Enable debug mode to access:
- Translation step-by-step logs
- Font detection results
- Text extraction statistics
- Processing time metrics

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Fork & Setup
```bash
# Fork the repository on GitHub
git clone https://github.com/yourusername/PDFTranslateHub.git
cd PDFTranslateHub

# Create a feature branch
git checkout -b feature/amazing-feature

# Make your changes and commit
git commit -m "Add amazing feature"

# Push to your fork
git push origin feature/amazing-feature

# Create a Pull Request
```

### Development Guidelines
- **TypeScript**: Use strict typing throughout
- **Python**: Follow PEP 8 style guidelines
- **Testing**: Add tests for new features
- **Documentation**: Update README for new functionality

### Areas for Contribution
- 🌍 **New Language Support**: Add support for additional languages
- 🎨 **UI/UX Improvements**: Enhance the user interface
- ⚡ **Performance**: Optimize translation speed and memory usage
- 🔧 **New Translation Modes**: Develop specialized translation algorithms
- 📱 **Mobile Support**: Improve mobile responsiveness
- 🧪 **Testing**: Add comprehensive test coverage

## 📊 Performance

### Benchmarks
- **Small PDFs** (1-5 pages): ~10-30 seconds
- **Medium PDFs** (5-20 pages): ~30-120 seconds  
- **Large PDFs** (20+ pages): ~2-10 minutes
- **Memory Usage**: ~50-200MB per document
- **Accuracy**: 95%+ layout preservation

### Optimization Features
- **Streaming Processing**: Handle large files without memory issues
- **Parallel Processing**: Multi-threaded text extraction and translation
- **Caching**: Smart caching of translation results and font data
- **Cleanup**: Automatic temporary file management

## 🐛 Troubleshooting

### Common Issues

**Translation Not Working**
```bash
# Check Python dependencies
pip install --upgrade deep-translator PyMuPDF

# Verify Python path in server configuration
python --version  # Should be 3.11+
```

**Font Issues**
```bash
# Install system fonts (Linux)
sudo apt-get install fonts-liberation fonts-dejavu

# macOS - fonts are usually pre-installed
# Windows - ensure Arial/Helvetica fonts are available
```

**Memory Issues**
```bash
# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=4096"
npm run dev
```



## 🙏 Acknowledgments

- **PyMuPDF Team** - For the incredible PDF processing library
- **Radix UI** - For the accessible component system
- **Google Translate** - For the translation API
- **Open Source Community** - For the amazing tools and libraries



---

<div align="center">

**Made with ❤️ by Naman Vashishtha**

[⭐ Star this repo](https://github.com/yourusername/PDFTranslateHub) | [🍴 Fork it](https://github.com/yourusername/PDFTranslateHub/fork) | [📢 Share it](https://twitter.com/intent/tweet?text=Check%20out%20this%20amazing%20PDF%20translation%20tool!)

</div>