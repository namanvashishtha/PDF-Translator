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
from deep_translator import GoogleTranslator
import io
import re
import argparse
import tempfile
import fitz  # PyMuPDF - for preserving images in PDFs

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
    """Extract text from a PDF file using OCR with SUPER FAST mode"""
    try:
        print(f"Starting FAST OCR text extraction for {pdf_path}")
        text = ""
        
        # Lower DPI even further for extremely fast processing
        # 150 DPI is much faster while still readable
        images = convert_from_path(pdf_path, dpi=150)
        
        total_pages = len(images)
        print(f"PDF has {total_pages} pages to process")
        
        # FAST MODE: Sample only a few pages for OCR
        pages_to_process = []
        
        if total_pages <= 3:
            # For small documents, process all pages
            pages_to_process = list(range(total_pages))
            print(f"Processing all {total_pages} pages with OCR")
        else:
            # For larger documents, just do first, one middle, and last page
            pages_to_process = [0]  # First page
            
            if total_pages > 2:
                middle = total_pages // 2
                pages_to_process.append(middle)  # Middle page
            
            if total_pages > 1:
                pages_to_process.append(total_pages - 1)  # Last page
                
            print(f"FAST MODE: Processing only {len(pages_to_process)} pages with OCR")
        
        # Process selected pages with OCR
        for idx, i in enumerate(pages_to_process):
            image = images[i]
            print(f"OCR processing page {i+1}/{total_pages} ({idx+1}/{len(pages_to_process)})")
            
            # Use fastest OCR settings
            # --oem 0: Legacy engine only (faster but less accurate)
            # --psm 3: Auto page segmentation
            config = '--oem 0 --psm 3'
            
            # Perform OCR
            page_text = pytesseract.image_to_string(image, config=config)
            
            # Add page marker except for first page
            if i > 0:
                text += f"\n\n[Page {i+1}]\n\n"
            
            text += page_text + "\n\n"
        
        # Add note about fast mode if we skipped pages
        if len(pages_to_process) < total_pages:
            text += "\n\n[NOTE: This is a fast preview translation. Only selected pages were processed using OCR.]\n\n"
        
        # Write text to output file
        with open(output_path, 'w', encoding='utf-8') as output_file:
            output_file.write(text)
        
        print(f"Fast OCR extraction completed, saved to {output_path}")
        return True
    except Exception as e:
        print(f"Error performing OCR: {e}", file=sys.stderr)
        return False

