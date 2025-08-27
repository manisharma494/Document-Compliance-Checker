from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import io
import os
import time
import logging
from typing import Dict, Any
from contextlib import asynccontextmanager

from .services.extract import extract_text_from_upload
from .services.checker import ComplianceChecker
from .services.modify import (
	generate_corrected_text, 
	text_to_docx_bytes, 
	generate_enhanced_corrected_text,
	create_enhanced_docx_with_annotations,
	create_comparison_docx
)
from .services.cache import DocumentCache
from .services.performance import PerformanceMonitor, PerformanceMetrics
from .services.security import SecurityValidator
from .services.context_clarity import ContextClarityAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
checker = ComplianceChecker()
cache = DocumentCache()
performance_monitor = PerformanceMonitor()
security_validator = SecurityValidator()
context_analyzer = ContextClarityAnalyzer()


@asynccontextmanager
async def lifespan(app: FastAPI):
	"""Lifespan events for startup and shutdown."""
	# Startup
	logger.info("Starting Document Compliance API...")
	
	# Clear expired cache entries
	expired_count = cache.clear_expired()
	if expired_count > 0:
		logger.info(f"Cleared {expired_count} expired cache entries")
	
	# Log context clarity analyzer status
	if context_analyzer.enabled:
		logger.info("Context clarity analysis enabled with OpenAI API")
	else:
		logger.warning("Context clarity analysis disabled - OpenAI API key not configured")
	
	logger.info("Document Compliance API started successfully")
	
	yield
	
	# Shutdown
	logger.info("Shutting down Document Compliance API...")
	
	# Clear all cache entries
	cleared_count = cache.clear_all()
	if cleared_count > 0:
		logger.info(f"Cleared {cleared_count} cache entries during shutdown")
	
	logger.info("Document Compliance API shutdown complete")


app = FastAPI(title="Document Compliance API", version="1.0.0", lifespan=lifespan)

# Enable permissive CORS for ease of local testing/clients
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Mount static files - use absolute path to avoid path issues
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(os.path.dirname(current_dir), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


class AnalyzeResponse(BaseModel):
	file_name: str
	num_issues: int
	issues: list
	performance_metrics: Dict[str, Any] = {}
	security_info: Dict[str, Any] = {}
	context_clarity: Dict[str, Any] = {}
	writing_style: Dict[str, Any] = {}


class ModifyResponse(BaseModel):
	file_name: str
	message: str
	performance_metrics: Dict[str, Any] = {}
	security_info: Dict[str, Any] = {}


@app.get("/", response_class=HTMLResponse)
async def index():
	"""Serve the main frontend interface."""
	try:
		html_path = os.path.join(static_dir, "index.html")
		with open(html_path, "r", encoding="utf-8") as f:
			return HTMLResponse(content=f.read())
	except FileNotFoundError:
		return HTMLResponse(content="<h1>Frontend not found. Please check static/index.html exists.</h1>")


@app.get("/health")
async def health():
	"""Health check endpoint."""
	return {
		"status": "ok", 
		"timestamp": time.time(),
		"services": {
			"context_clarity": context_analyzer.enabled,
			"cache": True,
			"performance_monitoring": True,
			"security": True
		}
	}


@app.get("/performance")
async def get_performance_summary():
	"""Get performance metrics summary."""
	return performance_monitor.get_performance_summary()


@app.get("/cache/status")
async def get_cache_status():
	"""Get cache status and statistics."""
	return {
		"cache_enabled": True,
		"cache_directory": str(cache.cache_dir),
		"max_age_hours": cache.max_age_seconds / 3600
	}


@app.post("/cache/clear")
async def clear_cache(background_tasks: BackgroundTasks):
	"""Clear all cached data."""
	background_tasks.add_task(cache.clear_all)
	return {"message": "Cache clearing initiated", "timestamp": time.time()}


@app.get("/context-clarity/status")
async def get_context_clarity_status():
	"""Get context clarity analyzer status."""
	return {
		"enabled": context_analyzer.enabled,
		"model": "gpt-3.5-turbo" if context_analyzer.enabled else None,
		"message": "Context clarity analysis using OpenAI API" if context_analyzer.enabled else "OpenAI API key not configured"
	}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(file: UploadFile = File(...)):
	"""Analyze document for compliance issues with enhanced context clarity."""
	start_time = time.time()
	
	try:
		# Read file content for security validation and caching
		file_content = await file.read()
		file_size = len(file_content)
		
		# Security validation
		is_valid, validation_message, security_info = security_validator.validate_file(
			file_content, file.filename or "uploaded"
		)
		
		if not is_valid:
			raise HTTPException(status_code=400, detail=validation_message)
		
		# Check cache first
		cached_result = cache.get(file_content, file.filename or "uploaded")
		if cached_result:
			logger.info(f"Cache hit for file: {file.filename}")
			return AnalyzeResponse(
				file_name=file.filename or "uploaded",
				num_issues=cached_result['data']['num_issues'],
				issues=cached_result['data']['issues'],
				performance_metrics={"cache_hit": True, "response_time": time.time() - start_time},
				security_info=security_info,
				context_clarity=cached_result['data'].get('context_clarity', {}),
				writing_style=cached_result['data'].get('writing_style', {})
			)
		
		# Extract text from file
		extraction_start = time.time()
		text = await extract_text_from_upload(file_content, file.filename or "uploaded")
		extraction_time = time.time() - extraction_start
		
		# Analyze compliance
		analysis_start = time.time()
		report = checker.check_text(text)
		analysis_time = time.time() - analysis_start
		
		# Enhanced context clarity analysis using OpenAI
		context_start = time.time()
		context_analysis = context_analyzer.analyze_context_clarity(text, report["issues"])
		writing_style_analysis = context_analyzer.get_writing_style_analysis(text)
		
		# Enhance grammar issues with context-specific improvements
		enhanced_issues = context_analyzer.enhance_grammar_analysis(text, report["issues"])
		context_time = time.time() - context_start
		
		# Calculate word count
		word_count = len(text.split())
		
		# Cache the result with enhanced analysis
		cache_data = {
			'num_issues': len(enhanced_issues),
			'issues': enhanced_issues,
			'context_clarity': context_analysis,
			'writing_style': writing_style_analysis
		}
		cache.set(file_content, file.filename or "uploaded", cache_data)
		
		# Record performance metrics
		total_time = time.time() - start_time
		metrics = PerformanceMetrics(
			total_time=total_time,
			extraction_time=extraction_time,
			analysis_time=analysis_time + context_time,
			modification_time=0,
			file_size=file_size,
			word_count=word_count,
			cache_hit=False
		)
		performance_monitor.add_metrics(metrics)
		
		return AnalyzeResponse(
			file_name=file.filename or "uploaded",
			num_issues=len(enhanced_issues),
			issues=enhanced_issues,
			performance_metrics={
				"total_time": total_time,
				"extraction_time": extraction_time,
				"analysis_time": analysis_time,
				"context_analysis_time": context_time,
				"cache_hit": False
			},
			security_info=security_info,
			context_clarity=context_analysis,
			writing_style=writing_style_analysis
		)
		
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc))
	except Exception as exc:
		logger.error(f"Error analyzing document: {exc}")
		raise HTTPException(status_code=500, detail="Internal server error during analysis")


