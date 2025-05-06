#!/usr/bin/env python3

"""
AGGRESSIVE TRANSLATION - Extreme version that prioritizes text visibility over layout
Special version for Spanish to English translations that ensures text is visible
"""

import os
import sys
import fitz  # PyMuPDF
from deep_translator import GoogleTranslator
import tempfile
import uuid
import time
import re

def translate_text_with_fallbacks(text, source_lang="es", target_lang="en"):
    """Translate text with multiple fallback options and retries"""
    
    # Safety check for empty or whitespace text
    if not text or text.isspace() or len(text) < 2:
        return text
        
    # Don't translate if same language
    if source_lang == target_lang:
        return text
    
    # For Spanish to English, always use Spanish as source
    if target_lang == "en" and source_lang != "es":
        print(f"OVERRIDE: Using Spanish (es) instead of {source_lang} for Spanish→English translation")
        source_lang = "es"
        
    # Keep track of translation attempts
    attempts = 0
    max_attempts = 3
    
    # Try up to max_attempts times with the main approach
    while attempts < max_attempts:
        try:
            attempts += 1
            # Create translator with source and target languages
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            
            # Translate text
            translated = translator.translate(text)
            
            # Check if translation actually worked (changed the text)
            if translated and not translated.isspace() and translated.lower() != text.lower():
                return translated
            
            # If we get here, translation didn't make a real change
            print(f"Attempt {attempts}: Translation didn't change text: '{text[:30]}...'")
            
            # Sleep briefly before retry
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Translation error on attempt {attempts}: {e}")
            time.sleep(1)  # Slightly longer delay after error
    
    # If we get here, all attempts failed, try one last emergency approach
    print(f"EMERGENCY: All translation attempts failed for: '{text[:30]}...'")
    
    try:
        # Try one more time with a different implementation
        alternate_translator = GoogleTranslator(source="auto", target="en")
        emergency_result = alternate_translator.translate(text)
        
        if emergency_result and emergency_result != text:
            print(f"EMERGENCY TRANSLATION WORKED: '{text[:20]}...' → '{emergency_result[:20]}...'")
            return emergency_result
    except:
        pass
        
    # Last resort, return the original text
    return text

def aggressive_translate_pdf(input_path, output_path, source_lang="es", target_lang="en"):
    """
    Aggressively translate PDF with maximum text visibility - specialized for Spanish to English
    """
    if not os.path.exists(input_path):
        print(f"ERROR: Input file does not exist: {input_path}")
        return False
        
    print(f"AGGRESSIVE TRANSLATION from {source_lang} to {target_lang}")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    
    # Verify languages are different
    if source_lang == target_lang:
        print("Source and target languages are the same, making copy")
        import shutil
        shutil.copy(input_path, output_path)
        return True
        
    # For performance reasons, check if source language is es and target is en
    is_spanish_to_english = (source_lang.lower() == "es" and target_lang.lower() == "en") 
    if is_spanish_to_english:
        print("CRITICAL LANGUAGE PAIR: Spanish to English - using maximum visibility mode")
    
    # Test if translation works with our language codes
    test_phrases = [
        "Esta es una prueba de traducción.",
        "Document has text in Spanish that needs English translation.",
        "Hola mundo, esta es una frase en español."
    ]
    
    print("Testing translations:")
    
    for test_phrase in test_phrases:
        try:
            test_result = translate_text_with_fallbacks(test_phrase, source_lang, target_lang)
            print(f"Test: '{test_phrase}' → '{test_result}'")
        except Exception as e:
            print(f"Test translation error: {e}")
            # Continue even if test fails
    
    try:
        # Open source document
        doc = fitz.open(input_path)
        total_pages = len(doc)
        
        # Create a new document 
        new_doc = fitz.open()
        
        # Process each page
        for page_num in range(total_pages):
            page = doc[page_num]
            print(f"Processing page {page_num + 1}/{total_pages}")
            
            # Create a new page with same dimensions
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
            
            # First copy all visual content including images for the background
            new_page.show_pdf_page(new_page.rect, doc, page_num)
            
            try:
                # Extract text blocks
                text_blocks = page.get_text("dict")["blocks"]
                block_count = len(text_blocks)
                print(f"Found {block_count} text blocks on page {page_num + 1}")
                
                # Variables to track statistics
                processed_count = 0
                translated_count = 0
                
                # Process each text block
                for block in text_blocks:
                    if block.get("type") == 0:  # 0 = text block
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                # Get text content
                                text = span.get("text", "").strip()
                                if not text or len(text) < 2:
                                    continue
                                    
                                # Track that we're processing this span
                                processed_count += 1
                                
                                try:
                                    # Get position and font info
                                    origin = span.get("origin", (0, 0))
                                    font_size = span.get("size", 11)
                                    font_name = span.get("font", "helv")
                                    
                                    # For Spanish to English, translate and make highly visible
                                    translated = translate_text_with_fallbacks(text, source_lang, target_lang)
                                    
                                    # Skip if translation failed (returned same text)
                                    if text.lower() == translated.lower():
                                        continue
                                        
                                    # Count successful translations
                                    translated_count += 1
                                    
                                    # Get the bounding box of the original text
                                    # Make an expanded rectangle to ensure we cover the text
                                    rect = fitz.Rect(
                                        span["bbox"][0] - 5,      # left - expand
                                        span["bbox"][1] - 5,      # top - expand 
                                        span["bbox"][2] + 40,     # right - extra space for translated text
                                        span["bbox"][3] + 5       # bottom - expand
                                    )
                                    
                                    # Cover original text with white rectangle
                                    new_page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                                    
                                    # Draw a thin border to make text area stand out
                                    new_page.draw_rect(rect, color=(0, 0, 0), width=0.2)
                                    
                                    # Use larger font size to ensure text visibility
                                    render_size = max(font_size * 1.5, 12)
                                    
                                    # Add translated text on top of white rectangle
                                    new_page.insert_text(
                                        (origin[0], origin[1]), 
                                        translated,
                                        fontsize=render_size,
                                        fontname=font_name, 
                                        color=(0, 0, 0)  # Black text
                                    )
                                    
                                    # Add duplicate text with small offset for pseudo-bold effect
                                    # This makes text more readable against any background
                                    new_page.insert_text(
                                        (origin[0] + 0.3, origin[1]), 
                                        translated,
                                        fontsize=render_size,
                                        fontname=font_name, 
                                        color=(0, 0, 0)
                                    )
                                    
                                    # Log sample of translations for debugging
                                    if processed_count % 10 == 0:
                                        print(f"Translated: '{text[:20]}...' → '{translated[:20]}...'")
                                    
                                except Exception as span_error:
                                    print(f"Error processing text span: {str(span_error)}")
                
                print(f"Page {page_num + 1}: Processed {processed_count} spans, translated {translated_count}")
                
            except Exception as page_error:
                print(f"Error extracting text from page {page_num + 1}: {str(page_error)}")
                
        # Save the translated document
        new_doc.save(output_path)
        new_doc.close()
        doc.close()
        
        print(f"Successfully saved translated document to: {output_path}")
        return True
        
    except Exception as e:
        import traceback
        print(f"ERROR in translation process: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: aggressive_translate.py input_path output_path source_lang target_lang")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    source_lang = sys.argv[3]
    target_lang = sys.argv[4]
    
    success = aggressive_translate_pdf(input_path, output_path, source_lang, target_lang)
    sys.exit(0 if success else 1)