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
    
    # For Spanish to English, which is most important case
    IS_SPANISH_TO_ENGLISH = (source_lang.lower() == "es" and target_lang.lower() == "en")
    if IS_SPANISH_TO_ENGLISH:
        print(f"CRITICAL TRANSLATION: Spanish to English for text: '{text[:50]}...'")
    
    # Use the provided source language but with fallbacks if needed
    actual_source = source_lang
    
    # Only override if source is auto, don't force Spanish for everything
    if source_lang == "auto" or source_lang == "ca":
        # Try to detect the language from the text itself
        try:
            import langdetect
            detected = langdetect.detect(text[:1000])
            print(f"Auto-detected language: {detected}")
            actual_source = detected
        except Exception as e:
            print(f"Language detection failed: {e}")
            # Keep the original source language
            
    print(f"Using source language: {actual_source} for translation to {target_lang}")
    
    # Translation function with retries and improved handling
    def attempt_translation(src_lang, tgt_lang, retry_count=0):
        try:
            # Create translator with source and target languages
            translator = GoogleTranslator(source=src_lang, target=tgt_lang)
            
            # For longer texts, split into chunks to improve reliability
            if len(text) > 1000:
                # Split text into sentences or chunks
                chunks = []
                current_chunk = ""
                
                # Simple sentence splitting (not perfect but helps)
                for sentence in text.replace('. ', '.|').replace('! ', '!|').replace('? ', '?|').split('|'):
                    if len(current_chunk) + len(sentence) < 1000:
                        current_chunk += sentence + (' ' if not sentence.endswith(('.', '!', '?')) else '')
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence + (' ' if not sentence.endswith(('.', '!', '?')) else '')
                
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Translate each chunk
                translated_chunks = []
                for chunk in chunks:
                    chunk_translated = translator.translate(chunk)
                    translated_chunks.append(chunk_translated)
                
                # Join the translated chunks
                return ' '.join(translated_chunks)
            else:
                # For shorter texts, translate directly
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
    IS_SPANISH_TO_ENGLISH = (source_lang.lower() == "es" and target_lang.lower() == "en")
    if IS_SPANISH_TO_ENGLISH:
        print("CRITICAL CASE: Spanish to English translation")
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
        
        # Initialize counters for overall statistics
        total_processed_spans = 0
        total_translated_spans = 0
        
        # Process each page
        for page_num in range(len(doc)):
            print(f"Processing page {page_num+1}/{len(doc)}")
            
            # Get the original page
            page = doc[page_num]
            
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
            
            # Create a list to store text replacements
            replacements = []
            
            # First pass: collect all text replacements
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
                                # Translate text
                                translated = translate_text_directly(text, source_lang, target_lang)
                                
                                # Skip if translation failed or is identical
                                if not translated or translated.isspace():
                                    continue
                                    
                                # Count translations
                                if text.lower() != translated.lower():
                                    translated_spans += 1
                                    total_translated_spans += 1
                                    
                                    # Store the replacement info
                                    replacements.append({
                                        "bbox": span["bbox"],
                                        "text": text,
                                        "translated": translated,
                                        "font_size": span["size"],
                                        "font_name": span["font"],
                                        "color": span["color"],
                                        "origin": span["origin"]
                                    })
                                    
                                # Log sample translations (not every one to reduce noise)
                                if processed_spans % 10 == 0 and len(text) > 5:
                                    print(f"  Translated ({processed_spans}): '{text[:30]}...' → '{translated[:30]}...'")
                            except Exception as e:
                                print(f"  Error translating text block: {e}")
            
            # Second pass: apply all replacements to the page
            # This approach preserves the original page structure and only modifies the text
            for replacement in replacements:
                try:
                    # Get the original text position
                    text_x = replacement["origin"][0]
                    text_y = replacement["origin"][1]
                    
                    # Get the original font properties
                    font_size = replacement["font_size"]
                    font_name = replacement["font_name"]
                    color = replacement["color"]
                    
                    # Create a redaction for the original text area (slightly expanded)
                    rect = fitz.Rect(
                        replacement["bbox"][0] - 1,  # x0
                        replacement["bbox"][1] - 1,  # y0 
                        replacement["bbox"][2] + 1,  # x1
                        replacement["bbox"][3] + 1   # y1
                    )
                    
                    # Add redaction annotation
                    annot = page.add_redact_annot(rect, fill=(1, 1, 1))
                    
                    # Apply the redaction
                    page.apply_redactions()
                    
                    # Now insert the translated text
                    # Try to use the original font first
                    try:
                        # Get all fonts available in the document
                        page_fonts = [f[4] for f in doc.get_page_fonts(page_num)]
                        
                        # Check if the original font exists in the document
                        if font_name in page_fonts:
                            use_font = font_name  # Use original font
                        else:
                            # Try to find a similar font in the document
                            font_base = font_name.split('-')[0].lower()
                            similar_fonts = [f for f in page_fonts if font_base in f.lower()]
                            
                            if similar_fonts:
                                use_font = similar_fonts[0]  # Use a similar font
                            else:
                                use_font = "helv"  # Default to Helvetica
                        
                        # Insert translated text at the exact same position with same font properties
                        page.insert_text(
                            (text_x, text_y), 
                            replacement["translated"], 
                            fontsize=font_size,  # Keep original size
                            fontname=use_font,
                            color=color  # Use the original text color
                        )
                    except Exception as font_error:
                        # Fallback to a guaranteed working approach if there's any font issue
                        print(f"Font error: {font_error}, using fallback font")
                        
                        # Use a standard built-in font that's guaranteed to work
                        page.insert_text(
                            (text_x, text_y), 
                            replacement["translated"], 
                            fontsize=font_size,  # Keep original size
                            fontname="helv",     # Helvetica is always available
                            color=color          # Keep original color
                        )
                except Exception as e:
                    print(f"  Error applying replacement: {e}")
            
            print(f"Processed {processed_spans} text spans, translated {translated_spans} on page {page_num+1}")
        
        # Save the result
        doc.save(output_path)
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