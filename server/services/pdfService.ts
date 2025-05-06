import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import util from 'util';
import { TempFileManager } from '../utils/tempFileManager';

const execAsync = util.promisify(exec);

export class PDFService {
  private tempFileManager: TempFileManager;

  constructor() {
    this.tempFileManager = new TempFileManager();
  }

  /**
   * Extracts text from a PDF file using pdftotext (poppler-utils)
   */
  async extractText(pdfPath: string): Promise<string> {
    try {
      const textOutputPath = this.tempFileManager.createTempFile('extracted', '.txt');
      
      // Use pdf2text from poppler-utils
      await execAsync(`python3 scripts/pdf_processor.py extract "${pdfPath}" "${textOutputPath}"`);
      
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
   */
  async needsOcr(pdfPath: string): Promise<boolean> {
    try {
      // Run Python script to check if OCR is needed
      const { stdout } = await execAsync(`python3 scripts/pdf_processor.py check_ocr "${pdfPath}"`);
      return stdout.trim() === 'true';
    } catch (error) {
      console.error('Error checking if PDF needs OCR:', error);
      // Default to using OCR if we can't determine
      return true;
    }
  }

  /**
   * Creates a PDF from translated text
   */
  async createPdf(text: string, language: string): Promise<string> {
    try {
      const textPath = this.tempFileManager.createTempFile('content', '.txt');
      fs.writeFileSync(textPath, text);
      
      const outputPdfPath = this.tempFileManager.createTempFile('translated', '.pdf');
      
      // Use Python script to generate PDF
      await execAsync(`python3 scripts/pdf_processor.py create_pdf "${textPath}" "${outputPdfPath}" "${language}"`);
      
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
      const originalTextPath = this.tempFileManager.createTempFile('original', '.txt');
      const translatedTextPath = this.tempFileManager.createTempFile('translated', '.txt');
      
      fs.writeFileSync(originalTextPath, originalText);
      fs.writeFileSync(translatedTextPath, translatedText);
      
      const outputPdfPath = this.tempFileManager.createTempFile('dual-language', '.pdf');
      
      // Use Python script to generate dual-language PDF
      await execAsync(
        `python3 scripts/pdf_processor.py create_dual_pdf "${originalTextPath}" "${translatedTextPath}" "${outputPdfPath}" "${sourceLanguage}" "${targetLanguage}"`
      );
      
      if (!fs.existsSync(outputPdfPath)) {
        throw new Error('Failed to create dual-language PDF');
      }
      
      return outputPdfPath;
    } catch (error) {
      console.error('Error creating dual-language PDF:', error);
      throw new Error(`Failed to create dual-language PDF: ${error}`);
    }
  }
}
