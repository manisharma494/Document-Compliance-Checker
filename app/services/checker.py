from __future__ import annotations

from typing import Dict, List, Any, Optional
import language_tool_python


class ComplianceChecker:
	def __init__(self, language: str = "en-US") -> None:
		self.language = language
		self.tool: Optional[language_tool_python.LanguageToolPublicAPI] = None
		try:
			self.tool = language_tool_python.LanguageToolPublicAPI(language)
		except Exception:
			self.tool = None

	def check_text(self, text: str) -> Dict[str, Any]:
		if not self.tool:
			return {"issues": []}
		try:
			matches = self.tool.check(text)
		except Exception:
			return {"issues": []}
		issues: List[dict] = []
		for m in matches:
			repls: List[str] = []
			for r in getattr(m, "replacements", []) or []:
				value = getattr(r, "value", r)
				if isinstance(value, str):
					repls.append(value)
			issues.append(
				{
					"message": getattr(m, "message", ""),
					"rule": getattr(getattr(m, "ruleIssueType", None), "value", None) or getattr(m, "ruleId", None),
					"offset": getattr(m, "offset", 0),
					"length": getattr(m, "errorLength", 0),
					"replacements": repls[:5],
					"context": getattr(m, "context", ""),
				}
			)
		return {"issues": issues}

