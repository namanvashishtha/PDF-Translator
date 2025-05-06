import { exec } from 'child_process';
import util from 'util';
import fs from 'fs';
import path from 'path';
import { TempFileManager } from '../utils/tempFileManager';

const execAsync = util.promisify(exec);
// Use the system Python path for reliability
const PYTHON_PATH = 'python';

export class PythonService {
  private tempFileManager: TempFileManager;
  private pythonScriptPath: string;

  constructor() {
    this.tempFileManager = new TempFileManager();
    this.pythonScriptPath = path.resolve(process.cwd(), 'scripts/pdf_processor.py');
  }

  /**
   * Detects language of a PDF document
   */
  async detectLanguage(pdfPath: string): Promise<string> {
    try {
      console.log(`Detecting language for ${pdfPath}...`);
      // Run Python script to detect language
      const { stdout, stderr } = await execAsync(`${PYTHON_PATH} "${this.pythonScriptPath}" detect_language "${pdfPath}"`);
      
      if (stderr) {
        console.error('Error in language detection:', stderr);
      }
      
      const language = stdout.trim();
      console.log(`Detected language: ${language || 'en (default)'}`);
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
      console.log(`Extracting text with OCR from ${pdfPath}...`);
      const outputTextPath = this.tempFileManager.createTempFile('ocr-output', '.txt');
      
      // Run OCR using Python script with optimized parameters
      const command = `${PYTHON_PATH} "${this.pythonScriptPath}" ocr "${pdfPath}" "${outputTextPath}"`;
      console.log(`Executing: ${command}`);
      await execAsync(command);
      
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
   * Map language codes to ones supported by Google Translator
   */
  private mapLanguageCode(code: string): string {
    // Language code mapping
    const languageMapping: Record<string, string> = {
      // ISO 639-1 language codes
      'en': 'en',    // English
      'es': 'es',    // Spanish
      'fr': 'fr',    // French
      'de': 'de',    // German
      'it': 'it',    // Italian
      'pt': 'pt',    // Portuguese
      'nl': 'nl',    // Dutch
      'ru': 'ru',    // Russian
      'ja': 'ja',    // Japanese
      'zh': 'zh-CN', // Chinese (simplified)
      'ar': 'ar',    // Arabic
      'ko': 'ko',    // Korean
      'tr': 'tr',    // Turkish
      'pl': 'pl',    // Polish
      'sv': 'sv',    // Swedish
      'hi': 'hi',    // Hindi
      // Add more mappings as needed
    };
    
    return languageMapping[code] || code;
  }

  /**
   * Translates text from source language to target language with optimized chunking
   */
  async translateText(
    text: string, 
    sourceLanguage: string, 
    targetLanguage: string
  ): Promise<string> {
    try {
      // Clean up language codes for compatibility with Google Translator
      const sourceCode = this.mapLanguageCode(sourceLanguage);
      const targetCode = this.mapLanguageCode(targetLanguage);
      
      console.log(`Translating text from ${sourceLanguage} (${sourceCode}) to ${targetLanguage} (${targetCode})...`);
      
      // Don't translate if languages are the same
      if (sourceLanguage === targetLanguage) {
        console.log('Source and target languages are the same, skipping translation');
        return text;
      }
      
      const inputTextPath = this.tempFileManager.createTempFile('to-translate', '.txt');
      const outputTextPath = this.tempFileManager.createTempFile('translated', '.txt');
      
      // Write text to temporary file
      fs.writeFileSync(inputTextPath, text);
      
      // Run translation using Python script with mapped language codes
      const command = `${PYTHON_PATH} "${this.pythonScriptPath}" translate "${inputTextPath}" "${outputTextPath}" "${sourceCode}" "${targetCode}"`;
      console.log(`Executing: ${command}`);
      await execAsync(command);
      
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
