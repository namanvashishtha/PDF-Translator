#!/usr/bin/env python3

import os
import sys
import fitz  # PyMuPDF
from deep_translator import GoogleTranslator
import uuid
import time
import json

def force_translate_pdf(input_path, output_path, source_lang, target_lang):
    """
    Aggressively translate PDF by extracting and replacing all text with translated versions
    """
    print(f"FORCE TRANSLATING PDF from {source_lang} to {target_lang}")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    
    # Verify languages
    if source_lang == target_lang:
        print("Source and target languages are the same, making copy")
        import shutil
        shutil.copy(input_path, output_path)
        return True
    
    # Create debug directory
    debug_dir = "./debug_output"
    os.makedirs(debug_dir, exist_ok=True)
    
    # First test if translation works
    test_text = "This is a test sentence."
    if source_lang == "ca":
        test_text = "Aquesta és una frase de prova."
    elif source_lang == "es":
        test_text = "Esta es una frase de prueba."
    
    print(f"Testing translation from {source_lang} to {target_lang} with: '{test_text}'")
    
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translated_test = translator.translate(test_text)
        print(f"Test translation result: '{translated_test}'")
        
        # Save to debug file
        with open(f"{debug_dir}/translation_test.json", "w") as f:
            json.dump({
                "source_lang": source_lang,
                "target_lang": target_lang,
                "original": test_text,
                "translated": translated_test
            }, f, indent=2)
            
    except Exception as e:
        print(f"ERROR: Test translation failed! {str(e)}")
        print("Will try alternative method")
    
    try:
        # Load the PDF
        pdf_document = fitz.open(input_path)
        result_pdf = fitz.open()
        
        # Will store all translation results to avoid redundant calls
        translation_cache = {}
        
        # Process each page
        for page_num, page in enumerate(pdf_document):
            print(f"Processing page {page_num+1}/{len(pdf_document)}")
            
            # Create new page with same dimensions
            new_page = result_pdf.new_page(
                width=page.rect.width,
                height=page.rect.height
            )
            
            # First copy the page as-is (with images and formatting)
            new_page.show_pdf_page(
                new_page.rect,
                pdf_document,
                page_num,
                keep_proportion=True,
                overlay=False
            )
            
            # Then extract text blocks
            text_blocks = page.get_text("dict", flags=11)["blocks"]
            text_instances = []
            
            debug_blocks = []
            
            # Extract all text instances and their locations
            for block in text_blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if span["text"].strip():
                                text_instances.append({
                                    "rect": fitz.Rect(span["bbox"]),
                                    "text": span["text"],
                                    "font": span["font"],
                                    "size": span["size"],
                                    "color": span["color"]
                                })
                                debug_blocks.append({
                                    "bbox": span["bbox"],
                                    "text": span["text"],
                                    "font": span["font"],
                                    "size": span["size"],
                                })
            
            # Save debug info about blocks to a file
            with open(f"{debug_dir}/page_{page_num+1}_blocks.json", "w") as f:
                json.dump(debug_blocks, f, indent=2)
                
            # Group adjacent spans with same text for better translation
            print(f"Found {len(text_instances)} text elements on page {page_num+1}")
            
            # Track elements that have translations
            translated_positions = []
            translations = []
            
            # Try to translate each text element
            for idx, instance in enumerate(text_instances):
                original_text = instance["text"].strip()
                
                # Skip if too short (numbers, single characters)
                if len(original_text) < 3:
                    continue
                
                # Use cached translation if available
                if original_text in translation_cache:
                    translated_text = translation_cache[original_text]
                else:
                    try:
                        # Translate the text
                        translator = GoogleTranslator(source=source_lang, target=target_lang)
                        translated_text = translator.translate(original_text)
                        translation_cache[original_text] = translated_text
                        
                        # For debug - log translation
                        if idx % 10 == 0:  # Log every 10th translation to reduce output
                            print(f"  Translated ({idx+1}/{len(text_instances)}): '{original_text[:20]}...' → '{translated_text[:20]}...'")
                            
                    except Exception as e:
                        print(f"  Error translating text: {e}")
                        translated_text = original_text  # Keep original on failure
                        
                # Store in translations list to render later
                translations.append({
                    "rect": instance["rect"],
                    "original": original_text,
                    "translated": translated_text,
                    "font": instance["font"],
                    "size": instance["size"],
                    "color": instance["color"]
                })
                translated_positions.append(instance["rect"])
            
            # Save translation progress to debug file
            with open(f"{debug_dir}/page_{page_num+1}_translations.json", "w") as f:
                json.dump(translations, f, indent=2)
            
            # Create white boxes to cover original text
            for rect in translated_positions:
                # Make the rectangle slightly larger to fully cover text
                expanded_rect = fitz.Rect(
                    rect.x0 - 1, 
                    rect.y0 - 1,
                    rect.x1 + 1, 
                    rect.y1 + 1
                )
                new_page.draw_rect(expanded_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
            
            # Insert translated text
            for translation in translations:
                rect = translation["rect"]
                text = translation["translated"]
                                
                try:
                    # Insert text at the same position as original
                    new_page.insert_text(
                        point=(rect.x0, rect.y1 - 2),  # Adjust position slightly to match original
                        text=text,
                        fontsize=translation["size"] * 0.85,  # Slightly smaller to fit
                        color=translation["color"]
                    )
                except Exception as text_err:
                    print(f"  Error inserting text: {text_err}")
        
        # Save the result
        result_pdf.save(output_path)
        result_pdf.close()
        pdf_document.close()
        
        print(f"PDF force-translated and saved to: {output_path}")
        return True
        
    except Exception as e:
        import traceback
        print(f"Error during force translation: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: force_translate_pdf.py input_path output_path source_lang target_lang")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    source_lang = sys.argv[3]
    target_lang = sys.argv[4]
    
    success = force_translate_pdf(input_path, output_path, source_lang, target_lang)
    sys.exit(0 if success else 1)