#!/usr/bin/env python3

import os
import sys
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
import langdetect
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from deep_translator import GoogleTranslator, MyMemoryTranslator, LingueeTranslator, DeeplTranslator
import io
import re
import argparse
import tempfile
import uuid
import fitz  # PyMuPDF - for preserving images in PDFs
import concurrent.futures
import time
import json
import hashlib
from functools import lru_cache

# Configure pytesseract path (adjust if needed)
# pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

def setup_args():
    """Set up command line arguments"""
    parser = argparse.ArgumentParser(description='PDF Processing Tool')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Extract text command
    extract_parser = subparsers.add_parser('extract', help='Extract text from PDF')
    extract_parser.add_argument('pdf_path', help='Path to PDF file')
    extract_parser.add_argument('output_path', help='Path to output text file')
    
    # OCR command
    ocr_parser = subparsers.add_parser('ocr', help='Extract text using OCR')
    ocr_parser.add_argument('pdf_path', help='Path to PDF file')
    ocr_parser.add_argument('output_path', help='Path to output text file')
    
    # Check OCR needed command
    check_ocr_parser = subparsers.add_parser('check_ocr', help='Check if PDF needs OCR')
    check_ocr_parser.add_argument('pdf_path', help='Path to PDF file')
    
    # Detect language command
    detect_lang_parser = subparsers.add_parser('detect_language', help='Detect PDF language')
    detect_lang_parser.add_argument('pdf_path', help='Path to PDF file')
    
    # Translate command
    translate_parser = subparsers.add_parser('translate', help='Translate text')
    translate_parser.add_argument('input_path', help='Path to input text file')
    translate_parser.add_argument('output_path', help='Path to output text file')
    translate_parser.add_argument('source_lang', help='Source language code')
    translate_parser.add_argument('target_lang', help='Target language code')
    
    # Create PDF command
    create_pdf_parser = subparsers.add_parser('create_pdf', help='Create PDF from text')
    create_pdf_parser.add_argument('text_path', help='Path to text file')
    create_pdf_parser.add_argument('pdf_path', help='Path to output PDF file')
    create_pdf_parser.add_argument('language', help='Language code')
    
    # Create dual language PDF command
    dual_pdf_parser = subparsers.add_parser('create_dual_pdf', help='Create dual language PDF')
    dual_pdf_parser.add_argument('original_text_path', help='Path to original text file')
    dual_pdf_parser.add_argument('translated_text_path', help='Path to translated text file')
    dual_pdf_parser.add_argument('pdf_path', help='Path to output PDF file')
    dual_pdf_parser.add_argument('source_lang', help='Source language code')
    dual_pdf_parser.add_argument('target_lang', help='Target language code')
    
    # Translate PDF with images
    translate_pdf_parser = subparsers.add_parser('translate_pdf', help='Translate PDF while preserving images')
    translate_pdf_parser.add_argument('input_path', help='Path to input PDF file')
    translate_pdf_parser.add_argument('output_path', help='Path to output PDF file')
    translate_pdf_parser.add_argument('source_lang', help='Source language code')
    translate_pdf_parser.add_argument('target_lang', help='Target language code')
    
    return parser.parse_args()

def extract_text(pdf_path, output_path):
    """Extract text from a PDF file with optimizations for speed"""
    text = ""
    
    try:
        print(f"Fast text extraction from {pdf_path}")
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            # Get number of pages
            num_pages = len(reader.pages)
            print(f"PDF has {num_pages} pages")
            
            # FAST MODE: Only process a subset of pages for instant results
            # For large documents, we'll sample pages from the beginning, middle and end
            pages_to_extract = []
            
            if num_pages <= 10:
                # For small documents, process all pages
                pages_to_extract = list(range(num_pages))
                print(f"Processing all {num_pages} pages")
            else:
                # For larger documents, take a sample
                # First 3 pages
                pages_to_extract.extend(range(min(3, num_pages)))
                
                # Two from the middle
                if num_pages > 6:
                    middle = num_pages // 2
                    pages_to_extract.extend([middle-1, middle])
                
                # Last 2 pages
                if num_pages > 4:
                    pages_to_extract.extend([num_pages-2, num_pages-1])
                    
                print(f"Processing sample of {len(pages_to_extract)} pages from {num_pages} total pages")
            
            # Extract text from selected pages
            for page_num in pages_to_extract:
                page = reader.pages[page_num]
                extracted = page.extract_text()
                if page_num > 0 and page_num not in [num_pages-1, num_pages-2]:
                    text += f"\n\n[Page {page_num+1}]\n\n"
                text += extracted + "\n\n"
            
            # Add note about fast mode
            if num_pages > 10:
                text += "\n\n[NOTE: This is a fast preview translation. Only selected pages were processed.]\n\n"
                
        # Write text to output file
        with open(output_path, 'w', encoding='utf-8') as output_file:
            output_file.write(text)
        
        print(f"Text extraction completed, saved to {output_path}")    
        return True
    except Exception as e:
        print(f"Error extracting text: {e}", file=sys.stderr)
        return False

