#!/usr/bin/env python3

"""
EXACT LAYOUT TRANSLATOR - Preserves the exact coordinates of text while replacing with translations
"""

import os
import sys
import fitz  # PyMuPDF
from deep_translator import GoogleTranslator
import tempfile
import time
import re

def translate_text(text, source_lang="es", target_lang="en"):
    """Translate text with Google Translator"""
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

def exact_layout_translate_pdf(input_path, output_path, source_lang="es", target_lang="en"):
    """
    Translate PDF while preserving exact layout and text positions
    """
    if not os.path.exists(input_path):
        print(f"ERROR: Input file does not exist: {input_path}")
        return False
        
    print(f"EXACT LAYOUT TRANSLATION from {source_lang} to {target_lang}")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    
    # Special case for Spanish to English
    is_spanish_to_english = (source_lang.lower() == "es" and target_lang.lower() == "en")
    if is_spanish_to_english:
        print("CRITICAL LANGUAGE PAIR: Spanish to English - using enhanced visibility")
    
    try:
        # Open the input PDF
        doc = fitz.open(input_path)
        
        # Create a dictionary to cache translations
        translation_cache = {}
        
        # Process each page to replace text with translations
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Get all text blocks with their positions
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                # Only process text blocks
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            # Get the text and its position
                            text = span["text"]
                            
                            # Skip empty spans
                            if not text or text.isspace():
                                continue
                                
                            # Get font information
                            font_size = span["size"]
                            font_name = span["font"]
                            
                            # Check if we've already translated this text
                            if text in translation_cache:
                                translated_text = translation_cache[text]
                            else:
                                # Translate the text
                                translated_text = translate_text(text, source_lang, target_lang)
                                # Cache the translation
                                translation_cache[text] = translated_text
                            
                            # Find the span position
                            rect = fitz.Rect(span["bbox"])
                            origin = (rect.x0, rect.y1)  # Bottom-left corner
                            
                            # Remove the original text by drawing white rectangle over it
                            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                            
                            # Insert the translated text at the same position
                            # For Spanish to English, use double-rendering for better visibility
                            if is_spanish_to_english:
                                # First draw a white background for better contrast
                                # Make the background slightly larger than the text area
                                bg_rect = fitz.Rect(rect.x0 - 1, rect.y0 - 1, rect.x1 + 1, rect.y1 + 1)
                                page.draw_rect(bg_rect, color=(1, 1, 1), fill=(1, 1, 1))
                                
                                # Draw a border around the text
                                page.draw_rect(bg_rect, color=(0, 0, 0), width=0.3)
                                
                                # Draw text shadow for better visibility
                                # Offset by a small amount and use black
                                shadow_pos = (origin[0] + 0.5, origin[1] + 0.5)
                                page.insert_text(shadow_pos, translated_text, fontname=font_name, fontsize=font_size, color=(0, 0, 0))
                                
                                # Then draw the actual text
                                page.insert_text(origin, translated_text, fontname=font_name, fontsize=font_size, color=(0, 0, 0))
                            else:
                                # For other language pairs, just insert the text without special handling
                                page.insert_text(origin, translated_text, fontname=font_name, fontsize=font_size)
        
        # Save the translated PDF
        doc.save(output_path)
        doc.close()
        
        print(f"Successfully translated document to: {output_path}")
        return True
        
    except Exception as e:
        import traceback
        print(f"ERROR in exact layout translation: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: exact_layout_translate.py input_path output_path source_lang target_lang")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    source_lang = sys.argv[3]
    target_lang = sys.argv[4]
    
    success = exact_layout_translate_pdf(input_path, output_path, source_lang, target_lang)
    sys.exit(0 if success else 1)