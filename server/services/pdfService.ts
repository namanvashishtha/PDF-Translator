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

      // KILO CODE: Commented out problematic language override to use detected language
      // // OVERRIDE SOURCE LANGUAGE - Force to work with common languages
      // // This is a critical fix to address the language detection issues
      // let actualSourceLang = "es";  // Spanish default
      // if (sourceLanguage === "ca" || sourceLanguage === "es") {
      //   actualSourceLang = "es";
      //   console.log(`Using Spanish (es) as source language instead of ${sourceLanguage}`);
      // } else if (sourceLanguage === "fr") {
      //   actualSourceLang = "fr";
      // } else if (sourceLanguage === "de") {
      //   actualSourceLang = "de";
      // } else if (sourceLanguage === "it") {
      //   actualSourceLang = "it";
      // } else {
      //   console.log(`Using Spanish (es) as fallback source language instead of ${sourceLanguage}`);
      // }
      let actualSourceLang = sourceLanguage; // KILO CODE: Use the passed sourceLanguage
      console.log(`Using source language: ${actualSourceLang}`);
      
      // Special case for Spanish to English - use exact layout translator first
      // This is our most common translation case and needs special handling
      const isSpanishToEnglish = (actualSourceLang === "es" && targetLanguage === "en");

      // KILO CODE: Prioritize pdf_processor.py's translate_pdf for all cases first,
      // as it has better image handling.
      console.log('Attempting translation with main pdf_processor.py (translate_pdf action)...');
      const mainTranslateCommand = `${PYTHON_PATH} "${this.pythonScriptPath}" translate_pdf "${inputPdfPath}" "${outputPdfPath}" "${actualSourceLang}" "${targetLanguage}"`;
      console.log(`Executing: ${mainTranslateCommand}`);
      try {
        const startTime = Date.now();
        await execAsync(mainTranslateCommand);
        const duration = Date.now() - startTime;
        console.log(`Main PDF translation (translate_pdf) completed in ${duration}ms`);
        if (fs.existsSync(outputPdfPath) && fs.statSync(outputPdfPath).size > 0) {
          console.log(`Successfully translated PDF with main pdf_processor.py`);
          return outputPdfPath;
        }
        console.log('Main pdf_processor.py translation failed or output file is empty, proceeding to fallbacks...');
      } catch (mainTranslateError) {
        console.error('Main pdf_processor.py translation (translate_pdf) failed, proceeding to fallbacks:', mainTranslateError);
      }

      if (isSpanishToEnglish) {
        console.log('CRITICAL CASE: Spanish to English detected - trying specific fallbacks...');
        
        // EXACT LAYOUT METHOD - preserves exact text positions from original PDF
        const exactLayoutScript = path.join(process.cwd(), 'scripts', 'exact_layout_translate.py');
        const exactLayoutCommand = `${PYTHON_PATH} "${exactLayoutScript}" "${inputPdfPath}" "${outputPdfPath}" "${actualSourceLang}" "${targetLanguage}"`;
        console.log(`Executing exact layout translator: ${exactLayoutCommand}`);
        
        try {
          const startTime = Date.now();
          await execAsync(exactLayoutCommand);
          const duration = Date.now() - startTime;
          console.log(`Exact layout translation completed in ${duration}ms`);
          
          if (fs.existsSync(outputPdfPath) && fs.statSync(outputPdfPath).size > 0) {
            console.log(`Successfully translated PDF with exact layout method`);
            return outputPdfPath;
          }
          console.log('Exact layout translation failed or output file is empty, trying text-only method');
        } catch (exactLayoutError) {
          console.error('Exact layout translation failed, trying text-only method:', exactLayoutError);
        }
        
        // TEXT-ONLY METHOD
        const textOnlyScript = path.join(process.cwd(), 'scripts', 'text_only_translate.py');
        const textOnlyCommand = `${PYTHON_PATH} "${textOnlyScript}" "${inputPdfPath}" "${outputPdfPath}" "${actualSourceLang}" "${targetLanguage}"`;
        console.log(`Executing text-only translator: ${textOnlyCommand}`);
        try {
          const startTime = Date.now();
          await execAsync(textOnlyCommand);
          const duration = Date.now() - startTime;
          console.log(`Text-only translation completed in ${duration}ms`);
          if (fs.existsSync(outputPdfPath) && fs.statSync(outputPdfPath).size > 0) {
            console.log(`Successfully translated PDF with text-only method`);
            return outputPdfPath;
          }
          console.log('Text-only translation failed or output file is empty, trying pure text method');
        } catch (textOnlyError) {
          console.error('Text-only translation failed, trying pure text method:', textOnlyError);
        }
        
        // PURE TEXT METHOD
        const pureTextScript = path.join(process.cwd(), 'scripts', 'pure_text_translate.py');
        const pureTextCommand = `${PYTHON_PATH} "${pureTextScript}" "${inputPdfPath}" "${outputPdfPath}" "${actualSourceLang}" "${targetLanguage}"`;
        console.log(`Executing pure text Spanish-English translator: ${pureTextCommand}`);
        try {
          const startTime = Date.now();
          await execAsync(pureTextCommand);
          const duration = Date.now() - startTime;
          console.log(`Pure text Spanish-English translation completed in ${duration}ms`);
          if (fs.existsSync(outputPdfPath) && fs.statSync(outputPdfPath).size > 0) {
            console.log(`Successfully translated PDF with pure text method`);
            return outputPdfPath;
          }
          console.log('Pure text translation failed or output file is empty, trying extreme method');
        } catch (pureTextError) {
          console.error('Pure text translation failed, trying extreme method:', pureTextError);
        }
        
        // EXTREME METHOD
        const extremeScript = path.join(process.cwd(), 'scripts', 'extreme_translate.py');
        const extremeCommand = `${PYTHON_PATH} "${extremeScript}" "${inputPdfPath}" "${outputPdfPath}" "${actualSourceLang}" "${targetLanguage}"`;
        console.log(`Executing extreme Spanish-English translator: ${extremeCommand}`);
        try {
          const startTime = Date.now();
          await execAsync(extremeCommand);
          const duration = Date.now() - startTime;
          console.log(`Extreme Spanish-English translation completed in ${duration}ms`);
          if (fs.existsSync(outputPdfPath) && fs.statSync(outputPdfPath).size > 0) {
            console.log(`Successfully translated PDF with extreme method`);
            return outputPdfPath;
          }
          console.log('Extreme translation failed or output file is empty, trying aggressive method');
        } catch (extremeError) {
          console.error('Extreme translation failed, trying aggressive method:', extremeError);
        }
        
        // AGGRESSIVE METHOD
        const aggressiveScript = path.join(process.cwd(), 'scripts', 'aggressive_translate.py');
        const aggressiveCommand = `${PYTHON_PATH} "${aggressiveScript}" "${inputPdfPath}" "${outputPdfPath}" "${actualSourceLang}" "${targetLanguage}"`;
        console.log(`Executing aggressive Spanish-English translator: ${aggressiveCommand}`);
        try {
          const startTime = Date.now();
          await execAsync(aggressiveCommand);
          const duration = Date.now() - startTime;
          console.log(`Aggressive Spanish-English translation completed in ${duration}ms`);
          if (fs.existsSync(outputPdfPath) && fs.statSync(outputPdfPath).size > 0) {
            console.log(`Successfully translated PDF with aggressive method`);
            return outputPdfPath;
          }
          console.log('Aggressive translation failed or output file is empty, trying guaranteed method as final Spanish-English fallback.');
        } catch (aggressiveError) {
          console.error('Aggressive translation failed, trying guaranteed method as final Spanish-English fallback:', aggressiveError);
        }
      }
      
      // Fallback for non-Spanish-to-English OR if all Spanish-to-English attempts failed
      // GUARANTEED METHOD
      const guaranteedScript = path.join(process.cwd(), 'scripts', 'guaranteed_translate.py');
      console.log('Using guaranteed translation method (either as primary for non-Sp->En or fallback for Sp->En)');
      const guaranteedCommand = `${PYTHON_PATH} "${guaranteedScript}" "${inputPdfPath}" "${outputPdfPath}" "${actualSourceLang}" "${targetLanguage}"`;
      console.log(`Executing guaranteed translate command: ${guaranteedCommand}`);
      
      try {
        const startTime = Date.now();
        await execAsync(guaranteedCommand);
        const duration = Date.now() - startTime;
        console.log(`Guaranteed PDF translation completed in ${duration}ms`);
        
        // Check if output file exists and has content
        if (fs.existsSync(outputPdfPath) && fs.statSync(outputPdfPath).size > 0) {
          console.log(`Successfully translated PDF with guaranteed method`);
          return outputPdfPath;
        } else {
          console.log('Guaranteed translation failed or output file is empty, trying direct method');
        }
      } catch (guaranteedError) {
        console.error('Guaranteed translation failed, trying direct method:', guaranteedError);
      }
      
      // METHOD 2: Try the direct translation method
      const directTranslateScript = path.join(process.cwd(), 'scripts', 'direct_translate.py');
      
      console.log('Using direct translation method');
      const directCommand = `${PYTHON_PATH} "${directTranslateScript}" "${inputPdfPath}" "${outputPdfPath}" "${actualSourceLang}" "${targetLanguage}"`;
      console.log(`Executing direct translate: ${directCommand}`);
      
      try {
        const startTime = Date.now();
        await execAsync(directCommand);
        const duration = Date.now() - startTime;
        console.log(`Direct PDF translation completed in ${duration}ms`);
        
        // Check if output file exists and has content
        if (fs.existsSync(outputPdfPath) && fs.statSync(outputPdfPath).size > 0) {
          console.log(`Successfully translated PDF with direct method`);
          return outputPdfPath;
        } else {
          console.log('Direct translation failed or output file is empty, trying force method');
        }
      } catch (directError) {
        console.error('Direct translation failed, trying force method:', directError);
      }
      
      // METHOD 3: Try the aggressive force translation method
      const forceTranslateScript = path.join(process.cwd(), 'scripts', 'force_translate_pdf.py');
      
      console.log('Using aggressive force translation method');
      const forceCommand = `${PYTHON_PATH} "${forceTranslateScript}" "${inputPdfPath}" "${outputPdfPath}" "${actualSourceLang}" "${targetLanguage}"`;
      console.log(`Executing force translate: ${forceCommand}`);
      
      try {
        const startTime = Date.now();
        await execAsync(forceCommand);
        const duration = Date.now() - startTime;
        console.log(`Force PDF translation completed in ${duration}ms`);
        
        // Check if output file exists and has content
        if (fs.existsSync(outputPdfPath) && fs.statSync(outputPdfPath).size > 0) {
          console.log(`Successfully translated PDF with force method`);
          return outputPdfPath;
        } else {
          // KILO CODE: Throw error if force translation didn't produce a valid file
          const errorMessage = 'Force translation method failed to produce a valid output file.';
          console.error(errorMessage);
          throw new Error(errorMessage);
        }
      } catch (forceError) {
        // KILO CODE: Log and re-throw a specific error
        const errorMessage = `Force translation method failed: ${(forceError as Error).message}`;
        console.error(errorMessage, forceError);
        throw new Error(errorMessage);
      }
      
      // This entire block from the previous diff was redundant and caused redeclaration errors.
      // The logic for directTranslateScript and forceTranslateScript is already present above (lines 330-376)
      // and should be the final fallbacks.
    } catch (error) {
      console.error('Error translating PDF with image preservation:', error);
      throw new Error(`Failed to translate PDF with image preservation: ${error}`);
    }
  }
}
