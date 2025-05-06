#!/usr/bin/env python3

"""
GUARANTEED TRANSLATION - Force PDF text translation without relying on automatic detection
"""

import os
import sys
import fitz  # PyMuPDF
from deep_translator import GoogleTranslator
import tempfile
import uuid

def translate_text_directly(text, source_lang, target_lang):
    """Translate text directly, ignoring auto-detection"""
    
    # Safety check
    if not text or text.isspace():
        return text
        
    # Quick test if text might already be in target language
    # This is a very rough check but helps avoid unnecessary translations
    if source_lang == target_lang:
        return text
    
    # Special case: Almost always use Spanish as source if translating to English
    # This is a workaround for the common case where Spanish documents are being detected wrong
    actual_source = source_lang
    if target_lang == "en" and (source_lang == "auto" or source_lang == "en" or source_lang == "ca"):
        actual_source = "es"
        print(f"OVERRIDE: Using Spanish (es) instead of {source_lang} when translating to English")
        
    try:
        # Create translator with source and target languages
        translator = GoogleTranslator(source=actual_source, target=target_lang)
        
        # Translate text
        translated = translator.translate(text)
        
        # Print debugging info for certain cases
        if len(text) > 10 and text.lower() == translated.lower():
            print(f"WARNING: Text appears unchanged after translation: '{text[:30]}'")
            
            # If translation failed (output same as input), try Spanish as source 
            # This is only needed if we didn't already try Spanish
            if actual_source != "es":
                print("RETRY: Attempting translation with Spanish (es) as source")
                try:
                    retry_translator = GoogleTranslator(source="es", target=target_lang)
                    retry_translated = retry_translator.translate(text)
                    
                    if retry_translated != text:
                        print("RETRY SUCCESSFUL: Translation worked with Spanish source")
                        return retry_translated
                except Exception as retry_error:
                    print(f"Retry translation error: {retry_error}")
            
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        # Return original text on error
        return text

