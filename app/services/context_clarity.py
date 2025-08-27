import os
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ContextClarityAnalyzer:
	"""Analyzes document context clarity using OpenAI API."""
	
	def __init__(self):
		# Initialize OpenAI client with API key from environment
		api_key = os.getenv("OPENAI_API_KEY")
		if not api_key or api_key == "your_openai_api_key_here":
			logger.warning("OpenAI API key not configured. Context clarity analysis will be disabled.")
			self.client = None
			self.enabled = False
		else:
			try:
				openai.api_key = api_key
				self.client = openai.OpenAI(api_key=api_key)
				self.enabled = True
				logger.info("OpenAI client initialized successfully for context clarity analysis")
			except Exception as e:
				logger.error(f"Failed to initialize OpenAI client: {e}")
				self.client = None
				self.enabled = False
	
	def analyze_context_clarity(self, text: str, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
		"""Analyze context clarity using OpenAI API."""
		if not self.enabled or not self.client:
			return {
				"context_clarity_enabled": False,
				"message": "Context clarity analysis not available - OpenAI API key not configured"
			}
		
		try:
			# Prepare the analysis prompt
			prompt = self._create_analysis_prompt(text, issues)
			
			# Call OpenAI API
			response = self.client.chat.completions.create(
				model="gpt-3.5-turbo",
				messages=[
					{
						"role": "system",
						"content": "You are an expert document analyst specializing in context clarity and writing quality. Analyze the given text and grammar issues to provide insights on context clarity, readability, and writing flow."
					},
					{
						"role": "user",
						"content": prompt
					}
				],
				max_tokens=1000,
				temperature=0.3
			)
			
			# Extract and parse the response
			analysis = response.choices[0].message.content
			parsed_analysis = self._parse_analysis_response(analysis)
			
			return {
				"context_clarity_enabled": True,
				"analysis": parsed_analysis,
				"raw_response": analysis,
				"model_used": "gpt-3.5-turbo"
			}
			
		except Exception as e:
			logger.error(f"Error in OpenAI context clarity analysis: {e}")
			return {
				"context_clarity_enabled": True,
				"error": str(e),
				"message": "Context clarity analysis failed due to API error"
			}
	
	def _create_analysis_prompt(self, text: str, issues: List[Dict[str, Any]]) -> str:
		"""Create a comprehensive prompt for context clarity analysis."""
		# Truncate text if too long (OpenAI has token limits)
		max_text_length = 3000
		if len(text) > max_text_length:
			text = text[:max_text_length] + "... [truncated]"
		
		# Format issues for the prompt
		issues_summary = ""
		if issues:
			issues_summary = "\n\nGrammar Issues Found:\n"
			for i, issue in enumerate(issues[:10], 1):  # Limit to first 10 issues
				issues_summary += f"{i}. {issue.get('message', 'Unknown issue')}\n"
				if issue.get('context'):
					issues_summary += f"   Context: {issue['context']}\n"
		
		prompt = f"""
Please analyze the following document for context clarity and writing quality:

Document Text:
{text}

{issues_summary}

Please provide a comprehensive analysis covering:

1. **Context Clarity Score** (1-10): Rate how clear and understandable the document's context is
2. **Readability Assessment**: Evaluate the overall readability and flow
3. **Context Issues**: Identify any specific context-related problems
4. **Writing Flow**: Assess how well ideas connect and transition
5. **Audience Appropriateness**: Determine if the content is appropriate for the intended audience
6. **Specific Recommendations**: Provide actionable suggestions for improvement
7. **Overall Quality Score** (1-10): Rate the overall document quality

Format your response as a structured analysis with clear sections and specific examples from the text.
"""
		return prompt
	
	def _parse_analysis_response(self, analysis: str) -> Dict[str, Any]:
		"""Parse the OpenAI response into structured data."""
		try:
			# Extract scores using regex patterns
			import re
			
			# Extract context clarity score
			clarity_match = re.search(r'Context Clarity Score[:\s]*(\d+(?:\.\d+)?)', analysis, re.IGNORECASE)
			context_clarity_score = float(clarity_match.group(1)) if clarity_match else None
			
			# Extract overall quality score
			quality_match = re.search(r'Overall Quality Score[:\s]*(\d+(?:\.\d+)?)', analysis, re.IGNORECASE)
			overall_quality_score = float(quality_match.group(1)) if quality_match else None
			
			# Extract sections
			sections = {}
			current_section = None
			current_content = []
			
			for line in analysis.split('\n'):
				line = line.strip()
				if not line:
					continue
				
				# Check if this is a new section header
				if re.match(r'^\d+\.\s*\*\*[^*]+\*\*', line) or re.match(r'^[A-Z][^:]*:', line):
					if current_section and current_content:
						sections[current_section] = '\n'.join(current_content).strip()
					
					current_section = line.replace('*', '').replace(':', '').strip()
					current_content = []
				else:
					if current_section:
						current_content.append(line)
			
			# Add the last section
			if current_section and current_content:
				sections[current_section] = '\n'.join(current_content).strip()
			
			return {
				"context_clarity_score": context_clarity_score,
				"overall_quality_score": overall_quality_score,
				"sections": sections,
				"summary": analysis[:500] + "..." if len(analysis) > 500 else analysis
			}
			
		except Exception as e:
			logger.error(f"Error parsing analysis response: {e}")
			return {
				"raw_analysis": analysis,
				"parsing_error": str(e)
			}
	
	def enhance_grammar_analysis(self, text: str, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
		"""Enhance grammar issues with context clarity insights."""
		if not self.enabled or not self.client:
			return issues
		
		try:
			# For each issue, get context-specific improvement suggestions
			enhanced_issues = []
			
			for issue in issues:
				enhanced_issue = issue.copy()
				
				# Get context around the issue
				context = issue.get('context', '')
				if context:
					# Generate context-specific improvement
					improvement = self._get_context_improvement(context, issue.get('message', ''))
					if improvement:
						enhanced_issue['context_improvement'] = improvement
						enhanced_issue['enhanced'] = True
				
				enhanced_issues.append(enhanced_issue)
			
			return enhanced_issues
			
		except Exception as e:
			logger.error(f"Error enhancing grammar analysis: {e}")
			return issues
	
	def _get_context_improvement(self, context: str, issue_message: str) -> Optional[str]:
		"""Get context-specific improvement suggestion from OpenAI."""
		try:
			prompt = f"""
Given this grammar issue: "{issue_message}"

And this context: "{context}"

Provide a specific, context-aware improvement suggestion that maintains the intended meaning while fixing the grammar issue. Keep the suggestion concise and actionable.
"""
			
			response = self.client.chat.completions.create(
				model="gpt-3.5-turbo",
				messages=[
					{
						"role": "system",
						"content": "You are a grammar expert. Provide concise, context-aware improvement suggestions."
					},
					{
						"role": "user",
						"content": prompt
					}
				],
				max_tokens=150,
				temperature=0.2
			)
			
			return response.choices[0].message.content.strip()
			
		except Exception as e:
			logger.error(f"Error getting context improvement: {e}")
			return None
	
	def get_writing_style_analysis(self, text: str) -> Dict[str, Any]:
		"""Analyze writing style and tone."""
		if not self.enabled or not self.client:
			return {
				"enabled": False,
				"message": "Writing style analysis not available"
			}
		
		try:
			prompt = f"""
Analyze the writing style and tone of this text:

{text[:2000]}

Provide insights on:
1. Writing style (formal, informal, technical, etc.)
2. Tone (professional, casual, authoritative, etc.)
3. Sentence structure variety
4. Vocabulary level
5. Style consistency
6. Recommendations for improvement

Keep the analysis concise and structured.
"""
			
			response = self.client.chat.completions.create(
				model="gpt-3.5-turbo",
				messages=[
					{
						"role": "system",
						"content": "You are a writing style analyst. Provide clear, structured analysis of writing style and tone."
					},
					{
						"role": "user",
						"content": prompt
					}
				],
				max_tokens=500,
				temperature=0.3
			)
			
			return {
				"enabled": True,
				"analysis": response.choices[0].message.content,
				"model_used": "gpt-3.5-turbo"
			}
			
		except Exception as e:
			logger.error(f"Error in writing style analysis: {e}")
			return {
				"enabled": True,
				"error": str(e),
				"message": "Writing style analysis failed"
			}
