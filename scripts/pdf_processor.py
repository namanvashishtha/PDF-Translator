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
    """Extract text from a PDF file"""
    text = ""
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            # Get number of pages
            num_pages = len(reader.pages)
            
            # Extract text from each page
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n\n"
                
        # Write text to output file
        with open(output_path, 'w', encoding='utf-8') as output_file:
            output_file.write(text)
            
        return True
    except Exception as e:
        print(f"Error extracting text: {e}", file=sys.stderr)
        return False

def extract_text_with_ocr(pdf_path, output_path):
    """Extract text from a PDF file using OCR"""
    try:
        text = ""
        
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=300)
        
        # Process each page with OCR
        for i, image in enumerate(images):
            # Perform OCR
            page_text = pytesseract.image_to_string(image)
            text += page_text + "\n\n"
        
        # Write text to output file
        with open(output_path, 'w', encoding='utf-8') as output_file:
            output_file.write(text)
            
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
                lang = langdetect.detect(text)
                return lang
            except:
                return "en"  # Default to English if detection fails
        else:
            return "en"  # Default to English if no text was extracted
    except Exception as e:
        print(f"Error detecting language: {e}", file=sys.stderr)
        return "en"  # Default to English on error

def translate_text(input_path, output_path, source_lang, target_lang):
    """Translate text from source language to target language"""
    try:
        with open(input_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        # Handle special case when source and target are the same
        if source_lang == target_lang or source_lang == "auto" and detect_language(input_path) == target_lang:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(text)
            return True
        
        # Use Google Translator
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        
        # Split text into chunks to avoid exceeding API limits
        # This is a simple approach, it could be improved to split by paragraphs
        MAX_CHUNK_SIZE = 4000  # Google Translate has limits
        
        chunks = []
        current_chunk = ""
        
        # Split by paragraphs
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 1 <= MAX_CHUNK_SIZE:
                current_chunk += paragraph + '\n'
            else:
                chunks.append(current_chunk)
                current_chunk = paragraph + '\n'
        
        if current_chunk:
            chunks.append(current_chunk)
        
        # Translate each chunk
        translated_text = ""
        for chunk in chunks:
            if chunk.strip():
                translated_chunk = translator.translate(chunk)
                translated_text += translated_chunk + '\n'
        
        # Write translated text to output file
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(translated_text)
        
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
