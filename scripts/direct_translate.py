#!/usr/bin/env python3

import os
import sys
import fitz  # PyMuPDF
from deep_translator import GoogleTranslator
import uuid
import json
import tempfile

def direct_translate_pdf(input_path, output_path, source_lang, target_lang):
    """
    Directly create a new PDF with translated text - simpler approach
    """
    print(f"DIRECT TRANSLATION from {source_lang} to {target_lang}")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    
    # Verify languages are different
    if source_lang == target_lang:
        print("Source and target languages are the same, making copy")
        import shutil
        shutil.copy(input_path, output_path)
        return True

    # Test translation to verify language support
    test_text = "This is a test sentence."
    if source_lang == "ca":
        test_text = "Aquesta és una frase de prova."
    elif source_lang == "es":
        test_text = "Esta es una frase de prueba."
    
    print(f"Testing translation from {source_lang} to {target_lang} with: '{test_text}'")
    
    try:
        # Create translator
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translated_test = translator.translate(test_text)
        print(f"Test translation result: '{translated_test}'")
    except Exception as e:
        print(f"ERROR: Test translation failed! {str(e)}")
        return False
        
    try:
        # Open source document
        doc = fitz.open(input_path)
        
        # Create a new document
        new_doc = fitz.open()
        
        # Process each page
        for page_num in range(len(doc)):
            print(f"Processing page {page_num+1}/{len(doc)}")
            
            # Get the original page
            page = doc[page_num]
            
            # Create a new page with the same dimensions
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
            
            # First add all images and drawings (non-text content)
            # Copy the entire visual appearance of the page
            new_page.show_pdf_page(
                new_page.rect,  # where to place the image
                doc,            # source document
                page_num,       # source page number
            )
            
            # Extract text blocks
            blocks = page.get_text("dict")["blocks"]
            
            # Translate and add text
            for block in blocks:
                if block.get("type") == 0:  # text block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            
                            # Skip empty or very short text
                            if not text or len(text) < 2:
                                continue
                                
                            try:
                                # Get position and font information
                                origin = (span["origin"][0], span["origin"][1])
                                font_size = span["size"]
                                font_name = span["font"]
                                color = span["color"]
                                
                                # Translate text
                                translated = translator.translate(text)
                                
                                # Create a white rectangle to cover original text
                                rect = fitz.Rect(
                                    span["bbox"][0] - 1,  # x0
                                    span["bbox"][1] - 1,  # y0 
                                    span["bbox"][2] + 1,  # x1
                                    span["bbox"][3] + 1   # y1
                                )
                                
                                # Create a bigger area to make sure we cover all the text
                                extra_width = max(len(translated) - len(text), 0) * 2  # estimate extra space needed
                                expanded_rect = fitz.Rect(
                                    rect.x0,
                                    rect.y0,
                                    rect.x1 + extra_width,
                                    rect.y3
                                )
                                
                                # Draw white rectangle to cover original text
                                new_page.draw_rect(expanded_rect, color=(1, 1, 1), fill=(1, 1, 1))
                                
                                # Also log direct comparison for troubleshooting
                                if text.lower() == translated.lower():
                                    print(f"  WARNING: Text unchanged after translation: '{text}'")
                                
                                # Insert translated text
                                new_page.insert_text(
                                    (origin[0], origin[1]), 
                                    translated, 
                                    fontsize=font_size * 0.9,  # slightly smaller to fit
                                    fontname=font_name,
                                    color=color
                                )
                                
                                # Log sample translations (not every one to reduce noise)
                                if len(text) > 10:
                                    print(f"  Translated: '{text[:20]}...' → '{translated[:20]}...'")
                            except Exception as e:
                                print(f"  Error translating text block: {e}")
                                # Skip this span on error
            
        # Save the result
        new_doc.save(output_path)
        new_doc.close()
        doc.close()
        
        print(f"Direct translation saved to: {output_path}")
        return True
        
    except Exception as e:
        import traceback
        print(f"Error during direct translation: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: direct_translate.py input_path output_path source_lang target_lang")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    source_lang = sys.argv[3]
    target_lang = sys.argv[4]
    
    success = direct_translate_pdf(input_path, output_path, source_lang, target_lang)
    sys.exit(0 if success else 1)