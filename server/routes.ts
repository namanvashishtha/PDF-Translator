import type { Express, Request, Response } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import multer from "multer";
import path from "path";
import fs from "fs";
import { translationRequestSchema } from "@shared/schema";
import { PDFService } from "./services/pdfService";
import { PythonService } from "./services/pythonService";
import { TempFileManager } from "./utils/tempFileManager";
import { z } from "zod";
import { ZodError } from "zod";

const uploadsDir = path.join(process.cwd(), "uploads");

// Ensure uploads directory exists
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Configure multer for file uploads
const upload = multer({
  storage: multer.diskStorage({
    destination: function (req, file, cb) {
      cb(null, uploadsDir);
    },
    filename: function (req, file, cb) {
      const uniqueSuffix = Date.now() + "-" + Math.round(Math.random() * 1e9);
      cb(null, uniqueSuffix + path.extname(file.originalname));
    },
  }),
  // Limit to 50MB
  limits: { fileSize: 50 * 1024 * 1024 },
  fileFilter: function (req, file, cb) {
    // Accept only PDFs
    if (file.mimetype !== "application/pdf") {
      return cb(new Error("Only PDF files are allowed"));
    }
    cb(null, true);
  },
});

// Service instances
const pdfService = new PDFService();
const pythonService = new PythonService();
const tempFileManager = new TempFileManager();

export async function registerRoutes(app: Express): Promise<Server> {
  // Error handling middleware for specific error types
  app.use((err: any, req: Request, res: Response, next: any) => {
    if (err instanceof multer.MulterError) {
      if (err.code === "LIMIT_FILE_SIZE") {
        return res.status(400).json({ message: "File size exceeds 50MB limit" });
      }
      return res.status(400).json({ message: err.message });
    }
    
    if (err instanceof ZodError) {
      return res.status(400).json({ 
        message: "Validation error", 
        errors: err.errors
      });
    }
    
    next(err);
  });

  // Upload PDF endpoint
  app.post("/api/upload", upload.single("file"), async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ message: "No file uploaded" });
      }

      // Save document info to storage
      const document = await storage.createDocument({
        originalName: req.file.originalname,
        storagePath: req.file.path,
        outputFormat: "pdf",
        status: "pending",
      });

      // Detect language asynchronously
      pythonService.detectLanguage(req.file.path)
        .then(async (language) => {
          // Clean up language code, ensuring it's not the output of the detection script
          let cleanLanguage = language;
          
          // Check if language is the full script output instead of just code
          if (language.includes('Detecting language for') || language.includes('Fast text extraction')) {
            console.log("Cleaning up detected language output:", language);
            // Extract the actual language code (usually at the end)
            const matches = language.match(/[a-z]{2}$/);
            if (matches && matches.length > 0) {
              cleanLanguage = matches[0];
            } else {
              // Default to English if we can't extract the language code
              cleanLanguage = 'en';
            }
          }
          
          console.log(`Cleaned language code: "${cleanLanguage}"`);
          
          await storage.updateDocument(document.id, { 
            originalLanguage: cleanLanguage,
            status: "language_detected"
          });
        })
        .catch(error => {
          console.error("Language detection error:", error);
          // Default to English on error
          storage.updateDocument(document.id, { 
            originalLanguage: 'en',
            status: "language_detected"
          });
        });

      return res.status(201).json({ document });
    } catch (error) {
      console.error("Error uploading file:", error);
      return res.status(500).json({ message: "Error uploading file" });
    }
  });

  // Get document details
  app.get("/api/documents/:id", async (req, res) => {
    try {
      const document = await storage.getDocument(parseInt(req.params.id));
      if (!document) {
        return res.status(404).json({ message: "Document not found" });
      }
      return res.json(document);
    } catch (error) {
      console.error("Error getting document:", error);
      return res.status(500).json({ message: "Error retrieving document" });
    }
  });

  // List supported languages
  app.get("/api/languages", async (req, res) => {
    try {
      const languages = await storage.getLanguages();
      return res.json(languages);
    } catch (error) {
      console.error("Error fetching languages:", error);
      return res.status(500).json({ message: "Error fetching languages" });
    }
  });

  // Start translation process
  app.post("/api/translate", async (req, res) => {
    try {
      const data = translationRequestSchema.parse(req.body);
      const document = await storage.getDocument(data.documentId);
      
      if (!document) {
        return res.status(404).json({ message: "Document not found" });
      }

      // Update document with translation request details
      await storage.updateDocument(document.id, {
        targetLanguage: data.targetLanguage,
        outputFormat: data.outputFormat,
        status: "translating"
      });

      // Process the translation asynchronously
      // Check if PDF contains images and adjust process accordingly
      const preserveImages = data.preserveImages === true; // Default to false if not specified
      
      processTranslation(document.id, data.targetLanguage, data.outputFormat, preserveImages)
        .catch(error => {
          console.error("Translation processing error:", error);
          storage.updateDocument(document.id, { status: "error" });
        });

      return res.status(202).json({ 
        message: "Translation started",
        documentId: document.id 
      });
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ 
          message: "Invalid request data", 
          errors: error.errors 
        });
      }
      console.error("Error starting translation:", error);
      return res.status(500).json({ message: "Error starting translation" });
    }
  });

  // Check translation status
  app.get("/api/translate/status/:id", async (req, res) => {
    try {
      const document = await storage.getDocument(parseInt(req.params.id));
      if (!document) {
        return res.status(404).json({ message: "Document not found" });
      }
      return res.json({ status: document.status });
    } catch (error) {
      console.error("Error checking translation status:", error);
      return res.status(500).json({ message: "Error checking translation status" });
    }
  });

  // Download translated document
  app.get("/api/download/:id", async (req, res) => {
    try {
      const document = await storage.getDocument(parseInt(req.params.id));
      
      if (!document) {
        return res.status(404).json({ message: "Document not found" });
      }
      
      if (document.status !== "completed" || !document.translatedPath) {
        return res.status(400).json({ message: "Translation not ready for download" });
      }
      
      if (!fs.existsSync(document.translatedPath)) {
        return res.status(404).json({ message: "Translated file not found" });
      }

      // Get the appropriate filename extension
      const extension = document.outputFormat === "txt" ? ".txt" : ".pdf";
      const originalName = document.originalName.replace(/\.pdf$/i, "");
      const downloadName = `${originalName}-translated-${document.targetLanguage}${extension}`;
      
      res.setHeader("Content-Disposition", `attachment; filename="${downloadName}"`);
      res.setHeader("Content-Type", document.outputFormat === "txt" ? "text/plain" : "application/pdf");
      
      const fileStream = fs.createReadStream(document.translatedPath);
      fileStream.pipe(res);
    } catch (error) {
      console.error("Error downloading file:", error);
      return res.status(500).json({ message: "Error downloading file" });
    }
  });

  // Seed languages if needed
  await seedLanguages();

  const httpServer = createServer(app);
  return httpServer;
}

