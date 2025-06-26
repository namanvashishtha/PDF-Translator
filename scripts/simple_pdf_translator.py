#!/usr/bin/env python3
"""
Simple PDF Translator - A reliable PDF translation tool
This script provides a simplified approach to PDF translation that prioritizes reliability over perfect layout preservation.
"""

import os
import sys
import time
import fitz  # PyMuPDF
import tempfile
import argparse
from deep_translator import GoogleTranslator

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    text = ""
    try:
        # Open the PDF
        doc = fitz.open(pdf_path)
        
        # Extract text from each page
        for page_num in range(len(doc)):
            page = doc[page_num]
            text += f"\n\n--- Page {page_num + 1} ---\n\n"
            text += page.get_text()
        
        doc.close()
        return text
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def translate_text(text, source_lang, target_lang):
    """Translate text from source language to target language"""
    if not text.strip():
        return ""
    
    # Skip translation if languages are the same
    if source_lang == target_lang:
        return text
    
    # Split text into manageable chunks (Google Translate has a limit)
    max_chunk_size = 4000
    chunks = []
    
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed the chunk size, start a new chunk
        if len(current_chunk) + len(paragraph) > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = paragraph
        else:
            if current_chunk:
                current_chunk += '\n\n' + paragraph
            else:
                current_chunk = paragraph
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    # Translate each chunk
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        print(f"Translating chunk {i+1}/{len(chunks)} ({len(chunk)} characters)")
        try:
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            translated = translator.translate(chunk)
            translated_chunks.append(translated)
        except Exception as e:
            print(f"Error translating chunk {i+1}: {e}")
            # If translation fails, try with auto-detection
            try:
                print("Trying with auto-detection...")
                translator = GoogleTranslator(source='auto', target=target_lang)
                translated = translator.translate(chunk)
                translated_chunks.append(translated)
            except Exception as auto_error:
                print(f"Auto-detection also failed: {auto_error}")
                # If all translation attempts fail, keep the original text
                translated_chunks.append(chunk)
    
    # Combine translated chunks
    return '\n\n'.join(translated_chunks)

def create_translated_pdf(translated_text, output_path):
    """Create a new PDF with the translated text"""
    try:
        # Create a new PDF document
        doc = fitz.open()
        
        # Split text by page markers
        pages = translated_text.split("--- Page ")
        
        # Skip the first empty element if it exists
        if not pages[0].strip():
            pages = pages[1:]
        
        # Process each page
        for page_text in pages:
            # Extract page number and content
            parts = page_text.split("---\n\n", 1)
            if len(parts) < 2:
                continue
                
            content = parts[1]
            
            # Create a new page
            page = doc.new_page()
            
            # Insert text
            page.insert_text((50, 50), content, fontname="Helvetica", fontsize=11)
        
        # If no pages were created (e.g., if splitting failed), create a single page with all text
        if len(doc) == 0:
            page = doc.new_page()
            page.insert_text((50, 50), translated_text, fontname="Helvetica", fontsize=11)
        
        # Save the document
        doc.save(output_path)
        doc.close()
        return True
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return False

def translate_pdf(input_path, output_path, source_lang, target_lang):
    """Translate a PDF file from source language to target language"""
    start_time = time.time()
    
    print(f"Extracting text from {input_path}...")
    text = extract_text_from_pdf(input_path)
    
    if not text:
        print("Failed to extract text from PDF")
        return False
    
    print(f"Translating from {source_lang} to {target_lang}...")
    translated_text = translate_text(text, source_lang, target_lang)
    
    print(f"Creating translated PDF at {output_path}...")
    success = create_translated_pdf(translated_text, output_path)
    
    elapsed_time = time.time() - start_time
    if success:
        print(f"Translation completed in {elapsed_time:.2f} seconds")
        return True
    else:
        print("Translation failed")
        return False

def main():
    parser = argparse.ArgumentParser(description="Simple PDF Translator")
    parser.add_argument("input_path", help="Path to input PDF file")
    parser.add_argument("output_path", help="Path to output PDF file")
    parser.add_argument("source_lang", help="Source language code (e.g., 'en', 'fr', 'auto')")
    parser.add_argument("target_lang", help="Target language code (e.g., 'en', 'fr')")
    
    args = parser.parse_args()
    
    success = translate_pdf(args.input_path, args.output_path, args.source_lang, args.target_lang)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()