def extract_text_with_ocr(pdf_path, output_path):
    """Extract text from a PDF file using OCR with improved quality and speed balance"""
    try:
        print(f"Starting OCR text extraction for {pdf_path}")
        text = ""
        
        # Use higher DPI for better OCR quality
        # 300 DPI is a good balance between quality and speed
        images = convert_from_path(pdf_path, dpi=300)
        
        total_pages = len(images)
        print(f"PDF has {total_pages} pages to process")
        
        # Determine how many pages to process based on document size
        pages_to_process = []
        
        if total_pages <= 5:
            # For small documents, process all pages
            pages_to_process = list(range(total_pages))
            print(f"Processing all {total_pages} pages with OCR")
        elif total_pages <= 20:
            # For medium documents, process first 3, middle 2, and last 2
            pages_to_process = list(range(min(3, total_pages)))  # First 3 pages
            
            if total_pages > 6:
                middle = total_pages // 2
                pages_to_process.extend([middle-1, middle])  # 2 middle pages
            
            if total_pages > 2:
                pages_to_process.extend([total_pages-2, total_pages-1])  # Last 2 pages
                
            print(f"Processing {len(pages_to_process)} pages with OCR")
        else:
            # For larger documents, process first 3, every 5th page, and last 2
            pages_to_process = list(range(min(3, total_pages)))  # First 3 pages
            
            # Add every 5th page
            for i in range(5, total_pages-2, 5):
                pages_to_process.append(i)
                
            # Add last 2 pages
            pages_to_process.extend([total_pages-2, total_pages-1])
            
            print(f"Processing {len(pages_to_process)} pages with OCR")
        
        # Remove duplicates and sort
        pages_to_process = sorted(list(set(pages_to_process)))
        
        # Process selected pages with OCR
        for idx, i in enumerate(pages_to_process):
            if i >= total_pages:
                continue
                
            image = images[i]
            print(f"OCR processing page {i+1}/{total_pages} ({idx+1}/{len(pages_to_process)})")
            
            # Preprocess image for better OCR results
            try:
                # Convert to numpy array
                import numpy as np
                from PIL import Image, ImageEnhance
                
                # Enhance image contrast
                enhancer = ImageEnhance.Contrast(image)
                enhanced_image = enhancer.enhance(1.5)  # Increase contrast by 50%
                
                # Sharpen image
                enhancer = ImageEnhance.Sharpness(enhanced_image)
                enhanced_image = enhancer.enhance(1.5)  # Increase sharpness by 50%
                
                # Use balanced OCR settings for better accuracy
                # --oem 1: LSTM engine only (more accurate)
                # --psm 3: Auto page segmentation
                config = '--oem 1 --psm 3'
                
                # Perform OCR on enhanced image
                page_text = pytesseract.image_to_string(enhanced_image, config=config)
            except Exception as preprocess_error:
                print(f"Image preprocessing failed: {preprocess_error}, using original image")
                # Fallback to original image with simpler settings
                config = '--oem 0 --psm 3'
                page_text = pytesseract.image_to_string(image, config=config)
            
            # Add page marker except for first page
            if i > 0:
                text += f"\n\n[Page {i+1}]\n\n"
            
            text += page_text + "\n\n"
        
        # Add note about partial processing if we skipped pages
        if len(pages_to_process) < total_pages:
            text += "\n\n[NOTE: This is a partial translation. Only selected pages were processed using OCR.]\n\n"
        
        # Clean up the extracted text
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Fix common OCR errors
        text = text.replace('|', 'I')  # Common OCR error: pipe instead of capital I
        text = text.replace('0', 'O')  # Common OCR error: zero instead of capital O
        text = text.replace('1', 'l')  # Common OCR error: one instead of lowercase L
        
        # Write text to output file
        with open(output_path, 'w', encoding='utf-8') as output_file:
            output_file.write(text)
        
        print(f"OCR extraction completed, saved to {output_path}")
        return True
    except Exception as e:
        print(f"Error performing OCR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

def needs_ocr(pdf_path):
    """Check if a PDF needs OCR by examining if it has extractable text"""
    try:
        # Try multiple extraction methods to determine if OCR is needed
        
        # Method 1: PyPDF2 extraction
        pypdf_text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Check a sample of pages (up to 5)
                pages_to_check = min(5, len(reader.pages))
                
                for i in range(pages_to_check):
                    page = reader.pages[i]
                    text = page.extract_text()
                    pypdf_text += text
        except Exception as e:
            print(f"PyPDF2 extraction error: {e}")
        
        # Method 2: PyMuPDF (fitz) extraction
        fitz_text = ""
        try:
            pdf_document = fitz.open(pdf_path)
            
            # Check a sample of pages (up to 5)
            pages_to_check = min(5, len(pdf_document))
            
            for i in range(pages_to_check):
                page = pdf_document[i]
                fitz_text += page.get_text()
                
            pdf_document.close()
        except Exception as e:
            print(f"PyMuPDF extraction error: {e}")
        
        # Combine results from both methods
        total_text = pypdf_text + fitz_text
        
        # If we extracted a reasonable amount of text, OCR is likely not needed
        if len(total_text) > 200:  # Increased threshold for better detection
            print(f"PDF has extractable text ({len(total_text)} chars), OCR not needed")
            return False
            
        # If very little text was extracted, try a small OCR sample to confirm
        print(f"PDF has little extractable text ({len(total_text)} chars), checking with OCR sample")
        
        # Convert first page to image and try OCR on a small sample
        try:
            images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)
            if images:
                # Use fast OCR settings
                config = '--oem 0 --psm 3'
                sample_text = pytesseract.image_to_string(images[0], config=config)
                
                # If OCR found significant text that wasn't found by text extraction
                if len(sample_text) > 100 and len(total_text) < 50:
                    print(f"OCR sample found {len(sample_text)} chars, OCR is needed")
                    return True
        except Exception as e:
            print(f"OCR sample check error: {e}")
        
        # Default decision based on extracted text
        needs_ocr = len(total_text) < 200
        print(f"Final OCR decision: {'OCR needed' if needs_ocr else 'OCR not needed'}")
        return needs_ocr
        
    except Exception as e:
        print(f"Error checking if PDF needs OCR: {e}", file=sys.stderr)
        return True  # Default to using OCR if we can't determine

