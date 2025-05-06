import { exec } from 'child_process';
import util from 'util';
import fs from 'fs';
import path from 'path';
import { TempFileManager } from '../utils/tempFileManager';

const execAsync = util.promisify(exec);

export class PythonService {
  private tempFileManager: TempFileManager;

  constructor() {
    this.tempFileManager = new TempFileManager();
  }

  /**
   * Detects language of a PDF document
   */
  async detectLanguage(pdfPath: string): Promise<string> {
    try {
      // Run Python script to detect language
      const { stdout, stderr } = await execAsync(`python3 scripts/pdf_processor.py detect_language "${pdfPath}"`);
      
      if (stderr) {
        console.error('Error in language detection:', stderr);
      }
      
      const language = stdout.trim();
      return language || 'en'; // Default to English if detection fails
    } catch (error) {
      console.error('Error detecting language:', error);
      return 'en'; // Default to English on error
    }
  }

  /**
   * Extracts text from a PDF using OCR
   */
  async extractTextWithOcr(pdfPath: string): Promise<string> {
    try {
      const outputTextPath = this.tempFileManager.createTempFile('ocr-output', '.txt');
      
      // Run OCR using Python script
      await execAsync(`python3 scripts/pdf_processor.py ocr "${pdfPath}" "${outputTextPath}"`);
      
      if (fs.existsSync(outputTextPath)) {
        return fs.readFileSync(outputTextPath, 'utf8');
      } else {
        throw new Error('OCR failed to produce output file');
      }
    } catch (error) {
      console.error('Error extracting text with OCR:', error);
      throw new Error(`OCR extraction failed: ${error}`);
    }
  }

  /**
   * Translates text from source language to target language
   */
  async translateText(
    text: string, 
    sourceLanguage: string, 
    targetLanguage: string
  ): Promise<string> {
    try {
      const inputTextPath = this.tempFileManager.createTempFile('to-translate', '.txt');
      const outputTextPath = this.tempFileManager.createTempFile('translated', '.txt');
      
      // Write text to temporary file
      fs.writeFileSync(inputTextPath, text);
      
      // Run translation using Python script
      await execAsync(`python3 scripts/pdf_processor.py translate "${inputTextPath}" "${outputTextPath}" "${sourceLanguage}" "${targetLanguage}"`);
      
      if (fs.existsSync(outputTextPath)) {
        return fs.readFileSync(outputTextPath, 'utf8');
      } else {
        throw new Error('Translation failed to produce output file');
      }
    } catch (error) {
      console.error('Error translating text:', error);
      throw new Error(`Translation failed: ${error}`);
    }
  }
}
