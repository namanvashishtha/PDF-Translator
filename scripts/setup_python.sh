#!/bin/bash

# Install Python dependencies
pip install --upgrade pip
pip install PyPDF2 pytesseract pdf2image langdetect reportlab deep-translator

# Install system dependencies for OCR
apt-get update && apt-get install -y \
  tesseract-ocr \
  tesseract-ocr-eng \
  tesseract-ocr-spa \
  tesseract-ocr-fra \
  tesseract-ocr-deu \
  tesseract-ocr-ita \
  tesseract-ocr-por \
  tesseract-ocr-jpn \
  tesseract-ocr-chi-sim \
  tesseract-ocr-rus \
  tesseract-ocr-ara \
  tesseract-ocr-hin \
  tesseract-ocr-nld \
  tesseract-ocr-kor \
  tesseract-ocr-tur \
  tesseract-ocr-swe \
  tesseract-ocr-pol \
  poppler-utils \
  libtesseract-dev

echo "Python environment setup completed"
