#!/usr/bin/env python3

from deep_translator import GoogleTranslator

def test_translate():
    """Test basic translation functionality"""
    print("Testing translation capabilities...")
    
    # Test text in different languages
    test_texts = {
        "es": "Hola mundo, esto es una prueba de traducción.",
        "fr": "Bonjour le monde, c'est un test de traduction.",
        "de": "Hallo Welt, dies ist ein Übersetzungstest.",
        "it": "Ciao mondo, questo è un test di traduzione.",
        "ca": "Hola món, aquesta és una prova de traducció."
    }
    
    target_lang = "en"
    
    print(f"\nTranslating to {target_lang}...\n")
    
    for source_lang, text in test_texts.items():
        print(f"Source ({source_lang}): {text}")
        
        try:
            # Initialize translator
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            
            # Translate
            translated = translator.translate(text)
            
            print(f"Translated ({target_lang}): {translated}")
            print("-" * 70)
        except Exception as e:
            print(f"Error translating from {source_lang}: {e}")
            print("-" * 70)
    
    print("\nTesting longer text...")
    
    # Test with a longer paragraph
    longer_text = """
    Aquest és un paràgraf més llarg en català que hauria de ser traduït a l'anglès.
    El sistema de traducció hauria de poder processar textos més llargs sense problemes.
    Volem assegurar-nos que la traducció funciona correctament i que el text es tradueix
    en el seu conjunt, i no només en parts petites.
    """
    
    print(f"Source (ca): {longer_text}")
    
    try:
        # Initialize translator for longer text
        translator = GoogleTranslator(source="ca", target="en")
        
        # Translate
        translated = translator.translate(longer_text)
        
        print(f"Translated (en): {translated}")
    except Exception as e:
        print(f"Error translating longer text: {e}")

if __name__ == "__main__":
    test_translate()