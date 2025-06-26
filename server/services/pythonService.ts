import { exec, spawn } from 'child_process';
import util from 'util';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { TempFileManager } from '../utils/tempFileManager';

const execAsync = util.promisify(exec);
// Use the system Python path for reliability
const PYTHON_PATH = 'python';

export class PythonService {
  private tempFileManager: TempFileManager;
  private pythonScriptPath: string;
  private robustPdfTranslatorPath: string;
  private simplePdfTranslatorPath: string;
  private translationCache: Map<string, string>;

  constructor() {
    this.tempFileManager = new TempFileManager();
    this.pythonScriptPath = path.resolve(process.cwd(), 'scripts/pdf_processor.py');
    this.robustPdfTranslatorPath = path.resolve(process.cwd(), 'scripts/robust_pdf_translator.py');
    this.simplePdfTranslatorPath = path.resolve(process.cwd(), 'scripts/simple_pdf_translator.py');
    this.translationCache = new Map<string, string>();
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
      
      const detectedLanguage = stdout.trim();
      console.log(`Detected language (original): ${detectedLanguage || 'auto'}`);
      
      // Improved language detection with filename hints
      let language = detectedLanguage || 'auto';
      const filenameLower = pdfPath.toLowerCase();
      
      // Check for language indicators in filename
      const languageIndicators: Record<string, string[]> = {
        'es': ['spanish', 'español', 'espanol'],
        'de': ['german', 'deutsch'],
        'fr': ['french', 'français', 'francais'],
        'it': ['italian', 'italiano'],
        'pt': ['portuguese', 'português', 'portugues'],
        'ja': ['japanese', '日本語'],
        'zh': ['chinese', '中文'],
        'ru': ['russian', 'русский'],
        'ar': ['arabic', 'العربية'],
        'hi': ['hindi', 'हिंदी'],
        'ko': ['korean', '한국어'],
        'nl': ['dutch', 'nederlands'],
        'pl': ['polish', 'polski'],
        'tr': ['turkish', 'türkçe'],
        'sv': ['swedish', 'svenska'],
        'en': ['english']
      };
      
      // Check if filename contains language indicators
      for (const [langCode, indicators] of Object.entries(languageIndicators)) {
        if (indicators.some(indicator => filenameLower.includes(indicator))) {
          language = langCode;
          console.log(`FILENAME HINT: Detected ${langCode} from filename: ${pdfPath}`);
          break;
        }
      }
      
      // Handle special cases
      if (language === 'ca') {
        // Catalan is often confused with Spanish
        language = 'es';
        console.log(`OVERRIDE: Detected as Catalan (ca), treating as Spanish (es) for better translation`);
      } else if (language === 'auto' || !language) {
        // If language detection failed, keep it as auto for the translator to auto-detect
        language = 'auto';
        console.log(`Using auto-detection since language couldn't be determined reliably`);
      }
      
      console.log(`Final language detection: ${language}`);
      return language;
    } catch (error) {
      console.error('Error detecting language:', error);
      // No need to access error.message here since we're just returning a default value
      return 'auto'; // Default to auto-detection on error
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
      const errorMessage = error instanceof Error 
        ? error.message 
        : 'Unknown error occurred';
      throw new Error(`OCR extraction failed: ${errorMessage}`);
    }
  }

  /**
   * Map language codes to ones supported by Google Translator
   * 
   * Note: The deep_translator library expects ISO 639-1 codes directly,
   * not the full language names as previously thought.
   */
  private mapLanguageCode(code: string): string {
    if (!code) return 'auto';
    
    // Convert to lowercase for consistency
    const lowerCode = code.toLowerCase();
    
    // Special cases and normalizations
    const specialCases: Record<string, string> = {
      'auto': 'auto',
      'zh': 'zh-cn',
      'zh-hans': 'zh-cn',
      'zh-hant': 'zh-tw',
      'iw': 'he',      // Hebrew alternate code
      'jw': 'jv',      // Javanese
      'nb': 'no',      // Norwegian Bokmål
      'nn': 'no',      // Norwegian Nynorsk
      'fil': 'tl',     // Filipino
      'he': 'he',      // Hebrew
    };
    
    // Return special case or the original code (lowercase)
    return specialCases[lowerCode] || lowerCode;
  }

  /**
   * Translates text from source language to target language with optimized chunking
   * and multiple fallback mechanisms for reliability
   */
  async translateText(
    text: string, 
    sourceLanguage: string, 
    targetLanguage: string
  ): Promise<string> {
    try {
      if (!text || text.trim() === '') {
        return '';
      }
      
      // Don't translate if languages are the same
      if (sourceLanguage === targetLanguage) {
        console.log('Source and target languages are the same, skipping translation');
        return text;
      }
      
      // Handle special cases but respect the detected language
      let actualSourceLang = sourceLanguage;
      
      // Only override Catalan to Spanish as they're very similar
      if (sourceLanguage === 'ca') {
        actualSourceLang = 'es';
        console.log(`OVERRIDE: Changing source language from Catalan (ca) to Spanish (es) for better translation`);
      }
      
      // Clean up language codes for compatibility with Google Translator
      const sourceCode = this.mapLanguageCode(actualSourceLang);
      const targetCode = this.mapLanguageCode(targetLanguage);
      
      console.log(`Translating text from ${actualSourceLang} (${sourceCode}) to ${targetLanguage} (${targetCode})...`);
      
      // Check if we have this translation in cache
      const cacheKey = `${sourceCode}:${targetCode}:${this.hashText(text)}`;
      if (this.translationCache.has(cacheKey)) {
        console.log('Found translation in memory cache');
        return this.translationCache.get(cacheKey) || text;
      }
      
      const inputTextPath = this.tempFileManager.createTempFile('to-translate', '.txt');
      const outputTextPath = this.tempFileManager.createTempFile('translated', '.txt');
      
      // Write text to temporary file with UTF-8 encoding
      fs.writeFileSync(inputTextPath, text, 'utf8');
      
      // Run translation using Python script with mapped language codes
      const command = `${PYTHON_PATH} "${this.pythonScriptPath}" translate "${inputTextPath}" "${outputTextPath}" "${sourceCode}" "${targetCode}"`;
      console.log(`Executing: ${command}`);
      
      let translationSucceeded = false;
      let translatedText = '';
      
      // First attempt with specified source language
      try {
        const { stdout, stderr } = await execAsync(command);
        if (stderr) {
          console.error('Translation stderr:', stderr);
        }
        if (stdout) {
          console.log('Translation stdout:', stdout);
        }
        
        if (fs.existsSync(outputTextPath)) {
          translatedText = fs.readFileSync(outputTextPath, 'utf8');
          
          // Check if translation actually happened
          translationSucceeded = translatedText !== text && translatedText.trim().length > 0;
          
          if (translationSucceeded) {
            console.log('Translation successful on first attempt');
          } else {
            console.log('Translation output is identical to input or empty');
          }
        }
      } catch (execError) {
        console.error('Translation command failed:', execError);
        // Continue to fallback methods
      }
      
      // If first attempt failed, try with auto-detection
      if (!translationSucceeded) {
        console.log('First translation attempt failed, trying with auto-detection');
        
        const retryCommand = `${PYTHON_PATH} "${this.pythonScriptPath}" translate "${inputTextPath}" "${outputTextPath}" "auto" "${targetCode}"`;
        console.log(`Executing retry with auto-detection: ${retryCommand}`);
        
        try {
          const { stdout, stderr } = await execAsync(retryCommand);
          if (stderr) {
            console.error('Retry translation stderr:', stderr);
          }
          if (stdout) {
            console.log('Retry translation stdout:', stdout);
          }
          
          if (fs.existsSync(outputTextPath)) {
            const retryText = fs.readFileSync(outputTextPath, 'utf8');
            
            if (retryText !== text && retryText.trim().length > 0) {
              console.log('Retry with auto-detection succeeded!');
              translatedText = retryText;
              translationSucceeded = true;
            } else {
              console.log('Retry with auto-detection also failed');
            }
          }
        } catch (retryError) {
          console.error('Retry translation command failed:', retryError);
          // Continue to next fallback
        }
      }
      
      // If both attempts failed and text is long, try splitting it into paragraphs
      if (!translationSucceeded && text.length > 500) {
        console.log('Both translation attempts failed, trying paragraph-by-paragraph translation');
        
        try {
          // Split text into paragraphs
          const paragraphs = text.split(/\n\s*\n/);
          const translatedParagraphs: string[] = [];
          
          // Translate each paragraph separately
          for (let i = 0; i < paragraphs.length; i++) {
            const paragraph = paragraphs[i].trim();
            if (!paragraph) {
              translatedParagraphs.push('');
              continue;
            }
            
            console.log(`Translating paragraph ${i+1}/${paragraphs.length} (${paragraph.length} chars)`);
            
            // Write paragraph to temp file
            fs.writeFileSync(inputTextPath, paragraph, 'utf8');
            
            // Try translation with auto-detection for this paragraph
            const paraCommand = `${PYTHON_PATH} "${this.pythonScriptPath}" translate "${inputTextPath}" "${outputTextPath}" "auto" "${targetCode}"`;
            
            try {
              await execAsync(paraCommand);
              
              if (fs.existsSync(outputTextPath)) {
                const translatedPara = fs.readFileSync(outputTextPath, 'utf8');
                
                if (translatedPara && translatedPara.trim() && translatedPara !== paragraph) {
                  translatedParagraphs.push(translatedPara);
                } else {
                  // If translation failed, keep original paragraph
                  translatedParagraphs.push(paragraph);
                }
              } else {
                translatedParagraphs.push(paragraph);
              }
            } catch (paraError) {
              console.error(`Error translating paragraph ${i+1}:`, paraError);
              translatedParagraphs.push(paragraph);
            }
          }
          
          // Combine translated paragraphs
          translatedText = translatedParagraphs.join('\n\n');
          translationSucceeded = translatedText !== text && translatedText.trim().length > 0;
          
          if (translationSucceeded) {
            console.log('Paragraph-by-paragraph translation succeeded');
          }
        } catch (splitError) {
          console.error('Paragraph-by-paragraph translation failed:', splitError);
        }
      }
      
      // Final result - use translated text if any method succeeded, otherwise return original
      const finalText = translationSucceeded ? translatedText : text;
      
      // Cache the result
      this.translationCache.set(cacheKey, finalText);
      
      return finalText;
    } catch (error) {
      console.error('Error translating text:', error);
      const errorMessage = error instanceof Error 
        ? error.message 
        : 'Unknown error occurred';
      
      // Even on error, return the original text rather than throwing
      // This ensures the user gets at least the original content
      console.log('Returning original text due to translation error');
      return text;
    }
  }
  
  /**
   * Creates a hash of the text for caching purposes
   */
  private hashText(text: string): string {
    return crypto.createHash('md5').update(text).digest('hex');
  }

  /**
   * Translates a PDF file while preserving images and layout
   */
  async translatePdfWithImages(
    inputPath: string, 
    outputPath: string, 
    sourceLanguage: string, 
    targetLanguage: string
  ): Promise<boolean> {
    try {
      console.log(`Translating PDF with image preservation from ${sourceLanguage} to ${targetLanguage}`);
      
      // Don't translate if languages are the same
      if (sourceLanguage === targetLanguage) {
        console.log('Source and target languages are the same, copying file');
        fs.copyFileSync(inputPath, outputPath);
        return true;
      }
      
      // Clean up language codes for compatibility with Google Translator
      const sourceCode = this.mapLanguageCode(sourceLanguage);
      const targetCode = this.mapLanguageCode(targetLanguage);
      
      // Try the robust PDF translator first
      const robustCommand = `${PYTHON_PATH} "${this.robustPdfTranslatorPath}" "${inputPath}" "${outputPath}" "${sourceCode}" "${targetCode}"`;
      console.log(`Executing robust PDF translation: ${robustCommand}`);
      
      try {
        // Set a timeout for the robust translation (3 minutes)
        const timeoutMs = 3 * 60 * 1000;
        const execPromise = execAsync(robustCommand);
        
        // Create a timeout promise
        const timeoutPromise = new Promise<{stdout: string, stderr: string}>((_, reject) => {
          setTimeout(() => {
            reject(new Error('PDF translation timed out after 3 minutes'));
          }, timeoutMs);
        });
        
        // Race the execution against the timeout
        const { stdout, stderr } = await Promise.race([execPromise, timeoutPromise]);
        
        if (stderr) {
          console.error('PDF translation stderr:', stderr);
        }
        if (stdout) {
          console.log('PDF translation stdout:', stdout);
        }
        
        // Check if the output file was created
        if (fs.existsSync(outputPath)) {
          console.log('Robust PDF translation completed successfully');
          return true;
        } else {
          throw new Error('Robust PDF translation failed to produce output file');
        }
      } catch (execError) {
        console.error('Robust PDF translation failed:', execError);
        
        // Fall back to the simple PDF translator
        console.log('Falling back to simple PDF translator...');
        
        const simpleCommand = `${PYTHON_PATH} "${this.simplePdfTranslatorPath}" "${inputPath}" "${outputPath}" "${sourceCode}" "${targetCode}"`;
        console.log(`Executing simple PDF translation: ${simpleCommand}`);
        
        try {
          const { stdout, stderr } = await execAsync(simpleCommand);
          if (stderr) {
            console.error('Simple PDF translation stderr:', stderr);
          }
          if (stdout) {
            console.log('Simple PDF translation stdout:', stdout);
          }
          
          // Check if the output file was created
          if (fs.existsSync(outputPath)) {
            console.log('Simple PDF translation completed successfully');
            return true;
          } else {
            throw new Error('Simple PDF translation also failed to produce output file');
          }
        } catch (fallbackError) {
          console.error('Simple PDF translation also failed:', fallbackError);
          
          // Last resort: try the original PDF processor
          console.log('Trying original PDF processor as last resort...');
          
          const originalCommand = `${PYTHON_PATH} "${this.pythonScriptPath}" translate_pdf "${inputPath}" "${outputPath}" "${sourceCode}" "${targetCode}"`;
          console.log(`Executing original PDF translation: ${originalCommand}`);
          
          try {
            const { stdout, stderr } = await execAsync(originalCommand);
            if (stderr) {
              console.error('Original PDF translation stderr:', stderr);
            }
            if (stdout) {
              console.log('Original PDF translation stdout:', stdout);
            }
            
            // Check if the output file was created
            if (fs.existsSync(outputPath)) {
              console.log('Original PDF translation completed successfully');
              return true;
            } else {
              throw new Error('All PDF translation methods failed to produce output file');
            }
          } catch (originalError) {
            console.error('All PDF translation methods failed:', originalError);
            const errorMessage = originalError instanceof Error 
              ? originalError.message 
              : 'Unknown error occurred';
            throw new Error(`All PDF translation methods failed: ${errorMessage}`);
          }
        }
      }
    } catch (error) {
      console.error('Error translating PDF with images:', error);
      const errorMessage = error instanceof Error 
        ? error.message 
        : 'Unknown error occurred';
      throw new Error(`PDF translation failed: ${errorMessage}`);
    }
  }
}