// Cache for document extraction (in-memory cache to avoid repeated processing)
const extractionCache = new Map<string, string>();

// Process translation asynchronously with optimizations
async function processTranslation(
  documentId: number, 
  targetLanguage: string, 
  outputFormat: string,
  preserveImages: boolean = false
): Promise<void> {
  console.log(`Starting translation process for document ${documentId} to ${targetLanguage} in ${outputFormat} format`);
  
  try {
    const document = await storage.getDocument(documentId);
    if (!document) {
      throw new Error(`Document ${documentId} not found`);
    }

    // Update status to processing
    await storage.updateDocument(documentId, { status: "processing" });
    
    // Check if we need to extract text or can use cache
    const cacheKey = document.storagePath;
    let extractedText: string;
    
    if (extractionCache.has(cacheKey)) {
      console.log(`Using cached text extraction for ${document.originalName}`);
      extractedText = extractionCache.get(cacheKey)!;
    } else {
      console.log(`Extracting text from ${document.originalName}`);
      
      // Check if we need OCR
      const needsOcr = await pdfService.needsOcr(document.storagePath);
      
      if (needsOcr) {
        // Use OCR to extract text
        console.log(`Using OCR for document ${documentId}`);
        await storage.updateDocument(documentId, { status: "ocr_processing" });
        extractedText = await pythonService.extractTextWithOcr(document.storagePath);
      } else {
        // Extract text directly from PDF
        console.log(`Using direct extraction for document ${documentId}`);
        extractedText = await pdfService.extractText(document.storagePath);
      }

      if (!extractedText) {
        throw new Error("Failed to extract text from PDF");
      }
      
      // Cache the extracted text
      extractionCache.set(cacheKey, extractedText);
    }

    // Update status to translating
    await storage.updateDocument(documentId, { status: "translating" });
    console.log(`Starting translation from ${document.originalLanguage} to ${targetLanguage}`);

    // Fast path: if source and target languages are the same, skip translation
    let translatedText: string;
    if (document.originalLanguage === targetLanguage) {
      console.log(`Source and target languages are the same (${targetLanguage}), skipping translation`);
      translatedText = extractedText;
    } else {
      // Step 2: Translate text
      console.log(`Translating document ${documentId} content`);
      translatedText = await pythonService.translateText(
        extractedText,
        document.originalLanguage || "auto",
        targetLanguage
      );

      if (!translatedText) {
        throw new Error("Translation failed");
      }
    }

    // Step 3: Generate output document
    let outputFilePath: string;
    await storage.updateDocument(documentId, { status: "generating_output" });
    console.log(`Generating ${outputFormat} output for document ${documentId}`);

    if (outputFormat === "txt") {
      // Create text file (fastest option)
      outputFilePath = tempFileManager.createTempFile("translated", ".txt");
      fs.writeFileSync(outputFilePath, translatedText);
      console.log(`Text file output created at ${outputFilePath}`);
    } else if (outputFormat === "dual") {
      // Create dual-language PDF
      console.log(`Creating dual-language PDF for document ${documentId}`);
      outputFilePath = await pdfService.createDualLanguagePdf(
        extractedText,
        translatedText,
        document.originalLanguage || "Unknown",
        targetLanguage
      );
    } else {
      // Create translated PDF
      console.log(`Creating translated PDF for document ${documentId}`);
      outputFilePath = await pdfService.createPdf(translatedText, targetLanguage);
    }

    // Update document with translated file path and completion status
    await storage.updateDocument(documentId, {
      translatedPath: outputFilePath,
      status: "completed"
    });
    
    console.log(`Translation process completed for document ${documentId}`);
  } catch (error) {
    console.error(`Error processing translation for document ${documentId}:`, error);
    await storage.updateDocument(documentId, { status: "error" });
    throw error;
  }
}