def detect_language(pdf_path):
    """Detect the language of a PDF document using multiple methods for reliability"""
    try:
        pdf_basename = os.path.basename(pdf_path)
        print(f"Detecting language for PDF: {pdf_basename}")
        
        # First check for language indicators in filename
        filename_lower = pdf_basename.lower()
        
        # Comprehensive language detection from filename
        language_indicators = {
            'es': ['spanish', 'español', 'espanol', 'castellano'],
            'fr': ['french', 'français', 'francais'],
            'de': ['german', 'deutsch', 'germanisch'],
            'it': ['italian', 'italiano'],
            'pt': ['portuguese', 'português', 'portugues'],
            'ja': ['japanese', 'japonés', 'japones', '日本語'],
            'zh': ['chinese', 'mandarin', '中文', '汉语', '漢語'],
            'ru': ['russian', 'русский', 'russkiy'],
            'ar': ['arabic', 'العربية', 'arabisch'],
            'hi': ['hindi', 'हिंदी'],
            'ko': ['korean', '한국어', 'corean'],
            'nl': ['dutch', 'nederlands', 'hollandais'],
            'pl': ['polish', 'polski', 'polaco'],
            'tr': ['turkish', 'türkçe', 'turkce'],
            'sv': ['swedish', 'svenska'],
            'en': ['english', 'inglés', 'ingles']
        }
        
        # Check filename for language indicators
        for lang_code, indicators in language_indicators.items():
            for indicator in indicators:
                if indicator in filename_lower:
                    print(f"FILENAME HINT: Detected {lang_code} from indicator '{indicator}' in filename: {pdf_basename}")
                    return lang_code
        
        # Create a temporary directory for our extraction files
        temp_dir = tempfile.mkdtemp()
        text_path = os.path.join(temp_dir, f"extract-{uuid.uuid4()}.txt")
        ocr_text_path = os.path.join(temp_dir, f"ocr-extract-{uuid.uuid4()}.txt")
        
        # Extract text using both methods to ensure we get enough content for detection
        direct_extraction_text = ""
        ocr_extraction_text = ""
        
        # Try direct extraction first
        try:
            if extract_text(pdf_path, text_path):
                with open(text_path, 'r', encoding='utf-8', errors='ignore') as file:
                    direct_extraction_text = file.read()
                print(f"Direct extraction produced {len(direct_extraction_text)} characters")
        except Exception as e:
            print(f"Direct extraction failed: {e}")
        
        # Also try OCR extraction
        try:
            extract_text_with_ocr(pdf_path, ocr_text_path)
            with open(ocr_text_path, 'r', encoding='utf-8', errors='ignore') as file:
                ocr_extraction_text = file.read()
            print(f"OCR extraction produced {len(ocr_extraction_text)} characters")
        except Exception as e:
            print(f"OCR extraction failed: {e}")
        
        # Use the text source with more content
        if len(direct_extraction_text.strip()) > len(ocr_extraction_text.strip()):
            text = direct_extraction_text
            print("Using direct extraction text for language detection")
        else:
            text = ocr_extraction_text
            print("Using OCR extraction text for language detection")
        
        # Clean up temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass
        
        if not text.strip():
            print("No text content found for language detection", file=sys.stderr)
            return "auto"  # Use auto-detection if no text was extracted
        
        # Detect language using multiple methods for reliability
        try:
            # Get a sample of the text (up to 5000 chars) for faster detection
            sample_text = text[:5000]
            
            # Dictionary of language indicators with their key words
            language_indicators = {
                'es': ['la', 'el', 'en', 'por', 'con', 'para', 'una', 'que', 'es', 'y', 'de', 'los', 'las', 'del', 'como', 'más'],
                'fr': ['le', 'la', 'les', 'des', 'un', 'une', 'et', 'est', 'pour', 'dans', 'avec', 'ce', 'cette', 'ces', 'nous', 'vous'],
                'de': ['der', 'die', 'das', 'und', 'ist', 'für', 'mit', 'ein', 'eine', 'zu', 'von', 'nicht', 'auch', 'dem', 'sich', 'auf', 'dass', 'wenn', 'werden', 'sind'],
                'it': ['il', 'la', 'i', 'le', 'un', 'una', 'e', 'è', 'per', 'con', 'che', 'di', 'non', 'sono', 'questo', 'questa'],
                'pt': ['o', 'a', 'os', 'as', 'um', 'uma', 'e', 'é', 'para', 'com', 'que', 'de', 'não', 'em', 'por', 'se'],
                'ja': ['は', 'の', 'に', 'を', 'た', 'が', 'で', 'て', 'と', 'れ', 'から', 'まで', 'です', 'ます'],
                'zh': ['的', '是', '在', '了', '和', '有', '我', '不', '这', '为', '他', '人', '你', '个'],
                'ru': ['и', 'в', 'не', 'на', 'я', 'что', 'с', 'по', 'это', 'от', 'к', 'но', 'а', 'у'],
                'nl': ['de', 'het', 'een', 'en', 'van', 'in', 'is', 'dat', 'op', 'te', 'voor', 'met', 'zijn', 'niet'],
                'en': ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'for', 'that', 'with', 'as', 'at', 'this', 'by', 'are', 'be']
            }
            
            # Count indicators for each language
            language_scores = {}
            for lang, indicators in language_indicators.items():
                score = 0
                for word in indicators:
                    # Count times each word appears as whole word with boundaries
                    count = len(re.findall(r'\b' + word + r'\b', sample_text.lower()))
                    score += count
                language_scores[lang] = score
                print(f"Language indicator score for {lang}: {score}")
            
            # Get the language with the highest score
            max_score = 0
            detected_lang = "auto"
            for lang, score in language_scores.items():
                if score > max_score:
                    max_score = score
                    detected_lang = lang
            
            # Only use word-based detection if we have a significant score
            # Lower threshold for German and other languages that might have fewer common words
            threshold = 5 if detected_lang in ['de', 'ja', 'zh', 'ru'] else 10
            
            if max_score > threshold:
                print(f"TEXT ANALYSIS: Detected {detected_lang} with score {max_score}")
                
                # Special case: If Spanish and Catalan are close, prefer Spanish
                if detected_lang == "es" and language_scores.get("ca", 0) > max_score * 0.8:
                    print("OVERRIDE: Detected text has both Spanish and Catalan indicators, using Spanish")
                    return "es"
                    
                return detected_lang
            
            # If word-based detection didn't yield a clear result, try langdetect
            print("Word-based detection inconclusive, trying langdetect")
            try:
                # Try multiple samples to improve accuracy
                samples = []
                if len(text) > 5000:
                    # Take samples from beginning, middle, and end
                    samples.append(text[:1500])
                    middle_start = len(text) // 2 - 750
                    samples.append(text[middle_start:middle_start+1500])
                    samples.append(text[-1500:])
                else:
                    samples.append(text)
                
                # Detect language for each sample
                lang_votes = {}
                for i, sample in enumerate(samples):
                    try:
                        detected = langdetect.detect(sample)
                        print(f"Langdetect sample {i+1}: {detected}")
                        lang_votes[detected] = lang_votes.get(detected, 0) + 1
                    except:
                        pass
                
                # Get the language with the most votes
                if lang_votes:
                    lang = max(lang_votes.items(), key=lambda x: x[1])[0]
                    print(f"Langdetect final result: {lang} (votes: {lang_votes})")
                else:
                    lang = "auto"
                    print("Langdetect failed on all samples")
                
                # Apply rules to fix common detection errors
                if lang == "ca":  # If detected as Catalan
                    print("OVERRIDE: Detected Catalan (ca), treating as Spanish (es) for better translation")
                    return "es"
                
                return lang
            except Exception as e:
                print(f"Langdetect failed: {e}")
                
            # If all detection methods fail, return auto
            return "auto"
            
        except Exception as e:
            print(f"Language detection failed: {e}", file=sys.stderr)
            return "auto"  # Use auto-detection if detection fails
    except Exception as e:
        print(f"Error in language detection process: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return "auto"  # Use auto-detection on error

def format_language_code(code):
    """Format language code properly for Google Translator API"""
    # The deep_translator GoogleTranslator expects ISO 639-1 codes
    
    # Special case for auto-detection
    if code == 'auto' or not code:
        return 'auto'
    
    # Map of special cases and alternate codes
    language_map = {
        # Chinese variants
        'zh-cn': 'zh-CN',
        'zh-tw': 'zh-TW',
        'zh-hans': 'zh-CN',
        'zh-hant': 'zh-TW',
        'zh': 'zh-CN',
        'chinese': 'zh-CN',
        'chinese simplified': 'zh-CN',
        'chinese traditional': 'zh-TW',
        
        # Hebrew
        'iw': 'he',
        'hebrew': 'he',
        
        # Javanese
        'jw': 'jv',
        'javanese': 'jv',
        
        # Norwegian variants
        'nb': 'no',
        'nn': 'no',
        'norwegian': 'no',
        'norwegian bokmål': 'no',
        'norwegian nynorsk': 'no',
        
        # Filipino/Tagalog
        'fil': 'tl',
        'filipino': 'tl',
        'tagalog': 'tl',
        
        # Common language names to codes
        'english': 'en',
        'spanish': 'es',
        'french': 'fr',
        'german': 'de',
        'italian': 'it',
        'portuguese': 'pt',
        'russian': 'ru',
        'japanese': 'ja',
        'korean': 'ko',
        'arabic': 'ar',
        'hindi': 'hi',
        'bengali': 'bn',
        'dutch': 'nl',
        'turkish': 'tr',
        'vietnamese': 'vi',
        'thai': 'th',
        'persian': 'fa',
        'polish': 'pl',
        'ukrainian': 'uk',
        'swedish': 'sv',
        'finnish': 'fi',
        'danish': 'da',
        'greek': 'el',
        'czech': 'cs',
        'hungarian': 'hu',
        'romanian': 'ro',
        
        # Special cases for common errors
        'auto-detect': 'auto',
        'automatic': 'auto',
        'unknown': 'auto',
        'ca': 'es',  # Treat Catalan as Spanish for better results
    }
    
    # Check if we have a special mapping
    lower_code = code.lower() if isinstance(code, str) else ''
    if lower_code in language_map:
        return language_map[lower_code]
    
    # Try to clean up the code if it contains extraneous information
    if isinstance(code, str) and len(code) > 2:
        # Try to extract a code pattern
        import re
        
        # Look for ISO 639-1 code pattern (2 letters)
        match = re.search(r'\b([a-z]{2})\b', lower_code)
        if match:
            extracted = match.group(1)
            return extracted
            
        # Look for language code with region (e.g., en-us)
        match = re.search(r'\b([a-z]{2})-([a-z]{2})\b', lower_code)
        if match:
            lang = match.group(1)
            region = match.group(2)
            
            # Special case for Chinese
            if lang == 'zh':
                if region in ['cn', 'hans']:
                    return 'zh-CN'
                elif region in ['tw', 'hk', 'hant']:
                    return 'zh-TW'
            
            # For most languages, just return the language part
            return lang
    
    # For most ISO 639-1 codes, return as is (if it's 2 characters)
    if isinstance(code, str) and len(code) == 2:
        return code.lower()
    
    # If all else fails, return auto
    print(f"Warning: Unrecognized language code '{code}', using auto-detection")
    return 'auto'


# Create a translation cache directory
CACHE_DIR = os.path.join(tempfile.gettempdir(), "pdf_translator_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_path(source_lang, target_lang):
    """Get the path to the translation cache file for the given language pair"""
    cache_filename = f"translation_cache_{source_lang}_{target_lang}.json"
    return os.path.join(CACHE_DIR, cache_filename)

def load_translation_cache(source_lang, target_lang):
    """Load the translation cache for the given language pair"""
    cache_path = get_cache_path(source_lang, target_lang)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading translation cache: {e}")
    return {}

def save_translation_cache(cache, source_lang, target_lang):
    """Save the translation cache for the given language pair"""
    cache_path = get_cache_path(source_lang, target_lang)
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving translation cache: {e}")

@lru_cache(maxsize=1000)
def translate_chunk(text, source_code, target_code, translator=None):
    """Translate a chunk of text with caching for performance and multiple fallback services"""
    if not text.strip():
        return ""
    
    # Create a hash of the text for cache lookup
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    
    # Try to get from memory cache first (lru_cache decorator)
    # If not in memory, check disk cache
    cache = load_translation_cache(source_code, target_code)
    if text_hash in cache:
        cached_result = cache[text_hash]
        if cached_result and cached_result.strip():
            return cached_result
        # If cached result is empty, continue with translation
    
    # Format language codes properly
    formatted_source = format_language_code(source_code)
    formatted_target = format_language_code(target_code)
    
    print(f"Translating with codes: source={formatted_source}, target={formatted_target}")
    
    # Clean the text to remove problematic characters
    cleaned_text = text.strip()
    
    # Skip translation for very short text (likely not meaningful content)
    if len(cleaned_text) < 2:
        return cleaned_text
    
    # Define translation services to try in order
    translation_services = [
        # 1. Google Translator with specified source
        lambda: try_google_translation(cleaned_text, formatted_source, formatted_target),
        
        # 2. Google Translator with auto detection
        lambda: try_google_translation(cleaned_text, 'auto', formatted_target),
        
        # 3. MyMemory Translator (another service)
        lambda: try_mymemory_translation(cleaned_text, formatted_source, formatted_target),
        
        # 4. MyMemory with auto detection
        lambda: try_mymemory_translation(cleaned_text, 'auto', formatted_target),
        
        # 5. Last resort - try with smaller chunks
        lambda: try_chunk_translation(cleaned_text, formatted_source, formatted_target)
    ]
    
    # Try each translation service in order
    for service_idx, translation_service in enumerate(translation_services):
        try:
            print(f"Trying translation service {service_idx + 1}/{len(translation_services)}")
            translated = translation_service()
            
            # Verify translation actually happened
            if translated and translated.strip() and translated != cleaned_text:
                print(f"Translation successful with service {service_idx + 1}")
                # Save to cache
                cache[text_hash] = translated
                save_translation_cache(cache, source_code, target_code)
                return translated
            else:
                print(f"Translation service {service_idx + 1} returned empty or unchanged text")
        except Exception as e:
            print(f"Error with translation service {service_idx + 1}: {e}")
    
    # If all translation services failed, return original text
    print("All translation services failed, returning original text")
    return cleaned_text

def try_google_translation(text, source, target):
    """Try to translate using Google Translator"""
    try:
        translator = GoogleTranslator(source=source, target=target)
        result = translator.translate(text)
        return result
    except Exception as e:
        print(f"Google translation error: {e}")
        raise

def try_mymemory_translation(text, source, target):
    """Try to translate using MyMemory Translator"""
    try:
        # MyMemory has a limit of 5000 characters per request
        if len(text) > 4900:  # Leave some margin
            # Split into smaller chunks
            chunks = []
            for i in range(0, len(text), 4000):
                chunks.append(text[i:i+4000])
            
            results = []
            for chunk in chunks:
                translator = MyMemoryTranslator(source=source, target=target)
                results.append(translator.translate(chunk))
            
            return " ".join(results)
        else:
            translator = MyMemoryTranslator(source=source, target=target)
            return translator.translate(text)
    except Exception as e:
        print(f"MyMemory translation error: {e}")
        raise

def try_chunk_translation(text, source, target):
    """Try to translate by breaking text into smaller chunks"""
    try:
        # Break text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        results = []
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            try:
                # Try Google first
                translator = GoogleTranslator(source=source, target=target)
                result = translator.translate(sentence)
                
                if result and result != sentence:
                    results.append(result)
                else:
                    # If Google fails, try MyMemory
                    translator = MyMemoryTranslator(source=source, target=target)
                    result = translator.translate(sentence)
                    results.append(result)
            except:
                # If both fail, keep original sentence
                results.append(sentence)
        
        return " ".join(results)
    except Exception as e:
        print(f"Chunk translation error: {e}")
        raise

def translate_chunks_parallel(chunks, source_code, target_code, max_workers=2):
    """Translate chunks in parallel for better performance and reliability"""
    # Format language codes properly
    formatted_source = format_language_code(source_code)
    formatted_target = format_language_code(target_code)
    
    # Don't share translator instances between threads to avoid concurrency issues
    # Each thread will create its own translator instance
    
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all translation tasks
        future_to_chunk = {
            executor.submit(translate_chunk, chunk, formatted_source, formatted_target, None): 
            i for i, chunk in enumerate(chunks)
        }
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_chunk):
            chunk_idx = future_to_chunk[future]
            try:
                result = future.result()
                if result and result.strip():
                    results.append((chunk_idx, result))
                    print(f"Completed chunk {chunk_idx+1}/{len(chunks)}")
                else:
                    print(f"Warning: Empty result for chunk {chunk_idx+1}, using original")
                    results.append((chunk_idx, chunks[chunk_idx]))
            except Exception as e:
                print(f"Error translating chunk {chunk_idx+1}: {e}")
                # Try one more time with a different approach
                try:
                    print(f"Retrying chunk {chunk_idx+1} with auto detection")
                    # Try with auto detection
                    result = translate_chunk(chunks[chunk_idx], 'auto', formatted_target, None)
                    if result and result.strip():
                        results.append((chunk_idx, result))
                        print(f"Retry successful for chunk {chunk_idx+1}")
                    else:
                        results.append((chunk_idx, chunks[chunk_idx]))
                except Exception as retry_error:
                    print(f"Retry also failed for chunk {chunk_idx+1}: {retry_error}")
                    results.append((chunk_idx, chunks[chunk_idx]))  # Use original text on error
    
    # Sort results by original chunk index
    results.sort(key=lambda x: x[0])
    
    # Check if we have results for all chunks
    if len(results) != len(chunks):
        print(f"Warning: Expected {len(chunks)} results but got {len(results)}")
        # Fill in any missing chunks with original text
        result_indices = set(idx for idx, _ in results)
        for i in range(len(chunks)):
            if i not in result_indices:
                print(f"Adding missing result for chunk {i+1}")
                results.append((i, chunks[i]))
        # Sort again after adding missing results
        results.sort(key=lambda x: x[0])
    
    return [result for _, result in results]

def translate_text(input_path, output_path, source_lang, target_lang):
    """Translate text from source language to target language with optimizations"""
    start_time = time.time()
    try:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read()
        
        # Format language codes properly
        source_code = format_language_code(source_lang)
        target_code = format_language_code(target_lang)
        
        print(f"Translating from {source_lang} ({source_code}) to {target_lang} ({target_code})")
        
        # Handle special case when source and target are the same
        if source_code == target_code and source_code != 'auto':
            print("Source and target languages are the same, skipping translation")
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(text)
            return True
        
        # Clear any existing cache for this language pair to ensure fresh translations
        try:
            cache_path = get_cache_path(source_code, target_code)
            if os.path.exists(cache_path):
                print(f"Removing existing translation cache for {source_code}->{target_code}")
                os.remove(cache_path)
        except Exception as e:
            print(f"Error clearing cache: {e}")
        
        # Process the full document for better results
        total_length = len(text)
        
        # For extremely large documents, we'll still need to sample
        if total_length <= 50000:  # 50KB threshold - process everything for most documents
            sample_text = text
            print(f"Processing full text ({total_length} characters)")
        else:
            # Take beginning (first 5000 chars)
            beginning = text[:5000]
            
            # Take some from middle (3000 chars)
            middle_start = total_length // 2 - 1500
            middle = text[middle_start:middle_start+3000] if middle_start > 0 else ""
            
            # Take end portion (2000 chars)
            end_start = max(0, total_length - 2000)
            end_portion = text[end_start:] if end_start < total_length else ""
            
            # Combine with section markers
            sample_text = beginning + "\n\n[...]\n\n" + middle + "\n\n[...]\n\n" + end_portion
            print(f"Reduced text from {total_length} to {len(sample_text)} characters for translation")
        
        # Split text into smaller chunks for more reliable translation
        MAX_CHUNK_SIZE = 1000  # Smaller chunks for better reliability
        
        # Split text into paragraphs first
        paragraphs = sample_text.split('\n\n')
        
        # Then split paragraphs into chunks if needed
        chunks = []
        for paragraph in paragraphs:
            if len(paragraph) <= MAX_CHUNK_SIZE:
                if paragraph.strip():
                    chunks.append(paragraph)
            else:
                # Split long paragraphs
                for i in range(0, len(paragraph), MAX_CHUNK_SIZE):
                    chunk = paragraph[i:i + MAX_CHUNK_SIZE]
                    if chunk.strip():
                        chunks.append(chunk)
        
        print(f"Split text into {len(chunks)} chunks for translation")
        
        # Determine optimal number of workers based on chunk count
        max_workers = min(2, len(chunks))  # Use fewer workers for reliability
        
        # Translate chunks in parallel
        print(f"Starting parallel translation with {max_workers} workers")
        translated_chunks = []
        
        # Process in smaller batches for better reliability
        batch_size = 10
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            print(f"Translating batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
            
            batch_results = translate_chunks_parallel(batch, source_code, target_code, max_workers)
            translated_chunks.extend(batch_results)
            
            # Save intermediate results
            intermediate_text = '\n\n'.join(translated_chunks)
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(intermediate_text)
            
            print(f"Saved intermediate results ({len(translated_chunks)}/{len(chunks)} chunks)")
        
        # Combine translated chunks with proper paragraph separation
        translated_text = '\n\n'.join(translated_chunks)
        
        # Write final translated text to output file
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(translated_text)
        
        elapsed_time = time.time() - start_time
        print(f"Translation completed successfully in {elapsed_time:.2f} seconds")
        return True
    except Exception as e:
        print(f"Error translating text: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        
        # Try to save whatever we've translated so far
        try:
            if 'translated_chunks' in locals() and translated_chunks:
                partial_text = '\n\n'.join(translated_chunks)
                with open(output_path, 'w', encoding='utf-8') as file:
                    file.write(partial_text)
                print(f"Saved partial translation with {len(translated_chunks)} chunks")
                return True
        except Exception as save_error:
            print(f"Error saving partial translation: {save_error}")
        
        return False

def create_pdf(text_path, pdf_path, language):
    """Create a PDF from a text file"""
    try:
        with open(text_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Create styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Justify',
            alignment=TA_JUSTIFY,
            fontName='Helvetica',
            fontSize=12,
            spaceAfter=12
        ))
        
        # Process text into paragraphs
        flowables = []
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            if paragraph.strip():
                p = Paragraph(paragraph.replace('\n', '<br/>'), styles["Justify"])
                flowables.append(p)
                flowables.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(flowables)
        
        return True
    except Exception as e:
        print(f"Error creating PDF: {e}", file=sys.stderr)
        return False

def create_dual_language_pdf(original_text_path, translated_text_path, pdf_path, source_lang, target_lang):
    """Create a dual language PDF with original and translated text side by side"""
    try:
        with open(original_text_path, 'r', encoding='utf-8') as file:
            original_text = file.read()
        
        with open(translated_text_path, 'r', encoding='utf-8') as file:
            translated_text = file.read()
        
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=72,
            bottomMargin=72
        )
        
        # Create styles
        styles = getSampleStyleSheet()
        title_style = styles["Heading1"]
        
        lang_header_style = styles["Heading2"]
        lang_header_style.fontSize = 14
        
        text_style = ParagraphStyle(
            name='Text',
            fontName='Helvetica',
            fontSize=10,
            spaceAfter=10
        )
        
        # Process text into paragraphs
        flowables = []
        
        # Title
        flowables.append(Paragraph("Dual Language Document", title_style))
        flowables.append(Spacer(1, 12))
        
        # Split texts into paragraphs
        original_paragraphs = original_text.split('\n\n')
        translated_paragraphs = translated_text.split('\n\n')
        
        # Make sure both lists have the same length
        max_length = max(len(original_paragraphs), len(translated_paragraphs))
        original_paragraphs.extend([''] * (max_length - len(original_paragraphs)))
        translated_paragraphs.extend([''] * (max_length - len(translated_paragraphs)))
        
        # Get language names
        source_lang_name = get_language_name(source_lang)
        target_lang_name = get_language_name(target_lang)
        
        # Add language headers
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        
        header_data = [[f"Original ({source_lang_name})", f"Translation ({target_lang_name})"]]
        header_table = Table(header_data, colWidths=[doc.width/2-10]*2)
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (1, 0), 8),
            ('TOPPADDING', (0, 0), (1, 0), 8),
            ('BOX', (0, 0), (1, 0), 1, colors.black),
            ('GRID', (0, 0), (1, 0), 1, colors.black)
        ]))
        flowables.append(header_table)
        flowables.append(Spacer(1, 12))
        
        # Add paragraphs side by side
        for i in range(max_length):
            if original_paragraphs[i].strip() or translated_paragraphs[i].strip():
                orig_p = original_paragraphs[i].replace('\n', '<br/>')
                trans_p = translated_paragraphs[i].replace('\n', '<br/>')
                
                data = [[Paragraph(orig_p, text_style), Paragraph(trans_p, text_style)]]
                t = Table(data, colWidths=[doc.width/2-10]*2)
                t.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (1, 0), 'TOP'),
                    ('GRID', (0, 0), (1, 0), 0.5, colors.grey),
                    ('LEFTPADDING', (0, 0), (1, 0), 6),
                    ('RIGHTPADDING', (0, 0), (1, 0), 6),
                    ('TOPPADDING', (0, 0), (1, 0), 6),
                    ('BOTTOMPADDING', (0, 0), (1, 0), 6)
                ]))
                flowables.append(t)
                flowables.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(flowables)
        
        return True
    except Exception as e:
        print(f"Error creating dual language PDF: {e}", file=sys.stderr)
        return False

