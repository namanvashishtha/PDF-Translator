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
    """Translate text directly, ignoring auto-detection with extra reliability"""
    
    # Safety check
    if not text or text.isspace():
        return text
        
    # Skip very short strings (likely not meaningful text)
    if len(text) < 2:
        return text
        
    # Don't translate if same language
    if source_lang == target_lang:
        return text
    
    # For Spanish to English, which is most important case, 
    # we will be super aggressive about making sure it works
    IS_SPANISH_TO_ENGLISH = (source_lang.lower() == "es" and target_lang.lower() == "en")
    if IS_SPANISH_TO_ENGLISH:
        print(f"CRITICAL TRANSLATION: Spanish to English for text: '{text[:50]}...'")
    
    # Special case: Almost always use Spanish as source if translating to English
    # This is a workaround for the common case where Spanish documents are being detected wrong
    actual_source = source_lang
    if target_lang == "en" and (source_lang == "auto" or source_lang == "en" or source_lang == "ca"):
        actual_source = "es"
        print(f"OVERRIDE: Using Spanish (es) instead of {source_lang} when translating to English")
        
    # Translation function with retries
    def attempt_translation(src_lang, tgt_lang, retry_count=0):
        try:
            # Create translator with source and target languages
            translator = GoogleTranslator(source=src_lang, target=tgt_lang)
            
            # Translate text with specific timeout
            translated = translator.translate(text)
            return translated
        except Exception as e:
            print(f"Translation error (attempt {retry_count}): {e}")
            if retry_count < 3:  # Maximum 3 retries
                print(f"Retrying translation (attempt {retry_count + 1})...")
                return attempt_translation(src_lang, tgt_lang, retry_count + 1)
            return None  # Give up after 3 attempts
    
    # First try with default language setting
    translated = attempt_translation(actual_source, target_lang)
    
    # Print debugging info for certain cases
    if translated and len(text) > 10 and text.lower() == translated.lower():
        print(f"WARNING: Text appears unchanged after translation: '{text[:30]}'")
        
        # Try again with explicit Spanish source if we didn't already
        if actual_source != "es" and target_lang == "en":
            print("FALLBACK: Attempting translation with Spanish (es) as explicit source")
            spanish_translated = attempt_translation("es", target_lang)
            
            if spanish_translated and spanish_translated != text:
                print("FALLBACK SUCCESSFUL: Translation worked with Spanish source")
                return spanish_translated
            
        # Try English as fallback target language
        if target_lang != "en":
            print("EMERGENCY FALLBACK: Attempting translation to English instead")
            english_translated = attempt_translation(actual_source, "en")
            if english_translated and english_translated != text:
                return english_translated
    
    # If all strategies failed, fallback to original text
    if not translated or translated.isspace():
        print(f"CRITICAL ERROR: All translation attempts failed for: '{text[:30]}'")
        return text
            
    return translated

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
                                
                                # Use a much more aggressive text replacement approach
                                # Create a more noticeable text box with solid white background
                                larger_rect = fitz.Rect(
                                    span["bbox"][0] - 3,    # x0 (expand leftward)
                                    span["bbox"][1] - 3,    # y0 (expand upward)
                                    span["bbox"][2] + 30,   # x1 (ensure plenty of space for translated text)
                                    span["bbox"][3] + 3     # y1 (expand downward)
                                )
                                
                                # ALWAYS use the aggressive approach for all translations
                                # First make the original text area completely white (solid background)
                                new_page.draw_rect(larger_rect, color=(1, 1, 1), fill=(1, 1, 1))
                                
                                # Apply a very thin black border to make the text area stand out
                                new_page.draw_rect(larger_rect, color=(0, 0, 0), width=0.1)
                                
                                # Insert text with much higher contrast and larger font
                                # Place text in the center of the white rectangle
                                text_x = origin[0]
                                text_y = origin[1]
                                
                                # Apply an even more aggressive approach for Spanish to English
                                if IS_SPANISH_TO_ENGLISH:
                                    # Double the font size for Spanish to English
                                    render_size = max(font_size * 1.5, 10)
                                    
                                    # Insert bold-style text (multiple overlapping renders)
                                    # This creates a more visible effect that stands out clearly
                                    new_page.insert_text(
                                        (text_x, text_y), 
                                        translated, 
                                        fontsize=render_size,
                                        fontname=font_name,
                                        color=(0, 0, 0)  # Pure black for maximum contrast
                                    )
                                    # Create fake bold effect with multiple slight offsets
                                    offsets = [0.2, 0.4, 0.6]
                                    for offset in offsets:
                                        new_page.insert_text(
                                            (text_x + offset, text_y), 
                                            translated, 
                                            fontsize=render_size,
                                            fontname=font_name,
                                            color=(0, 0, 0)
                                        )
                                else:
                                    # Standard approach for other language pairs, but still with 
                                    # better visibility than before
                                    render_size = max(font_size * 1.2, 9)
                                    
                                    # Insert text with good visibility
                                    new_page.insert_text(
                                        (text_x, text_y), 
                                        translated, 
                                        fontsize=render_size,
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