def guaranteed_translate_pdf(input_path, output_path, source_lang, target_lang):
    """
    Directly create a new PDF with translated text without relying on auto-detection
    """
    if not os.path.exists(input_path):
        print(f"ERROR: Input file does not exist: {input_path}")
        return False
        
    print(f"GUARANTEED TRANSLATION from {source_lang} to {target_lang}")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    
    # Verify languages are different
    if source_lang == target_lang:
        print("Source and target languages are the same, making copy")
        import shutil
        shutil.copy(input_path, output_path)
        return True
        
    # Check if this is Spanish to English - the most common translation
    # For this case, we'll be more aggressive about ensuring translated text is visible
    IS_SPANISH_TO_ENGLISH = (source_lang.lower() == "es" and target_lang.lower() == "en")
    if IS_SPANISH_TO_ENGLISH:
        print("CRITICAL CASE: Spanish to English translation - using high visibility mode")
    else:
        print(f"Normal translation mode for {source_lang} to {target_lang}")

    # First test if translation works with our language codes
    test_input = "This is a test sentence."
    
    # Use language-specific test texts for more accurate testing
    if source_lang == "es":
        test_input = "Esta es una frase de prueba en español."
    elif source_lang == "fr":
        test_input = "Ceci est une phrase de test en français."
    elif source_lang == "de":
        test_input = "Das ist ein Testsatz auf Deutsch."
    elif source_lang == "ca":
        test_input = "Aquesta és una frase de prova en català."
        
    print(f"Test translating: '{test_input}'")
    
    try:
        test_output = translate_text_directly(test_input, source_lang, target_lang)
        print(f"Test translation result: '{test_output}'")
        
        if test_input == test_output:
            print("WARNING: Test translation did not change text, may indicate a problem")
    except Exception as e:
        print(f"ERROR in test translation: {e}")
        return False
        
    try:
        # Open source document
        doc = fitz.open(input_path)
        
        # Create a new document
        new_doc = fitz.open()
        
        # Initialize counters for overall statistics
        total_processed_spans = 0
        total_translated_spans = 0
        
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
            try:
                blocks = page.get_text("dict")["blocks"]
                print(f"Found {len(blocks)} blocks on page {page_num+1}")
            except Exception as block_err:
                print(f"Error extracting blocks: {block_err}")
                blocks = []
            
            # Track processed text spans for debugging
            processed_spans = 0
            translated_spans = 0
            
            # Translate and add text
            for block in blocks:
                if block.get("type") == 0:  # text block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            processed_spans += 1
                            total_processed_spans += 1
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
                                translated = translate_text_directly(text, source_lang, target_lang)
                                
                                # Skip if translation failed
                                if not translated or translated.isspace():
                                    continue
                                    
                                # Count translations
                                if text.lower() != translated.lower():
                                    translated_spans += 1
                                    total_translated_spans += 1
                                
                                # CRITICAL FIX: Change text visibility approach
                                # Instead of trying to cover text with white rectangles
                                # which might interfere with background images, use a different approach
                                
                                # Make text stand out with a semi-transparent background
                                rect = fitz.Rect(
                                    span["bbox"][0] - 2,  # x0
                                    span["bbox"][1] - 2,  # y0 
                                    span["bbox"][2] + 20,  # x1 - extra space for translated text
                                    span["bbox"][3] + 2   # y1
                                )
                                
                                # Special handling for Spanish to English translations (most important case)
                                if IS_SPANISH_TO_ENGLISH:
                                    # Add a more opaque background for Spanish->English translations
                                    # Draw a solid white background first 
                                    new_page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                                    
                                    # Then add the black text on top with a slightly larger font
                                    new_page.insert_text(
                                        (origin[0], origin[1]), 
                                        translated, 
                                        fontsize=font_size * 1.1,  # Make text slightly larger
                                        fontname=font_name,
                                        color=(0, 0, 0)  # Pure black for maximum contrast
                                    )
                                    
                                    # Add a second copy of the text slightly offset for emphasis
                                    # This creates a pseudo-bold effect
                                    if len(translated) > 3:  # Only for non-trivial text
                                        new_page.insert_text(
                                            (origin[0] + 0.3, origin[1]), 
                                            translated, 
                                            fontsize=font_size * 1.1,
                                            fontname=font_name,
                                            color=(0, 0, 0)
                                        )
                                else:
                                    # Standard approach for other language pairs
                                    # Draw semi-transparent white background for better readability
                                    new_page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1, 0.7))
                                    
                                    # Insert translated text with high contrast black color
                                    new_page.insert_text(
                                        (origin[0], origin[1]), 
                                        translated, 
                                        fontsize=font_size * 1.0,  # Use original size for better visibility
                                        fontname=font_name,
                                        color=(0, 0, 0)  # Force black color for best contrast
                                    )
                                
                                # Log sample translations (not every one to reduce noise)
                                if processed_spans % 10 == 0 and len(text) > 5:
                                    print(f"  Translated ({processed_spans}): '{text[:30]}...' → '{translated[:30]}...'")
                            except Exception as e:
                                print(f"  Error translating text block: {e}")
            
            print(f"Processed {processed_spans} text spans, translated {translated_spans} on page {page_num+1}")
        
        # Save the result
        new_doc.save(output_path)
        new_doc.close()
        doc.close()
        
        print(f"Guaranteed translation saved to: {output_path}")
        print(f"Summary: Processed {total_processed_spans} text spans, translated {total_translated_spans} spans")
        return True
        
    except Exception as e:
        import traceback
        print(f"Error during guaranteed translation: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: guaranteed_translate.py input_path output_path source_lang target_lang")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    source_lang = sys.argv[3]
    target_lang = sys.argv[4]
    
    success = guaranteed_translate_pdf(input_path, output_path, source_lang, target_lang)
    sys.exit(0 if success else 1)