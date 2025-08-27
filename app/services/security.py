import hashlib
import os
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class SecurityValidator:
	"""Security validation for uploaded documents."""
	
	def __init__(self):
		# Allowed file signatures (magic numbers)
		self.allowed_signatures = {
			'pdf': [b'%PDF'],
			'docx': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08']
		}
		
		# Maximum file sizes (in bytes)
		self.max_file_sizes = {
			'pdf': 50 * 1024 * 1024,  # 50MB
			'docx': 25 * 1024 * 1024   # 25MB
		}
		
		# Suspicious patterns to check
		self.suspicious_patterns = [
			b'<script',
			b'javascript:',
			b'vbscript:',
			b'<iframe',
			b'<object',
			b'<embed'
		]
	
	def validate_file(self, file_content: bytes, filename: str) -> Tuple[bool, str, Dict[str, any]]:
		"""Comprehensive file validation."""
		validation_result = {
			'filename': filename,
			'file_size': len(file_content),
			'file_hash': hashlib.sha256(file_content).hexdigest(),
			'file_type': self._detect_file_type(file_content),
			'security_checks': {}
		}
		
		# Check file size
		file_extension = self._get_file_extension(filename)
		if file_extension in self.max_file_sizes:
			if len(file_content) > self.max_file_sizes[file_extension]:
				return False, f"File too large. Maximum size: {self.max_file_sizes[file_extension] / (1024*1024):.1f}MB", validation_result
		
		# Check file signature
		if not self._validate_file_signature(file_content, file_extension):
			return False, "Invalid file signature detected", validation_result
		
		# Check for suspicious content
		suspicious_found = self._check_suspicious_content(file_content)
		if suspicious_found:
			validation_result['security_checks']['suspicious_content'] = suspicious_found
			return False, "Suspicious content detected in file", validation_result
		
		# Check file extension vs actual content
		if not self._validate_extension_match(file_content, file_extension):
			return False, "File extension does not match file content", validation_result
		
		# Additional security checks
		validation_result['security_checks'] = {
			'file_integrity': self._check_file_integrity(file_content),
			'content_analysis': self._analyze_content_security(file_content),
			'risk_score': self._calculate_risk_score(file_content, file_extension)
		}
		
		return True, "File validation passed", validation_result
	
	def _detect_file_type(self, content: bytes) -> str:
		"""Detect file type using magic numbers."""
		try:
			# Use basic magic number detection
			if len(content) >= 4:
				if content.startswith(b'%PDF'):
					return 'pdf'
				elif content.startswith(b'PK\x03\x04') or content.startswith(b'PK\x05\x06'):
					return 'docx'
			return 'unknown'
		except Exception:
			return 'unknown'
	
	def _get_file_extension(self, filename: str) -> str:
		"""Extract file extension from filename."""
		return Path(filename).suffix.lower().lstrip('.')
	
	def _validate_file_signature(self, content: bytes, expected_type: str) -> bool:
		"""Validate file signature against expected type."""
		if expected_type not in self.allowed_signatures:
			return False
		
		for signature in self.allowed_signatures[expected_type]:
			if content.startswith(signature):
				return True
		
		return False
	
	def _check_suspicious_content(self, content: bytes) -> List[str]:
		"""Check for suspicious content patterns."""
		suspicious_found = []
		content_lower = content.lower()
		
		for pattern in self.suspicious_patterns:
			if pattern.lower() in content_lower:
				suspicious_found.append(f"Pattern '{pattern.decode()}' detected")
		
		return suspicious_found
	
	def _validate_extension_match(self, content: bytes, extension: str) -> bool:
		"""Validate that file extension matches actual content."""
		detected_type = self._detect_file_type(content)
		
		if extension == 'pdf' and detected_type == 'pdf':
			return True
		elif extension == 'docx' and detected_type == 'docx':
			return True
		
		return False
	
	def _check_file_integrity(self, content: bytes) -> Dict[str, any]:
		"""Check file integrity and structure."""
		integrity_checks = {
			'file_size_valid': len(content) > 0,
			'content_readable': self._is_content_readable(content),
			'structure_valid': True
		}
		
		# Check if content is readable text (for text-based files)
		if content.startswith(b'%PDF'):
			integrity_checks['pdf_structure'] = self._validate_pdf_structure(content)
		elif content.startswith(b'PK'):
			integrity_checks['docx_structure'] = self._validate_docx_structure(content)
		
		return integrity_checks
	
	def _is_content_readable(self, content: bytes) -> bool:
		"""Check if content contains readable text."""
		try:
			# Check if content contains printable ASCII characters
			printable_chars = sum(1 for b in content if 32 <= b <= 126)
			return printable_chars > len(content) * 0.1  # At least 10% printable
		except Exception:
			return False
	
	def _validate_pdf_structure(self, content: bytes) -> bool:
		"""Basic PDF structure validation."""
		try:
			# Check for PDF header and trailer
			has_header = b'%PDF' in content
			has_trailer = b'trailer' in content or b'startxref' in content
			return has_header and has_trailer
		except Exception:
			return False
	
	def _validate_docx_structure(self, content: bytes) -> bool:
		"""Basic DOCX structure validation."""
		try:
			# Check for ZIP file structure indicators
			has_pk_header = b'PK\x03\x04' in content
			has_content_types = b'[Content_Types].xml' in content
			return has_pk_header and has_content_types
		except Exception:
			return False
	
	def _analyze_content_security(self, content: bytes) -> Dict[str, any]:
		"""Analyze content for security risks."""
		analysis = {
			'executable_code': False,
			'external_links': False,
			'embedded_objects': False,
			'macro_content': False
		}
		
		content_str = content.decode('utf-8', errors='ignore').lower()
		
		# Check for executable code patterns
		if any(pattern in content_str for pattern in ['<script', 'javascript:', 'vbscript:']):
			analysis['executable_code'] = True
		
		# Check for external links
		if any(pattern in content_str for pattern in ['http://', 'https://', 'ftp://']):
			analysis['external_links'] = True
		
		# Check for embedded objects
		if any(pattern in content_str for pattern in ['<object', '<embed', '<iframe']):
			analysis['embedded_objects'] = True
		
		# Check for macro content (Office documents)
		if any(pattern in content_str for pattern in ['vba', 'macro', 'vbscript']):
			analysis['macro_content'] = True
		
		return analysis
	
	def _calculate_risk_score(self, content: bytes, file_type: str) -> int:
		"""Calculate security risk score (0-100)."""
		risk_score = 0
		
		# Base risk by file type
		if file_type == 'pdf':
			risk_score += 10
		elif file_type == 'docx':
			risk_score += 15
		
		# Content-based risk
		content_analysis = self._analyze_content_security(content)
		if content_analysis['executable_code']:
			risk_score += 40
		if content_analysis['embedded_objects']:
			risk_score += 25
		if content_analysis['macro_content']:
			risk_score += 30
		if content_analysis['external_links']:
			risk_score += 15
		
		# File size risk
		if len(content) > 10 * 1024 * 1024:  # 10MB
			risk_score += 10
		
		return min(risk_score, 100)
	
	def sanitize_filename(self, filename: str) -> str:
		"""Sanitize filename for security."""
		# Remove path traversal attempts
		filename = os.path.basename(filename)
		
		# Remove dangerous characters
		dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
		for char in dangerous_chars:
			filename = filename.replace(char, '_')
		
		# Limit length
		if len(filename) > 100:
			name, ext = os.path.splitext(filename)
			filename = name[:95] + ext
		
		return filename