def needs_ocr(pdf_path):
    """Check if a PDF needs OCR by examining if it has extractable text"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            # Check a sample of pages (up to 5)
            pages_to_check = min(5, len(reader.pages))
            total_text = ""
            
            for i in range(pages_to_check):
                page = reader.pages[i]
                text = page.extract_text()
                total_text += text
            
            # If we extracted a reasonable amount of text, OCR is likely not needed
            # This is a simple heuristic and could be improved
            if len(total_text) > 100:  # Arbitrary threshold
                return False
            return True
    except Exception as e:
        print(f"Error checking if PDF needs OCR: {e}", file=sys.stderr)
        return True  # Default to using OCR if we can't determine

def detect_language(pdf_path):
    """Detect the language of a PDF document"""
    try:
        print(f"Detecting language for PDF: {os.path.basename(pdf_path)}")
        # First extract some text from the PDF
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            text_path = temp_file.name
        
        # Try direct extraction first
        if extract_text(pdf_path, text_path):
            with open(text_path, 'r', encoding='utf-8') as file:
                text = file.read()
        else:
            # If direct extraction fails, try OCR
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as ocr_temp_file:
                ocr_text_path = ocr_temp_file.name
            
            extract_text_with_ocr(pdf_path, ocr_text_path)
            with open(ocr_text_path, 'r', encoding='utf-8') as file:
                text = file.read()
            os.unlink(ocr_text_path)
        
        # Clean up the temporary file
        os.unlink(text_path)
        
        if text.strip():
            # Detect language using langdetect
            try:
                # Get a sample of the text (up to 5000 chars) for faster detection
                sample_text = text[:5000]
                lang = langdetect.detect(sample_text)
                print(f"Detected language: {lang}")
                return lang
            except Exception as e:
                print(f"Language detection failed: {e}", file=sys.stderr)
                return "en"  # Default to English if detection fails
        else:
            print("No text content found for language detection", file=sys.stderr)
            return "en"  # Default to English if no text was extracted
    except Exception as e:
        print(f"Error detecting language: {e}", file=sys.stderr)
        return "en"  # Default to English on error

def format_language_code(code):
    """Format language code properly for Google Translator API"""
    # Map ISO 639-1 language codes to Google Translator codes
    language_map = {
        'en': 'english',
        'es': 'spanish',
        'fr': 'french',
        'de': 'german',
        'it': 'italian',
        'pt': 'portuguese',
        'ja': 'japanese',
        'zh': 'chinese (simplified)',
        'zh-cn': 'chinese (simplified)',
        'zh-CN': 'chinese (simplified)',
        'ru': 'russian',
        'ar': 'arabic',
        'hi': 'hindi',
        'nl': 'dutch',
        'ko': 'korean',
        'tr': 'turkish',
        'sv': 'swedish',
        'pl': 'polish',
        # Add more mappings as needed
    }
    
    # Check both lowercase and original form
    lower_code = code.lower() if isinstance(code, str) else ''
    if lower_code in language_map:
        return language_map[lower_code]
        
    # Try to clean up the code if it contains extraneous information
    if isinstance(code, str) and len(code) > 5:
        # Try to extract a code pattern at the end
        import re
        match = re.search(r'[a-z]{2}(?:-[a-z]{2})?$', lower_code)
        if match:
            extracted = match.group(0)
            if extracted in language_map:
                return language_map[extracted]
    
    # If all else fails, return as is (will use auto-detection)
    return code if isinstance(code, str) else 'auto'


def translate_text(input_path, output_path, source_lang, target_lang):
    """Translate text from source language to target language"""
    try:
        with open(input_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        # Format language codes properly for Google Translator
        source_code = format_language_code(source_lang)
        target_code = format_language_code(target_lang)
        
        print(f"Translating from {source_lang} ({source_code}) to {target_lang} ({target_code})")
        
        # Handle special case when source and target are the same
        if source_lang == target_lang:
            print("Source and target languages are the same, skipping translation")
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(text)
            return True
        
        # FAST MODE: Process only a representative portion of the document
        # This drastically speeds up translation while providing useful results
        print("Using fast translation mode")
        
        # Get a representative sample (first 1000 characters plus a paragraph from middle and end)
        total_length = len(text)
        if total_length > 3000:
            # Take beginning
            beginning = text[:1000]
            # Take some from middle
            middle_start = total_length // 2 - 500
            middle = text[middle_start:middle_start+800] if middle_start > 0 else ""
            # Take end portion
            end_start = max(0, total_length - 700)
            end_portion = text[end_start:] if end_start < total_length else ""
            
            # Combine with section markers
            sample_text = beginning + "\n\n[...]\n\n" + middle + "\n\n[...]\n\n" + end_portion
            print(f"Reduced text from {total_length} to {len(sample_text)} characters for fast translation")
        else:
            sample_text = text
            print("Text is already short, using full text for translation")
            
        # Use Google Translator with optimized settings
        translator = GoogleTranslator(source=source_code if source_code != 'auto' else 'auto', 
                                     target=target_code)
        
        # Split text into chunks to avoid exceeding API limits
        # Using larger chunks and fewer iterations for faster translation
        MAX_CHUNK_SIZE = 5000  # Maximum allowed size
        
        # Split text into manageable chunks
        chunks = []
        
        # Simple split by MAX_CHUNK_SIZE for speed
        for i in range(0, len(sample_text), MAX_CHUNK_SIZE):
            chunk = sample_text[i:i + MAX_CHUNK_SIZE]
            if chunk.strip():
                chunks.append(chunk)
        
        print(f"Split text into {len(chunks)} chunks for translation")
        
        # Translate each chunk - with optimized settings
        translated_text = ""
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                print(f"Translating chunk {i+1} of {len(chunks)}")
                translated_chunk = translator.translate(chunk)
                translated_text += translated_chunk + '\n'
        
        # Write translated text to output file
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(translated_text)
        
        print("Translation completed successfully")
        return True
    except Exception as e:
        print(f"Error translating text: {e}", file=sys.stderr)
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
    
    else:
        print("Unknown command. Use -h for help.")
        sys.exit(1)