def get_language_name(lang_code):
    """Convert language code to full name"""
    language_names = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ja': 'Japanese',
        'zh': 'Chinese',
        'ru': 'Russian',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'nl': 'Dutch',
        'ko': 'Korean',
        'tr': 'Turkish',
        'sv': 'Swedish',
        'pl': 'Polish',
        'auto': 'Auto-detected'
    }
    return language_names.get(lang_code, lang_code.capitalize())

def translate_pdf_with_images(input_pdf_path, output_pdf_path, source_lang, target_lang):
    """Translate a PDF while preserving images and layout with optimized performance"""
    start_time = time.time()
    try:
        print(f"Translating PDF with image preservation from {source_lang} to {target_lang}")
        
        # Format language codes properly
        source_code = format_language_code(source_lang)
        target_code = format_language_code(target_lang)
        
        print(f"Using language codes: {source_code} to {target_code}")
        
        # If source and target are the same, just copy the file
        if source_code == target_code and source_code != 'auto':
            print("Source and target languages are the same, copying file")
            import shutil
            shutil.copy(input_pdf_path, output_pdf_path)
            return True
            
        # Clear any existing cache for this language pair to ensure fresh translations
        # This helps avoid issues with stale or incorrect translations
        try:
            cache_path = get_cache_path(source_code, target_code)
            if os.path.exists(cache_path):
                print(f"Removing existing translation cache for {source_code}->{target_code}")
                os.remove(cache_path)
        except Exception as e:
            print(f"Error clearing cache: {e}")
        
        # Load fresh translation cache
        translation_cache = load_translation_cache(source_code, target_code)
        print(f"Loaded translation cache with {len(translation_cache)} entries")

        # Create a mapping of original text to translated text for all blocks
        translation_mapping = {}
        
        # Open the PDF with PyMuPDF
        pdf_document = fitz.open(input_pdf_path)
        output_document = fitz.open()
        
        # Ensure standard fonts are available in the output document
        try:
            # Create a temporary page to embed fonts
            temp_page = output_document.new_page()
            
            # Try to embed standard fonts by using them
            for std_font in ["Helvetica", "Times-Roman", "Courier"]:
                try:
                    temp_page.insert_text((50, 50), f"Font test: {std_font}", fontname=std_font, fontsize=1)
                except Exception as font_error:
                    print(f"Could not embed font {std_font}: {font_error}")
            
            # Delete the temporary page
            output_document.delete_page(0)
        except Exception as font_embed_error:
            print(f"Error pre-embedding fonts: {font_embed_error}")
        
        # Collect all text blocks from all pages first
        all_text_blocks = []
        page_blocks_map = {}
        
        print("Phase 1: Collecting all text blocks from document...")
        for page_idx, page in enumerate(pdf_document):
            page_blocks = []
            
            try:
                # Try multiple text extraction methods for better results
                # First try with blocks
                text_blocks = page.get_text("blocks")
                
                # If no blocks found or very few, try with words
                if len(text_blocks) < 3:
                    print(f"Few blocks found on page {page_idx+1}, trying word extraction")
                    words = page.get_text("words")
                    
                    # Group words into lines
                    if words:
                        # Sort words by y-coordinate (top to bottom)
                        words.sort(key=lambda w: (w[3], w[0]))  # Sort by y0, then x0
                        
                        current_line_y = words[0][3]
                        line_words = []
                        lines = []
                        
                        # Group words into lines based on y-coordinate
                        for word in words:
                            if abs(word[3] - current_line_y) < 12:  # If on same line (within 12 points)
                                line_words.append(word)
                            else:
                                # New line
                                if line_words:
                                    lines.append(line_words)
                                line_words = [word]
                                current_line_y = word[3]
                        
                        # Add the last line
                        if line_words:
                            lines.append(line_words)
                        
                        # Group lines into paragraphs
                        paragraphs = []
                        current_para = []
                        
                        for line in lines:
                            if current_para and (line[0][3] - current_para[-1][-1][3]) > 20:
                                # If vertical gap is large, start a new paragraph
                                paragraphs.append(current_para)
                                current_para = [line]
                            else:
                                current_para.append(line)
                        
                        # Add the last paragraph
                        if current_para:
                            paragraphs.append(current_para)
                        
                        # Create blocks from paragraphs
                        for para_idx, para in enumerate(paragraphs):
                            # Calculate bounding box
                            x0 = min(w[0] for line in para for w in line)
                            y0 = min(w[1] for line in para for w in line)
                            x1 = max(w[2] for line in para for w in line)
                            y1 = max(w[3] for line in para for w in line)
                            
                            # Combine text
                            text = ""
                            for line in para:
                                line_text = " ".join(w[4] for w in line)
                                text += line_text + "\n"
                            
                            if text.strip() and len(text.strip()) >= 2:
                                block_data = [x0, y0, x1, y1, text, para_idx, 0]
                                page_blocks.append(block_data)
                                all_text_blocks.append(text)
                
                # If still no blocks, try dict extraction
                if len(page_blocks) == 0:
                    dict_text = page.get_text("dict")
                    if "blocks" in dict_text:
                        dict_blocks = dict_text["blocks"]
                        
                        # Convert dict blocks to the format expected by the block processing code
                        for block in dict_blocks:
                            if block.get("type") == 0:  # text block
                                text = ""
                                for line in block.get("lines", []):
                                    for span in line.get("spans", []):
                                        text += span.get("text", "")
                                    text += "\n"
                                
                                if text.strip() and len(text.strip()) >= 2:
                                    # Create a block in the format [x0, y0, x1, y1, text, block_no, block_type]
                                    block_data = [
                                        block["bbox"][0], block["bbox"][1], 
                                        block["bbox"][2], block["bbox"][3],
                                        text, len(page_blocks), 0
                                    ]
                                    page_blocks.append(block_data)
                                    all_text_blocks.append(text)
                
                # If we still have standard blocks from the first extraction, process them
                if text_blocks and len(page_blocks) == 0:
                    for block in text_blocks:
                        if block[6] == 0 and len(block[4].strip()) >= 2:  # Text block with meaningful content
                            page_blocks.append(block)
                            all_text_blocks.append(block[4])
            except Exception as e:
                print(f"Error extracting blocks from page {page_idx+1}: {e}")
            
            page_blocks_map[page_idx] = page_blocks
            print(f"Collected {len(page_blocks)} text blocks from page {page_idx+1}/{len(pdf_document)}")
        
        # Deduplicate text blocks to minimize translation requests
        unique_texts = list(set(all_text_blocks))
        print(f"Found {len(all_text_blocks)} total blocks, {len(unique_texts)} unique text blocks to translate")
        
        # Check cache for existing translations
        texts_to_translate = []
        for text in unique_texts:
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            if text_hash not in translation_cache:
                texts_to_translate.append(text)
        
        print(f"After cache check: {len(texts_to_translate)} blocks need translation")
        
        # Phase 2: Translate all unique text blocks in parallel
        if texts_to_translate:
            print("Phase 2: Translating unique text blocks in parallel...")
            
            # Split into smaller chunks for more reliable translation
            chunk_size = 5  # Smaller chunk size for better reliability
            
            # Create batches of texts
            batches = []
            for i in range(0, len(texts_to_translate), chunk_size):
                batch = texts_to_translate[i:i+chunk_size]
                batches.append(batch)
            
            print(f"Split {len(texts_to_translate)} texts into {len(batches)} batches for parallel translation")
            
            # Process batches in parallel with fewer workers for reliability
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                # Submit translation tasks
                future_to_batch = {
                    executor.submit(
                        lambda b: [(text, translate_chunk(text, source_code, target_code)) for text in b],
                        batch
                    ): batch_idx for batch_idx, batch in enumerate(batches)
                }
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_batch):
                    batch_idx = future_to_batch[future]
                    try:
                        results = future.result()
                        for text, translated in results:
                            if translated and translated.strip():
                                translation_mapping[text] = translated
                                # Also update cache
                                text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
                                translation_cache[text_hash] = translated
                            else:
                                print(f"Warning: Empty translation result for text: {text[:30]}...")
                                translation_mapping[text] = text  # Use original if translation failed
                        
                        print(f"Completed batch {batch_idx+1}/{len(batches)}")
                    except Exception as e:
                        print(f"Error processing batch {batch_idx+1}: {e}")
                        # For failed batches, try translating each text individually
                        try:
                            batch = batches[batch_idx]
                            print(f"Retrying batch {batch_idx+1} texts individually")
                            for text in batch:
                                try:
                                    translated = translate_chunk(text, source_code, target_code)
                                    if translated and translated.strip():
                                        translation_mapping[text] = translated
                                        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
                                        translation_cache[text_hash] = translated
                                    else:
                                        translation_mapping[text] = text
                                except Exception as text_error:
                                    print(f"Error translating individual text: {text_error}")
                                    translation_mapping[text] = text
                        except Exception as retry_error:
                            print(f"Error in batch retry: {retry_error}")
            
            # Save updated cache
            save_translation_cache(translation_cache, source_code, target_code)
        else:
            print("All text blocks found in cache, skipping translation phase")
        
        # Add cache entries to translation mapping
        for text in unique_texts:
            if text not in translation_mapping:
                text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
                if text_hash in translation_cache:
                    translation_mapping[text] = translation_cache[text_hash]
                else:
                    # Fallback if somehow not in cache
                    translation_mapping[text] = text
        
        # Phase 3: Create output PDF with translations
        print("Phase 3: Creating output PDF with translations...")
        for page_idx, page in enumerate(pdf_document):
            print(f"Processing page {page_idx+1}/{len(pdf_document)}")
            
            # Create a new page with the same dimensions
            new_page = output_document.new_page(width=page.rect.width, height=page.rect.height)
            
            # First, copy the entire page as background (preserves all images and layout)
            new_page.show_pdf_page(
                new_page.rect,
                pdf_document,
                page_idx,
                clip=None,
                keep_proportion=True,
                overlay=False,
                oc=0,
                rotate=0
            )
            
            # Process text blocks for this page
            page_blocks = page_blocks_map.get(page_idx, [])
            
            # If no blocks were found, try to extract text directly from the page
            if len(page_blocks) == 0:
                print(f"No text blocks found on page {page_idx+1}, trying direct text extraction")
                try:
                    # Get all text from the page
                    page_text = page.get_text()
                    if page_text and len(page_text.strip()) > 10:
                        # Create a single block covering the whole page
                        page_blocks = [[
                            10,  # x0 - leave margin
                            10,  # y0 - leave margin
                            page.rect.width - 10,  # x1
                            page.rect.height - 10,  # y1
                            page_text,
                            0,  # block number
                            0   # block type (text)
                        ]]
                        print(f"Created a single block with {len(page_text)} characters")
                except Exception as e:
                    print(f"Error extracting text directly from page {page_idx+1}: {e}")
            
            # Process each text block
            for block_idx, block in enumerate(page_blocks):
                # Process text block
                rect = fitz.Rect(block[:4])
                text = block[4]
                
                try:
                    # Skip very short or empty blocks
                    if not text or len(text.strip()) < 2:
                        continue
                        
                    # Get translation for this text
                    translated = translation_mapping.get(text, text)
                    
                    # Skip if translation is empty or identical to original
                    if not translated.strip() or translated == text:
                        continue
                    
                    # Create a white rectangle to cover the original text
                    # Use a slightly transparent white to blend better with background
                    # Try to detect the background color for better blending
                    try:
                        # Sample the background color near the text block
                        bg_color = (1, 1, 1)  # Default to white
                        
                        # Get the page pixmap
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        
                        # Sample points around the text block
                        sample_points = [
                            (max(0, int(rect.x0) - 5), max(0, int(rect.y0) - 5)),
                            (min(pix.width - 1, int(rect.x1) + 5), max(0, int(rect.y0) - 5)),
                            (max(0, int(rect.x0) - 5), min(pix.height - 1, int(rect.y1) + 5)),
                            (min(pix.width - 1, int(rect.x1) + 5), min(pix.height - 1, int(rect.y1) + 5))
                        ]
                        
                        # Get average color
                        r_sum, g_sum, b_sum = 0, 0, 0
                        for x, y in sample_points:
                            if 0 <= x < pix.width and 0 <= y < pix.height:
                                pixel = pix.pixel(x, y)
                                r, g, b = pixel[0] / 255, pixel[1] / 255, pixel[2] / 255
                                r_sum += r
                                g_sum += g
                                b_sum += b
                        
                        if sample_points:
                            bg_color = (r_sum / len(sample_points), g_sum / len(sample_points), b_sum / len(sample_points))
                        
                        # Draw rectangle with detected background color
                        # PyMuPDF version compatibility - older versions don't support opacity
                        new_page.draw_rect(rect, color=bg_color, fill=bg_color)
                    except Exception as color_error:
                        print(f"Error detecting background color: {color_error}, using white")
                        # Fallback to white background
                        new_page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                    
                    # Calculate appropriate font size based on original text and translation length
                    original_len = len(text.strip())
                    translated_len = len(translated.strip())
                    
                    # Base font size on text length ratio and available space
                    ratio = min(1.0, original_len / max(1, translated_len))
                    fontsize = max(8, 11 * ratio)  # Minimum 8pt, maximum 11pt
                    
                    # Use standard built-in fonts that are guaranteed to be available in all PDFs
                    is_heading = rect.y0 < 100 or len(text.strip()) < 50
                    fontname = "Helvetica-Bold" if is_heading else "Helvetica"
                    
                    # Determine text color - use black for light backgrounds, white for dark backgrounds
                    text_color = (0, 0, 0)  # Default to black
                    try:
                        # Calculate background brightness (simple average)
                        if 'bg_color' in locals():
                            brightness = sum(bg_color) / 3
                            # Use white text on dark backgrounds
                            if brightness < 0.5:
                                text_color = (1, 1, 1)
                    except:
                        pass
                    
                    # Insert the translated text with word wrapping
                    # Expand the rectangle slightly to accommodate longer translations
                    expanded_rect = fitz.Rect(
                        rect.x0,
                        rect.y0,
                        rect.x1 + 20,  # Add extra width
                        rect.y1 + 10    # Add extra height
                    )
                    
                    # Try multiple font sizes if needed
                    text_inserted = -1
                    
                    # List of fallback fonts to try
                    fallback_fonts = ["Helvetica", "Times-Roman", "Courier"]
                    
                    # Try different fonts and sizes
                    success = False
                    for current_font in fallback_fonts:
                        if success:
                            break
                            
                        for attempt in range(3):
                            try:
                                # Insert the translated text with word wrapping
                                text_inserted = new_page.insert_textbox(
                                    expanded_rect,
                                    translated,
                                    fontsize=fontsize,
                                    fontname=current_font,
                                    color=text_color,
                                    align=0
                                )
                                
                                # If text fit successfully, break the loop
                                if text_inserted >= 0:
                                    success = True
                                    break
                                    
                                # If text didn't fit, reduce font size for next attempt
                                fontsize = max(6, fontsize * 0.8)  # Reduce font size by 20%, minimum 6pt
                            except Exception as font_error:
                                print(f"Font error with {current_font}: {font_error}, trying next font or size")
                                fontsize = max(6, fontsize * 0.8)  # Reduce font size for next attempt
                    
                    # If all attempts failed, try a simpler approach with text insertion
                    if not success:
                        try:
                            # Further expand rectangle and use minimum font size
                            wider_rect = fitz.Rect(
                                rect.x0,
                                rect.y0,
                                rect.x1 + 40,  # Add even more width
                                rect.y1 + 20   # Add even more height
                            )
                            
                            # Try with the simplest text insertion method
                            try:
                                # Try insert_text instead of insert_textbox
                                new_page.insert_text(
                                    point=(rect.x0, rect.y0 + 10),
                                    text=translated[:100] + ("..." if len(translated) > 100 else ""),
                                    fontsize=6,
                                    color=text_color
                                )
                                success = True
                            except Exception as text_error:
                                print(f"Simple text insertion failed: {text_error}")
                                
                                # Last resort: try to draw text directly
                                try:
                                    # Create a simple text annotation
                                    annot = new_page.add_text_annot(
                                        rect.tl,  # top-left point
                                        translated[:50] + ("..." if len(translated) > 50 else ""),
                                        icon="Note"
                                    )
                                    success = True
                                except Exception as annot_error:
                                    print(f"Text annotation failed: {annot_error}")
                        except Exception as last_error:
                            print(f"All text insertion methods failed: {last_error}")
                except Exception as e:
                    print(f"Error processing block {block_idx} on page {page_idx+1}: {e}")
                    import traceback
                    traceback.print_exc()
            
            print(f"Finished processing page {page_idx+1}")
        
        # Save the translated document
        output_document.save(output_pdf_path)
        output_document.close()
        pdf_document.close()
        
        elapsed_time = time.time() - start_time
        print(f"PDF translation completed successfully in {elapsed_time:.2f} seconds")
        return True
        
    except Exception as e:
        print(f"Error translating PDF with images: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    args = setup_args()
    
    if args.command == 'extract':
        success = extract_text(args.pdf_path, args.output_path)
        sys.exit(0 if success else 1)
    
    elif args.command == 'ocr':
        success = extract_text_with_ocr(args.pdf_path, args.output_path)
        sys.exit(0 if success else 1)
    
    elif args.command == 'check_ocr':
        result = needs_ocr(args.pdf_path)
        print(str(result).lower())
        sys.exit(0)
    
    elif args.command == 'detect_language':
        lang = detect_language(args.pdf_path)
        print(lang)
        sys.exit(0)
    
    elif args.command == 'translate':
        success = translate_text(args.input_path, args.output_path, args.source_lang, args.target_lang)
        sys.exit(0 if success else 1)
    
    elif args.command == 'create_pdf':
        success = create_pdf(args.text_path, args.pdf_path, args.language)
        sys.exit(0 if success else 1)
    
    elif args.command == 'create_dual_pdf':
        success = create_dual_language_pdf(
            args.original_text_path,
            args.translated_text_path,
            args.pdf_path,
            args.source_lang,
            args.target_lang
        )
        sys.exit(0 if success else 1)
    
    elif args.command == 'translate_pdf':
        success = translate_pdf_with_images(
            args.input_path,
            args.output_path,
            args.source_lang,
            args.target_lang
        )
        sys.exit(0 if success else 1)
    
    else:
        print("Unknown command. Use -h for help.")
        sys.exit(1)
