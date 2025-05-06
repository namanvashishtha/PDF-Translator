import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import util from 'util';
import { TempFileManager } from '../utils/tempFileManager';

const execAsync = util.promisify(exec);
// Use the system Python path for reliability
const PYTHON_PATH = 'python';

// In-memory cache for OCR check results
const ocrCheckCache = new Map<string, boolean>();

export class PDFService {
  private tempFileManager: TempFileManager;
  private pythonScriptPath: string;

  constructor() {
    this.tempFileManager = new TempFileManager();
    this.pythonScriptPath = path.resolve(process.cwd(), 'scripts/pdf_processor.py');
  }

  /**
   * Extracts text from a PDF file using the Python script
   */
  async extractText(pdfPath: string): Promise<string> {
    try {
      console.log(`Extracting text from PDF: ${path.basename(pdfPath)}`);
      const textOutputPath = this.tempFileManager.createTempFile('extracted', '.txt');
      
      // Use Python script for text extraction with optimized parameters
      const command = `${PYTHON_PATH} "${this.pythonScriptPath}" extract "${pdfPath}" "${textOutputPath}"`;
      console.log(`Executing: ${command}`);
      
      const startTime = Date.now();
      await execAsync(command);
      const duration = Date.now() - startTime;
      console.log(`Text extraction completed in ${duration}ms`);
      
      if (fs.existsSync(textOutputPath)) {
        const text = fs.readFileSync(textOutputPath, 'utf8');
        return text;
      } else {
        throw new Error('Failed to extract text from PDF');
      }
    } catch (error) {
      console.error('Error extracting text from PDF:', error);
      throw new Error(`Failed to extract text: ${error}`);
    }
  }

  /**
   * Determines if a PDF needs OCR (has scanned/image content)
   * Uses caching to avoid repeated processing of the same file
   */
  async needsOcr(pdfPath: string): Promise<boolean> {
    try {
      // Check cache first
      if (ocrCheckCache.has(pdfPath)) {
        const needsOcr = ocrCheckCache.get(pdfPath)!;
        console.log(`Using cached OCR check result for ${path.basename(pdfPath)}: ${needsOcr}`);
        return needsOcr;
      }
      
      console.log(`Checking if PDF needs OCR: ${path.basename(pdfPath)}`);
      // Run Python script to check if OCR is needed
      const command = `${PYTHON_PATH} "${this.pythonScriptPath}" check_ocr "${pdfPath}"`;
      
      const { stdout } = await execAsync(command);
      const needsOcr = stdout.trim() === 'true';
      
      // Cache the result
      ocrCheckCache.set(pdfPath, needsOcr);
      
      console.log(`OCR needed for ${path.basename(pdfPath)}: ${needsOcr}`);
      return needsOcr;
    } catch (error) {
      console.error('Error checking if PDF needs OCR:', error);
      // Default to false (direct extraction) for better performance
      // If direct extraction fails, we'll fall back to OCR in the translation process
      return false;
    }
  }

  /**
   * Creates a PDF from translated text
   */
  async createPdf(text: string, language: string): Promise<string> {
    try {
      console.log(`Creating PDF for translated text in ${language}`);
      const textPath = this.tempFileManager.createTempFile('content', '.txt');
      fs.writeFileSync(textPath, text);
      
      const outputPdfPath = this.tempFileManager.createTempFile('translated', '.pdf');
      
      // Use Python script to generate PDF
      const command = `${PYTHON_PATH} "${this.pythonScriptPath}" create_pdf "${textPath}" "${outputPdfPath}" "${language}"`;
      console.log(`Executing: ${command}`);
      
      const startTime = Date.now();
      await execAsync(command);
      const duration = Date.now() - startTime;
      console.log(`PDF creation completed in ${duration}ms`);
      
      if (!fs.existsSync(outputPdfPath)) {
        throw new Error('Failed to create PDF file');
      }
      
      return outputPdfPath;
    } catch (error) {
      console.error('Error creating PDF:', error);
      throw new Error(`Failed to create PDF: ${error}`);
    }
  }

  /**
   * Creates a dual-language PDF with original and translated text
   */
  async createDualLanguagePdf(
    originalText: string,
    translatedText: string,
    sourceLanguage: string,
    targetLanguage: string
  ): Promise<string> {
    try {
      console.log(`Creating dual-language PDF (${sourceLanguage} → ${targetLanguage})`);
      const originalTextPath = this.tempFileManager.createTempFile('original', '.txt');
      const translatedTextPath = this.tempFileManager.createTempFile('translated', '.txt');
      
      fs.writeFileSync(originalTextPath, originalText);
      fs.writeFileSync(translatedTextPath, translatedText);
      
      const outputPdfPath = this.tempFileManager.createTempFile('dual-language', '.pdf');
      
      // Use Python script to generate dual-language PDF
      const command = `${PYTHON_PATH} "${this.pythonScriptPath}" create_dual_pdf "${originalTextPath}" "${translatedTextPath}" "${outputPdfPath}" "${sourceLanguage}" "${targetLanguage}"`;
      console.log(`Executing: ${command}`);
      
      const startTime = Date.now();
      await execAsync(command);
      const duration = Date.now() - startTime;
      console.log(`Dual-language PDF creation completed in ${duration}ms`);
      
      if (!fs.existsSync(outputPdfPath)) {
        throw new Error('Failed to create dual-language PDF');
      }
      
      return outputPdfPath;
    } catch (error) {
      console.error('Error creating dual-language PDF:', error);
      throw new Error(`Failed to create dual-language PDF: ${error}`);
    }
  }
  
  /**
   * Translates a PDF while preserving images and layout
   */
  async translatePdfWithImages(
    inputPdfPath: string,
    sourceLanguage: string, 
    targetLanguage: string
  ): Promise<string> {
    try {
      console.log(`Translating PDF with image preservation from ${sourceLanguage} to ${targetLanguage}`);
      
      const outputPdfPath = this.tempFileManager.createTempFile('translated-with-images', '.pdf');
      
      // Use Python script to translate PDF while preserving images
      const command = `${PYTHON_PATH} "${this.pythonScriptPath}" translate_pdf "${inputPdfPath}" "${outputPdfPath}" "${sourceLanguage}" "${targetLanguage}"`;
      console.log(`Executing: ${command}`);
      
      const startTime = Date.now();
      await execAsync(command);
      const duration = Date.now() - startTime;
      console.log(`PDF translation with image preservation completed in ${duration}ms`);
      
      if (!fs.existsSync(outputPdfPath)) {
        throw new Error('Failed to translate PDF with image preservation');
      }
      
      return outputPdfPath;
    } catch (error) {
      console.error('Error translating PDF with image preservation:', error);
      throw new Error(`Failed to translate PDF with image preservation: ${error}`);
    }
  }
}
