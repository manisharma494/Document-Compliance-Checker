from fastapi import UploadFile
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document
import tempfile
import os
import re
from typing import Union


SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def clean_extracted_text(text: str) -> str:
	"""Clean extracted text to remove problematic characters."""
	if not text:
		return ""
	
	# Remove NULL bytes and control characters (except newlines and tabs)
	cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
	
	# Normalize whitespace
	cleaned = re.sub(r'\s+', ' ', cleaned)
	
	# Remove leading/trailing whitespace
	cleaned = cleaned.strip()
	
	return cleaned


async def extract_text_from_upload(upload: Union[UploadFile, bytes], filename: str = None) -> str:
	"""Extract text from uploaded file content or UploadFile."""
	
	# Handle both UploadFile and bytes
	if isinstance(upload, UploadFile):
		file_content = await upload.read()
		filename = upload.filename or filename or "uploaded"
	else:
		file_content = upload
		filename = filename or "uploaded"
	
	# Determine file type
	_, ext = os.path.splitext(filename.lower())
	if ext not in SUPPORTED_EXTENSIONS:
		raise ValueError("Unsupported file type. Please upload a PDF or DOCX file.")

	# Write to a temporary file to support libraries expecting file paths
	with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
		tmp.write(file_content)
		tmp_path = tmp.name

	try:
		if ext == ".pdf":
			text = pdf_extract_text(tmp_path) or ""
		else:  # .docx
			doc = Document(tmp_path)
			text = "\n".join(p.text for p in doc.paragraphs)
	finally:
		try:
			os.unlink(tmp_path)
		except OSError:
			pass

	# Clean the extracted text
	text = clean_extracted_text(text)
	
	if not text:
		raise ValueError("No extractable text found in the uploaded document.")

	return text


def get_word_count(text: str) -> int:
	"""Get word count from text."""
	if not text:
		return 0
	
	# Split by whitespace and count non-empty words
	words = [word for word in text.split() if word.strip()]
	return len(words)


def get_document_stats(text: str) -> dict:
	"""Get comprehensive document statistics."""
	if not text:
		return {
			"word_count": 0,
			"character_count": 0,
			"line_count": 0,
			"paragraph_count": 0,
			"average_words_per_line": 0
		}
	
	lines = text.split('\n')
	paragraphs = [p for p in lines if p.strip()]
	words = [word for word in text.split() if word.strip()]
	
	avg_words_per_line = len(words) / len(lines) if lines else 0
	
	return {
		"word_count": len(words),
		"character_count": len(text),
		"line_count": len(lines),
		"paragraph_count": len(paragraphs),
		"average_words_per_line": round(avg_words_per_line, 2)
	}

