#!/usr/bin/env python3

"""
PURE TEXT TRANSLATION - Extract all text, translate it, and create a new plain text PDF with NO formatting
Suitable when original PDF formatting causes rendering issues
"""

import os
import sys
import fitz  # PyMuPDF
from deep_translator import GoogleTranslator
import tempfile
import uuid
import time
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors

def translate_text(text, source_lang="es", target_lang="en"):
    """Translate text with multiple fallback options and retries"""
    
    # Safety check for empty or whitespace text
    if not text or text.isspace() or len(text) < 2:
        return text
        
    # Don't translate if same language
    if source_lang == target_lang:
        return text
    
    # Special case for Spanish to English
    is_spanish_to_english = (source_lang.lower() == "es" and target_lang.lower() == "en")
    if is_spanish_to_english and source_lang != "es":
        print("OVERRIDE: Using Spanish (es) as source language for Spanish→English translation")
        source_lang = "es"
        
    # Keep track of translation attempts
    attempts = 0
    max_attempts = 3
    
    # Try up to max_attempts times
    while attempts < max_attempts:
        try:
            attempts += 1
            # Create translator with source and target languages
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            
            # Translate text
            translated = translator.translate(text)
            
            # Check if translation actually worked
            if translated and not translated.isspace() and translated.lower() != text.lower():
                return translated
            
            # If we get here, translation didn't make a real change
            print(f"Attempt {attempts}: Translation didn't change text")
            
            # Sleep briefly before retry
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Translation error on attempt {attempts}: {e}")
            time.sleep(1)  # Slightly longer delay after error
    
    # If we get here, all attempts failed
    print("WARNING: All translation attempts failed, returning original text")
    return text

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF in a simple format"""
    try:
        doc = fitz.open(pdf_path)
        text_content = []
        
        for page_num in range(len(doc)):
            # Extract text from page
            page = doc[page_num]
            text = page.get_text()
            
            # Clean up the text
            lines = text.split('\n')
            clean_lines = []
            for line in lines:
                if line.strip():
                    clean_lines.append(line.strip())
            
            # Join cleaned lines with newlines
            clean_text = '\n'.join(clean_lines)
            text_content.append(clean_text)
            
        doc.close()
        return text_content
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return []

def create_simple_text_pdf(text_content, output_path):
    """Create a very simple PDF with just text - no fancy formatting"""
    try:
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter
        
        # Set font to a standard font that's guaranteed to be available
        font_name = "Helvetica"
        font_size = 12
        line_height = font_size * 1.2
        
        # Set margins
        left_margin = 1 * inch
        top_margin = height - 1 * inch
        
        for page_text in text_content:
            # Split text into lines
            lines = page_text.split("\n")
            
            # Start at top margin
            y_position = top_margin
            
            for line in lines:
                # Skip empty lines
                if not line.strip():
                    y_position -= line_height / 2
                    continue
                
                # Draw text
                c.setFont(font_name, font_size)
                c.drawString(left_margin, y_position, line)
                
                # Move down for next line
                y_position -= line_height
                
                # If we've reached the bottom margin, start a new page
                if y_position < 1 * inch:
                    c.showPage()
                    y_position = top_margin
            
            # Add a page break after each original page
            c.showPage()
        
        c.save()
        return True
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return False

def pure_text_translate_pdf(input_path, output_path, source_lang="es", target_lang="en"):
    """
    Extract text, translate it, and create a simple text-only PDF
    """
    if not os.path.exists(input_path):
        print(f"ERROR: Input file does not exist: {input_path}")
        return False
        
    print(f"PURE TEXT TRANSLATION from {source_lang} to {target_lang}")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    
    # Create a temporary text file for the translated content
    temp_dir = tempfile.gettempdir()
    temp_text_file = os.path.join(temp_dir, f"translated_text_{uuid.uuid4()}.txt")
    
    try:
        # Extract text from PDF
        print("Extracting text from PDF...")
        page_texts = extract_text_from_pdf(input_path)
        
        if not page_texts:
            print("Error: No text extracted from PDF")
            return False
        
        print(f"Extracted {len(page_texts)} pages of text")
        
        # Translate each page
        translated_pages = []
        for i, page_text in enumerate(page_texts):
            print(f"Translating page {i+1}/{len(page_texts)}...")
            
            # Add page header
            translated_page = f"--- Page {i+1} ---\n\n"
            
            # Split into paragraphs and translate each
            paragraphs = page_text.split('\n\n')
            for para in paragraphs:
                if not para.strip():
                    continue
                    
                translated_para = translate_text(para, source_lang, target_lang)
                translated_page += translated_para + "\n\n"
            
            translated_pages.append(translated_page)
        
        # Create the output PDF with the translated text
        print("Creating output PDF...")
        success = create_simple_text_pdf(translated_pages, output_path)
        
        if success:
            print(f"Successfully created translated PDF: {output_path}")
            return True
        else:
            print("Failed to create output PDF")
            return False
            
    except Exception as e:
        import traceback
        print(f"ERROR in pure text translation: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: pure_text_translate.py input_path output_path source_lang target_lang")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    source_lang = sys.argv[3]
    target_lang = sys.argv[4]
    
    success = pure_text_translate_pdf(input_path, output_path, source_lang, target_lang)
    sys.exit(0 if success else 1)