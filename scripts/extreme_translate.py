#!/usr/bin/env python3

"""
EXTREME TRANSLATION - Last resort option that completely rebuilds the PDF
Special version that ignores the original layout and prioritizes readability
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
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors

def translate_text(text, source_lang="es", target_lang="en"):
    """Translate text with multiple fallback options and retries"""
    
    # Safety check for empty or whitespace text
    if not text or text.isspace() or len(text) < 2:
        return text
        
    # Don't translate if same language
    if source_lang == target_lang:
        return text
    
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
    """Extract text from PDF with page breaks preserved"""
    try:
        doc = fitz.open(pdf_path)
        text_content = []
        
        for page_num in range(len(doc)):
            # Get page text with line breaks preserved
            page = doc[page_num]
            text = page.get_text()
            text_content.append(text)
            
        doc.close()
        return text_content
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return []

def extreme_translate_pdf(input_path, output_path, source_lang="es", target_lang="en"):
    """
    Extreme translation method that completely rebuilds the PDF with basic layout
    """
    if not os.path.exists(input_path):
        print(f"ERROR: Input file does not exist: {input_path}")
        return False
        
    print(f"EXTREME TRANSLATION from {source_lang} to {target_lang}")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    
    # For performance reasons, check if source language is es and target is en
    is_spanish_to_english = (source_lang.lower() == "es" and target_lang.lower() == "en") 
    if is_spanish_to_english:
        print("CRITICAL LANGUAGE PAIR: Spanish to English - using extreme rebuilding mode")
    
    try:
        # Set up the document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Create styles for different text elements
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Normal_Justified', 
            parent=styles['Normal'],
            alignment=TA_JUSTIFY
        ))
        
        # Create a bold style for headers
        styles.add(ParagraphStyle(
            name='Heading1',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=12
        ))
        
        # Extract text from the PDF, preserving page structure
        page_texts = extract_text_from_pdf(input_path)
        
        # Build the new PDF content
        story = []
        
        # Add title with document name
        doc_name = os.path.basename(input_path)
        title_text = f"<b>Translated Document: {doc_name}</b>"
        title = Paragraph(title_text, styles['Heading1'])
        story.append(title)
        story.append(Spacer(1, 0.25 * inch))
        
        # Add translation information
        info_text = f"<i>Translated from {source_lang} to {target_lang}</i>"
        info = Paragraph(info_text, styles['Italic'])
        story.append(info)
        story.append(Spacer(1, 0.5 * inch))
        
        # Process each page of extracted text
        for page_num, page_text in enumerate(page_texts):
            # Add page header
            page_header = Paragraph(f"<b>Page {page_num + 1}</b>", styles['Heading2'])
            story.append(page_header)
            story.append(Spacer(1, 0.2 * inch))
            
            # Split the text into paragraphs
            paragraphs = page_text.split('\n\n')
            
            # Process each paragraph
            for para_text in paragraphs:
                if not para_text.strip():
                    continue  # Skip empty paragraphs
                
                # Translate the paragraph text
                translated_text = translate_text(para_text, source_lang, target_lang)
                
                # Add the translated paragraph
                p = Paragraph(translated_text, styles['Normal_Justified'])
                story.append(p)
                story.append(Spacer(1, 0.1 * inch))
            
            # Add a page break after each original page except the last one
            if page_num < len(page_texts) - 1:
                story.append(Spacer(1, 0.5 * inch))
                story.append(Paragraph("--- Original Page Break ---", styles['Italic']))
                story.append(Spacer(1, 0.5 * inch))
        
        # Build the document
        doc.build(story)
        
        print(f"Successfully saved translated document to: {output_path}")
        return True
        
    except Exception as e:
        import traceback
        print(f"ERROR in extreme translation process: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: extreme_translate.py input_path output_path source_lang target_lang")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    source_lang = sys.argv[3]
    target_lang = sys.argv[4]
    
    success = extreme_translate_pdf(input_path, output_path, source_lang, target_lang)
    sys.exit(0 if success else 1)