// Seed the languages database with initial data
async function seedLanguages() {
  const languages = [
    { code: "en", name: "English", nativeName: "English", flag: "🇺🇸" },
    { code: "es", name: "Spanish", nativeName: "Español", flag: "🇪🇸" },
    { code: "fr", name: "French", nativeName: "Français", flag: "🇫🇷" },
    { code: "de", name: "German", nativeName: "Deutsch", flag: "🇩🇪" },
    { code: "it", name: "Italian", nativeName: "Italiano", flag: "🇮🇹" },
    { code: "pt", name: "Portuguese", nativeName: "Português", flag: "🇵🇹" },
    { code: "ja", name: "Japanese", nativeName: "日本語", flag: "🇯🇵" },
    { code: "zh", name: "Chinese", nativeName: "中文", flag: "🇨🇳" },
    { code: "ru", name: "Russian", nativeName: "Русский", flag: "🇷🇺" },
    { code: "ar", name: "Arabic", nativeName: "العربية", flag: "🇦🇪" },
    { code: "hi", name: "Hindi", nativeName: "हिन्दी", flag: "🇮🇳" },
    { code: "nl", name: "Dutch", nativeName: "Nederlands", flag: "🇳🇱" },
    { code: "ko", name: "Korean", nativeName: "한국어", flag: "🇰🇷" },
    { code: "tr", name: "Turkish", nativeName: "Türkçe", flag: "🇹🇷" },
    { code: "sv", name: "Swedish", nativeName: "Svenska", flag: "🇸🇪" },
    { code: "pl", name: "Polish", nativeName: "Polski", flag: "🇵🇱" },
  ];

  // Check if languages are already seeded
  const existingLanguages = await storage.getLanguages();
  if (existingLanguages.length === 0) {
    // Add languages one by one
    for (const language of languages) {
      await storage.addLanguage(language);
    }
    console.log("Seeded languages database");
  }
}
