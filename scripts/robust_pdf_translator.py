#!/usr/bin/env python3
"""
Robust PDF Translator - A reliable PDF translation tool with layout preservation
This script provides a robust approach to PDF translation that balances layout preservation with reliability.
"""

import os
import sys
import time
import fitz  # PyMuPDF
import tempfile
import argparse
from deep_translator import GoogleTranslator
import concurrent.futures
import json
import re

def extract_text_blocks(pdf_path):
    """Extract text blocks from a PDF file"""
    blocks = []
    try:
        # Open the PDF
        doc = fitz.open(pdf_path)
        
        # Extract text blocks from each page
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_blocks = page.get_text("blocks")
            
            for block in page_blocks:
                # Each block is (x0, y0, x1, y1, text, block_no, block_type)
                if block[4].strip():  # Only include non-empty blocks
                    blocks.append({
                        "page": page_num,
                        "rect": [block[0], block[1], block[2], block[3]],
                        "text": block[4],
                        "block_no": block[5],
                        "block_type": block[6]
                    })
        
        doc.close()
        return blocks
    except Exception as e:
        print(f"Error extracting text blocks: {e}")
        return []

def translate_text(text, source_lang, target_lang):
    """Translate text from source language to target language"""
    if not text.strip():
        return ""
    
    # Skip translation if languages are the same
    if source_lang == target_lang:
        return text
    
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translated = translator.translate(text)
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        # Try with auto-detection
        try:
            print("Trying with auto-detection...")
            translator = GoogleTranslator(source='auto', target=target_lang)
            translated = translator.translate(text)
            return translated
        except Exception as auto_error:
            print(f"Auto-detection also failed: {auto_error}")
            # If all translation attempts fail, keep the original text
            return text

def translate_blocks(blocks, source_lang, target_lang, max_workers=5):
    """Translate all text blocks in parallel"""
    # Group blocks into batches to avoid too many concurrent requests
    batch_size = 5
    batches = [blocks[i:i + batch_size] for i in range(0, len(blocks), batch_size)]
    
    translated_blocks = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for batch_idx, batch in enumerate(batches):
            print(f"Translating batch {batch_idx + 1}/{len(batches)}")
            
            # Create translation tasks for this batch
            future_to_block = {}
            for block in batch:
                future = executor.submit(translate_text, block["text"], source_lang, target_lang)
                future_to_block[future] = block
            
            # Process completed translations
            for future in concurrent.futures.as_completed(future_to_block):
                block = future_to_block[future]
                try:
                    translated_text = future.result()
                    # Create a new block with the translated text
                    translated_block = block.copy()
                    translated_block["translated_text"] = translated_text
                    translated_blocks.append(translated_block)
                except Exception as e:
                    print(f"Error translating block: {e}")
                    # Keep the original text if translation fails
                    block["translated_text"] = block["text"]
                    translated_blocks.append(block)
    
    # Sort blocks by page and position
    translated_blocks.sort(key=lambda b: (b["page"], b["rect"][1], b["rect"][0]))
    return translated_blocks

def create_translated_pdf(input_path, translated_blocks, output_path):
    """Create a new PDF with translated text blocks"""
    try:
        # Open the input PDF to copy pages
        input_doc = fitz.open(input_path)
        
        # Create a new PDF document
        output_doc = fitz.open()
        
        # Group blocks by page
        blocks_by_page = {}
        for block in translated_blocks:
            page_num = block["page"]
            if page_num not in blocks_by_page:
                blocks_by_page[page_num] = []
            blocks_by_page[page_num].append(block)
        
        # Process each page
        for page_num in range(len(input_doc)):
            # Copy the original page
            page = input_doc[page_num]
            output_page = output_doc.new_page(width=page.rect.width, height=page.rect.height)
            
            # Copy the page content (images, graphics, etc.)
            output_page.show_pdf_page(output_page.rect, input_doc, page_num)
            
            # If there are translated blocks for this page, add them
            if page_num in blocks_by_page:
                for block in blocks_by_page[page_num]:
                    # Create a rectangle for the block
                    rect = fitz.Rect(block["rect"])
                    
                    # First, create a white rectangle to cover the original text
                    output_page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                    
                    # Then insert the translated text
                    try:
                        # Try with standard fonts
                        for font in ["Helvetica", "Times-Roman", "Courier"]:
                            try:
                                # Calculate font size based on rectangle size and text length
                                font_size = min(12, rect.height / 2)
                                
                                # Insert text with word wrapping
                                text_inserted = output_page.insert_textbox(
                                    rect,
                                    block["translated_text"],
                                    fontname=font,
                                    fontsize=font_size,
                                    align=0  # Left alignment
                                )
                                
                                if text_inserted >= 0:
                                    break  # Text inserted successfully
                            except Exception as font_error:
                                print(f"Error with font {font}: {font_error}")
                                continue
                        
                        # If all font attempts failed, try a simpler approach
                        if text_inserted < 0:
                            try:
                                # Just insert text at the top-left of the rectangle
                                output_page.insert_text(
                                    (rect.x0, rect.y0 + 10),
                                    block["translated_text"][:100] + ("..." if len(block["translated_text"]) > 100 else ""),
                                    fontsize=8
                                )
                            except Exception as text_error:
                                print(f"Simple text insertion failed: {text_error}")
                    except Exception as e:
                        print(f"Error inserting translated text: {e}")
        
        # Save the document
        output_doc.save(output_path)
        output_doc.close()
        input_doc.close()
        return True
    except Exception as e:
        print(f"Error creating translated PDF: {e}")
        return False

def translate_pdf(input_path, output_path, source_lang, target_lang):
    """Translate a PDF file from source language to target language"""
    start_time = time.time()
    
    print(f"Extracting text blocks from {input_path}...")
    blocks = extract_text_blocks(input_path)
    
    if not blocks:
        print("Failed to extract text blocks from PDF")
        return False
    
    print(f"Found {len(blocks)} text blocks")
    
    print(f"Translating from {source_lang} to {target_lang}...")
    translated_blocks = translate_blocks(blocks, source_lang, target_lang)
    
    print(f"Creating translated PDF at {output_path}...")
    success = create_translated_pdf(input_path, translated_blocks, output_path)
    
    elapsed_time = time.time() - start_time
    if success:
        print(f"Translation completed in {elapsed_time:.2f} seconds")
        return True
    else:
        print("Translation failed")
        return False

def main():
    parser = argparse.ArgumentParser(description="Robust PDF Translator")
    parser.add_argument("input_path", help="Path to input PDF file")
    parser.add_argument("output_path", help="Path to output PDF file")
    parser.add_argument("source_lang", help="Source language code (e.g., 'en', 'fr', 'auto')")
    parser.add_argument("target_lang", help="Target language code (e.g., 'en', 'fr')")
    
    args = parser.parse_args()
    
    success = translate_pdf(args.input_path, args.output_path, args.source_lang, args.target_lang)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()