@app.post("/modify")
async def modify(
	file: UploadFile = File(...),
	format: str = Query("enhanced", description="Output format: 'enhanced', 'annotated', 'comparison', or 'basic'")
):
	"""Modify document to comply with guidelines with AI context improvements."""
	start_time = time.time()
	
	try:
		# Read file content for security validation
		file_content = await file.read()
		file_size = len(file_content)
		
		# Security validation
		is_valid, validation_message, security_info = security_validator.validate_file(
			file_content, file.filename or "uploaded"
		)
		
		if not is_valid:
			raise HTTPException(status_code=400, detail=validation_message)
		
		# Extract text
		extraction_start = time.time()
		text = await extract_text_from_upload(file_content, file.filename or "uploaded")
		extraction_time = time.time() - extraction_start
		
		# Get enhanced issues for AI improvements
		enhanced_issues = []
		if context_analyzer.enabled:
			# Analyze the text to get enhanced issues
			report = checker.check_text(text)
			enhanced_issues = context_analyzer.enhance_grammar_analysis(text, report["issues"])
		
		# Generate corrected text based on format
		modification_start = time.time()
		
		if format == "enhanced" and enhanced_issues:
			# Use AI-enhanced corrections
			corrected_text = generate_enhanced_corrected_text(text, enhanced_issues)
			output_suffix = "_ai_enhanced.docx"
		elif format == "annotated" and enhanced_issues:
			# Create annotated version with AI improvements
			docx_bytes = create_enhanced_docx_with_annotations(text, enhanced_issues)
			output_suffix = "_ai_annotated.docx"
		elif format == "comparison" and enhanced_issues:
			# Create comparison version
			docx_bytes = create_comparison_docx(text, enhanced_issues)
			output_suffix = "_ai_comparison.docx"
		else:
			# Basic grammar correction only
			corrected_text = generate_corrected_text(text)
			output_suffix = "_corrected.docx"
		
		# If not using annotated/comparison formats, create DOCX from corrected text
		if format not in ["annotated", "comparison"]:
			docx_start = time.time()
			docx_bytes = text_to_docx_bytes(corrected_text)
			docx_time = time.time() - docx_start
		else:
			docx_time = 0
		
		modification_time = time.time() - modification_start
		
		# Calculate word count
		word_count = len(text.split())
		
		# Record performance metrics
		total_time = time.time() - start_time
		metrics = PerformanceMetrics(
			total_time=total_time,
			extraction_time=extraction_time,
			analysis_time=0,
			modification_time=modification_time + docx_time,
			file_size=file_size,
			word_count=word_count,
			cache_hit=False
		)
		performance_monitor.add_metrics(metrics)
		
		# Prepare response
		filename_base, _ = os.path.splitext(file.filename or "document")
		output_name = f"{filename_base}{output_suffix}"
		
		# Sanitize filename for security
		output_name = security_validator.sanitize_filename(output_name)
		
		# Set appropriate headers based on format
		headers = {
			"Content-Disposition": f"attachment; filename=\"{output_name}\"",
			"X-Performance-Total-Time": str(total_time),
			"X-Performance-Extraction-Time": str(extraction_time),
			"X-Performance-Modification-Time": str(modification_time),
			"X-Output-Format": format,
			"X-AI-Enhanced": str(bool(enhanced_issues and format != "basic"))
		}
		
		return StreamingResponse(
			io.BytesIO(docx_bytes),
			media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
			headers=headers,
		)
		
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc))
	except Exception as exc:
		logger.error(f"Error modifying document: {exc}")
		raise HTTPException(status_code=500, detail="Internal server error during modification")


@app.get("/optimization/{file_size:int}/{word_count:int}")
async def get_optimization_recommendations(file_size: int, word_count: int):
	"""Get optimization recommendations for document processing."""
	return performance_monitor.optimize_large_documents(file_size, word_count)

