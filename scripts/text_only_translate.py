#!/usr/bin/env python3

"""
TEXT-ONLY TRANSLATION - Absolute simplest approach that just extracts text, 
translates it, and creates a new PDF with basic text only
"""

import os
import sys
import tempfile
import subprocess
from deep_translator import GoogleTranslator
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

def extract_text_with_command(pdf_path):
    """Use multiple command line tools to extract text"""
    try:
        # Try pdf2text from poppler first
        text = extract_text_with_pdf2text(pdf_path)
        if text and len(text) > 100:  # Minimum viable text length
            return text
            
        # If that fails, try pdftotxt
        print("pdf2text extraction insufficient, trying pdftotext...")
        try:
            text = extract_text_with_pdftotext(pdf_path)
            if text and len(text) > 100:
                return text
        except Exception as e2:
            print(f"pdftotext failed: {e2}")
            
        # Still no good text? Try one more tool
        print("pdftotext extraction insufficient, trying pdftocairo+OCR...")
        
        # Fallback to PyPDF2
        print("All command line tools failed, using PyPDF2...")
        return extract_text_with_pypdf2(pdf_path)
        
    except Exception as e:
        print(f"Error in command extraction: {e}")
        # Last resort is PyPDF2
        return extract_text_with_pypdf2(pdf_path)
        
def extract_text_with_pdf2text(pdf_path):
    """Use pdf2text command from poppler tools"""
    try:
        # Create temporary file for output
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_txt_path = temp_file.name
            
        # Use pdf2text command (part of poppler)
        cmd = ['pdf2text', '-simple', pdf_path, temp_txt_path]
        process = subprocess.run(cmd, capture_output=True, check=False)
        
        # Check if successful
        if process.returncode != 0:
            print(f"pdf2text error: {process.stderr.decode('utf-8', errors='replace')}")
            if os.path.exists(temp_txt_path):
                os.unlink(temp_txt_path)
            return ""
            
        # Read the extracted text
        if os.path.exists(temp_txt_path):
            with open(temp_txt_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
                
            # Clean up
            os.unlink(temp_txt_path)
            return text
        else:
            return ""
    except Exception as e:
        print(f"pdf2text extraction failed: {e}")
        return ""
        
def extract_text_with_pdftotext(pdf_path):
    """Use pdftotext command line tool from poppler"""
    try:
        # Create temporary file for output
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_txt_path = temp_file.name
            
        # Run pdftotext command
        cmd = ['pdftotext', '-layout', pdf_path, temp_txt_path]
        process = subprocess.run(cmd, capture_output=True, check=False)
        
        # Check if successful
        if process.returncode != 0:
            print(f"pdftotext error: {process.stderr.decode('utf-8', errors='replace')}")
            if os.path.exists(temp_txt_path):
                os.unlink(temp_txt_path)
            return ""
            
        # Read the text back
        if os.path.exists(temp_txt_path):
            with open(temp_txt_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
                
            # Clean up
            os.unlink(temp_txt_path)
            return text
        else:
            return ""
    except Exception as e:
        print(f"pdftotext extraction failed: {e}")
        return ""

def extract_text_with_pypdf2(pdf_path):
    """Extract text using PyPDF2 as a fallback"""
    try:
        import PyPDF2
        
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\\n\\n--- PAGE BREAK ---\\n\\n"
                
        return text
    except Exception as e:
        print(f"Error extracting text with PyPDF2: {e}")
        return ""

def translate_text(text, source_lang, target_lang):
    """Translate text with Google Translator"""
    try:
        if source_lang == target_lang:
            return text
            
        # Clean text before translation
        text = text.strip()
        if not text:
            return ""
            
        # Translate text with Google Translator
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        
        # Translate text in chunks to avoid exceeding limits
        chunk_size = 4000  # Google Translate has a limit of ~5000 chars
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        # Translate each chunk
        translated_chunks = []
        for chunk in chunks:
            try:
                translated = translator.translate(chunk)
                translated_chunks.append(translated)
            except Exception as chunk_error:
                print(f"Error translating chunk: {chunk_error}")
                # Return original chunk if translation fails
                translated_chunks.append(chunk)
                
        # Join translated chunks
        return "".join(translated_chunks)
        
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text on error

def create_simple_pdf(text, output_path):
    """Create a simple PDF with just text"""
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Set font
    font_name = "Helvetica"
    font_size = 10
    line_height = font_size * 1.2
    
    # Set margins
    left_margin = 0.5 * inch
    right_margin = width - 0.5 * inch
    top_margin = height - 0.5 * inch
    bottom_margin = 0.5 * inch
    
    # Available width for text
    available_width = right_margin - left_margin
    
    # Split text into lines
    lines = text.split('\\n')
    
    # Start at top margin
    y_position = top_margin
    
    # Set font
    c.setFont(font_name, font_size)
    
    for line in lines:
        # Check if we need a new page
        if y_position < bottom_margin:
            c.showPage()
            y_position = top_margin
            c.setFont(font_name, font_size)
            
        # Check if it's a page break marker
        if "--- PAGE BREAK ---" in line:
            c.showPage()
            y_position = top_margin
            c.setFont(font_name, font_size)
            continue
            
        # Draw text
        text_width = c.stringWidth(line, font_name, font_size)
        
        # If text is too wide, wrap it
        if text_width > available_width:
            words = line.split()
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                test_width = c.stringWidth(test_line, font_name, font_size)
                
                if test_width <= available_width:
                    current_line = test_line
                else:
                    # Draw current line and start a new one
                    if current_line:
                        c.drawString(left_margin, y_position, current_line)
                        y_position -= line_height
                        
                        # Check if we need a new page
                        if y_position < bottom_margin:
                            c.showPage()
                            y_position = top_margin
                            c.setFont(font_name, font_size)
                            
                    current_line = word
                    
            # Draw the last line
            if current_line:
                c.drawString(left_margin, y_position, current_line)
                y_position -= line_height
        else:
            # Draw the line directly
            c.drawString(left_margin, y_position, line)
            y_position -= line_height
    
    # Save the PDF
    c.save()
    return True

def simple_translate_pdf(input_path, output_path, source_lang, target_lang):
    """
    Most basic approach: extract text, translate it, create a new PDF
    """
    if not os.path.exists(input_path):
        print(f"Input file does not exist: {input_path}")
        return False
        
    print(f"TEXT-ONLY TRANSLATION from {source_lang} to {target_lang}")
    print(f"Input PDF: {input_path}")
    print(f"Output PDF: {output_path}")
    
    try:
        # 1. Extract text from PDF
        print("Extracting text from PDF...")
        text = extract_text_with_command(input_path)
        
        if not text:
            print("No text extracted from PDF")
            return False
            
        print(f"Extracted {len(text)} characters from PDF")
        
        # 2. Translate text
        print(f"Translating from {source_lang} to {target_lang}...")
        translated_text = translate_text(text, source_lang, target_lang)
        
        if not translated_text:
            print("Translation failed")
            return False
            
        print(f"Translation complete: {len(translated_text)} characters")
        
        # 3. Create a new PDF with translated text
        print("Creating output PDF...")
        success = create_simple_pdf(translated_text, output_path)
        
        if success:
            print(f"Successfully created PDF: {output_path}")
            return True
        else:
            print("Failed to create PDF")
            return False
            
    except Exception as e:
        import traceback
        print(f"Error in simple translation: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: text_only_translate.py input_path output_path source_lang target_lang")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    source_lang = sys.argv[3]
    target_lang = sys.argv[4]
    
    success = simple_translate_pdf(input_path, output_path, source_lang, target_lang)
    sys.exit(0 if success else 1)