"""
AI Service - Daily Logger Assist

Service for AI-powered content analysis using OpenRoute API.
"""

from typing import List, Dict, Any, Optional
import aiohttp
import asyncio
import json
from datetime import datetime
from loguru import logger

from app.config import settings

class AIService:
    """AI integration service using OpenRoute API"""
    
    def __init__(self):
        self.api_key = settings.OPENROUTE_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_model = "microsoft/wizardlm-2-8x22b"
        
    async def analyze_content_for_work_items(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze content to extract work items and activities.
        
        Args:
            content: Text content to analyze (message, email)
            context: Optional context information (sender, timestamp, etc.)
            
        Returns:
            List[Dict[str, Any]]: Extracted work items
        """
        try:
            prompt = self._build_work_analysis_prompt(content, context)
            
            response = await self._call_openroute_api(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.3
            )
            
            if response:
                return self._parse_work_items_response(response)
            
            return []
            
        except Exception as e:
            logger.error(f"Work analysis failed: {e}")
            return []
    
    async def estimate_time_for_task(
        self,
        task_description: str,
        task_type: Optional[str] = None,
        complexity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Estimate time required for a task using AI.
        
        Args:
            task_description: Description of the task
            task_type: Type of task (development, testing, meeting, etc.)
            complexity: Task complexity (low, medium, high)
            
        Returns:
            Dict[str, Any]: Time estimate and confidence
        """
        try:
            prompt = self._build_time_estimation_prompt(task_description, task_type, complexity)
            
            response = await self._call_openroute_api(
                prompt=prompt,
                max_tokens=500,
                temperature=0.2
            )
            
            if response:
                return self._parse_time_estimate_response(response)
            
            return {"estimated_hours": 1.0, "confidence": "low", "reasoning": "Default estimate"}
            
        except Exception as e:
            logger.error(f"Time estimation failed: {e}")
            return {"estimated_hours": 1.0, "confidence": "low", "reasoning": "Error in estimation"}
    
    async def match_content_to_jira_tickets(
        self,
        content: str,
        available_tickets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Match content to relevant JIRA tickets using AI.
        
        Args:
            content: Content to analyze
            available_tickets: List of available JIRA tickets
            
        Returns:
            List[Dict[str, Any]]: Matched tickets with confidence scores
        """
        try:
            if not available_tickets:
                return []
            
            prompt = self._build_ticket_matching_prompt(content, available_tickets)
            
            response = await self._call_openroute_api(
                prompt=prompt,
                max_tokens=800,
                temperature=0.3
            )
            
            if response:
                return self._parse_ticket_matches_response(response, available_tickets)
            
            return []
            
        except Exception as e:
            logger.error(f"Ticket matching failed: {e}")
            return []
    
    async def generate_daily_summary(
        self,
        work_items: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        date: datetime
    ) -> Dict[str, Any]:
        """
        Generate a daily work summary using AI.
        
        Args:
            work_items: List of work items for the day
            messages: List of messages/communications
            date: Date for the summary
            
        Returns:
            Dict[str, Any]: Generated summary with insights
        """
        try:
            prompt = self._build_summary_prompt(work_items, messages, date)
            
            response = await self._call_openroute_api(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.4
            )
            
            if response:
                return self._parse_summary_response(response)
            
            return {"summary": "No summary available", "key_achievements": [], "insights": []}
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return {"summary": "Error generating summary", "key_achievements": [], "insights": []}
    
    async def _call_openroute_api(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.3,
        model: Optional[str] = None
    ) -> Optional[str]:
        """
        Call OpenRoute API with the given prompt.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            model: Model to use (optional)
            
        Returns:
            Optional[str]: API response content
        """
        try:
            if not self.api_key:
                logger.error("OpenRoute API key not configured")
                return None
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model or self.default_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            url = f"{self.base_url}/chat/completions"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        return content.strip()
                    else:
                        logger.error(f"OpenRoute API error: {response.status}")
                        error_text = await response.text()
                        logger.error(f"Error details: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"OpenRoute API call failed: {e}")
            return None
    
    def _build_work_analysis_prompt(self, content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Build prompt for work item analysis."""
        
        context_info = ""
        if context:
            sender = context.get("sender", "Unknown")
            timestamp = context.get("timestamp", "")
            source = context.get("source", "")
            context_info = f"\nContext: From {sender} via {source} at {timestamp}"
        
        return f"""
Analyze the following communication content and extract work items, tasks, and activities that could be logged for daily work tracking.

Content:{context_info}
"{content}"

Please identify and extract:
1. Specific tasks or work activities mentioned
2. Time spent on activities (if mentioned)
3. Project or ticket references
4. Meeting activities
5. Development, testing, or deployment work
6. Problem-solving or troubleshooting activities

For each work item found, provide:
- activity_type: (development, testing, meeting, review, planning, troubleshooting, documentation, other)
- description: Brief description of the work
- estimated_time: Estimated time in hours (if not mentioned, provide reasonable estimate)
- project_reference: Any project/ticket mentioned
- priority: (high, medium, low)

Respond in JSON format as an array of work items:
[
  {{
    "activity_type": "development",
    "description": "Fixed login bug",
    "estimated_time": 2.0,
    "project_reference": "PROJ-123",
    "priority": "high"
  }}
]

If no work items are found, return an empty array [].
"""
    
    def _build_time_estimation_prompt(
        self, 
        task_description: str, 
        task_type: Optional[str] = None, 
        complexity: Optional[str] = None
    ) -> str:
        """Build prompt for time estimation."""
        
        type_info = f" (Type: {task_type})" if task_type else ""
        complexity_info = f" (Complexity: {complexity})" if complexity else ""
        
        return f"""
Estimate the time required for the following task{type_info}{complexity_info}:

Task: "{task_description}"

Consider:
- Task complexity and scope
- Typical time for similar tasks
- Potential challenges or unknowns
- Testing and documentation time if applicable

Provide a realistic time estimate in hours and explain your reasoning.

Respond in JSON format:
{{
  "estimated_hours": 2.5,
  "confidence": "medium",
  "reasoning": "This task involves...",
  "breakdown": {{
    "development": 1.5,
    "testing": 0.5,
    "documentation": 0.5
  }}
}}

Confidence levels: low, medium, high
"""
    
    def _build_ticket_matching_prompt(self, content: str, tickets: List[Dict[str, Any]]) -> str:
        """Build prompt for JIRA ticket matching."""
        
        tickets_info = ""
        for i, ticket in enumerate(tickets[:10]):  # Limit to 10 tickets
            tickets_info += f"{i+1}. {ticket.get('ticket_key', 'N/A')} - {ticket.get('title', 'No title')}\n"
            if ticket.get('description'):
                tickets_info += f"   Description: {ticket.get('description', '')[:200]}...\n"
        
        return f"""
Analyze the following content and match it to relevant JIRA tickets.

Content: "{content}"

Available JIRA tickets:
{tickets_info}

For each relevant ticket, consider:
- Keywords and topic similarity
- Project context
- Task type alignment
- Specific references

Respond in JSON format with matched tickets and confidence scores:
[
  {{
    "ticket_key": "PROJ-123",
    "confidence": 0.85,
    "reasoning": "Content mentions login issues which matches this bug fix ticket"
  }}
]

Only include matches with confidence > 0.3. If no matches found, return [].
"""
    
    def _build_summary_prompt(
        self, 
        work_items: List[Dict[str, Any]], 
        messages: List[Dict[str, Any]], 
        date: datetime
    ) -> str:
        """Build prompt for daily summary generation."""
        
        date_str = date.strftime("%Y-%m-%d")
        
        work_summary = ""
        if work_items:
            for item in work_items[:20]:  # Limit items
                work_summary += f"- {item.get('description', 'N/A')} ({item.get('estimated_time', 0)}h)\n"
        else:
            work_summary = "No work items recorded"
        
        comm_count = len(messages)
        
        return f"""
Generate a comprehensive daily work summary for {date_str}.

Work Items Completed:
{work_summary}

Communication Activity: {comm_count} messages/emails processed

Please provide:
1. A concise summary of the day's work
2. Key achievements and accomplishments
3. Time allocation across different activities
4. Notable insights or patterns
5. Areas that required significant time/effort

Focus on professional accomplishments and productivity insights.

Respond in JSON format:
{{
  "summary": "Brief overview of the day's work...",
  "key_achievements": ["Achievement 1", "Achievement 2"],
  "time_breakdown": {{
    "development": 4.0,
    "meetings": 2.0,
    "testing": 1.5,
    "other": 0.5
  }},
  "insights": ["Insight 1", "Insight 2"],
  "total_productive_hours": 8.0
}}
"""
    
    def _parse_work_items_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response for work items."""
        try:
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:-3]
            elif response.startswith("```"):
                response = response[3:-3]
            
            work_items = json.loads(response)
            
            # Validate and normalize work items
            normalized_items = []
            for item in work_items:
                if isinstance(item, dict) and item.get("description"):
                    normalized_item = {
                        "activity_type": item.get("activity_type", "other"),
                        "description": item.get("description", ""),
                        "estimated_time": float(item.get("estimated_time", 1.0)),
                        "project_reference": item.get("project_reference"),
                        "priority": item.get("priority", "medium")
                    }
                    normalized_items.append(normalized_item)
            
            return normalized_items
            
        except Exception as e:
            logger.error(f"Error parsing work items response: {e}")
            return []
    
    def _parse_time_estimate_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for time estimation."""
        try:
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:-3]
            elif response.startswith("```"):
                response = response[3:-3]
            
            estimate = json.loads(response)
            
            return {
                "estimated_hours": float(estimate.get("estimated_hours", 1.0)),
                "confidence": estimate.get("confidence", "medium"),
                "reasoning": estimate.get("reasoning", ""),
                "breakdown": estimate.get("breakdown", {})
            }
            
        except Exception as e:
            logger.error(f"Error parsing time estimate response: {e}")
            return {"estimated_hours": 1.0, "confidence": "low", "reasoning": "Parse error"}
    
    def _parse_ticket_matches_response(
        self, 
        response: str, 
        available_tickets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse AI response for ticket matching."""
        try:
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:-3]
            elif response.startswith("```"):
                response = response[3:-3]
            
            matches = json.loads(response)
            
            # Validate matches against available tickets
            valid_matches = []
            ticket_keys = {t.get("ticket_key") for t in available_tickets}
            
            for match in matches:
                if (isinstance(match, dict) and 
                    match.get("ticket_key") in ticket_keys and
                    match.get("confidence", 0) > 0.3):
                    valid_matches.append(match)
            
            return valid_matches
            
        except Exception as e:
            logger.error(f"Error parsing ticket matches response: {e}")
            return []
    
    def _parse_summary_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for daily summary."""
        try:
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:-3]
            elif response.startswith("```"):
                response = response[3:-3]
            
            summary = json.loads(response)
            
            return {
                "summary": summary.get("summary", ""),
                "key_achievements": summary.get("key_achievements", []),
                "time_breakdown": summary.get("time_breakdown", {}),
                "insights": summary.get("insights", []),
                "total_productive_hours": float(summary.get("total_productive_hours", 0))
            }
            
        except Exception as e:
            logger.error(f"Error parsing summary response: {e}")
            return {"summary": "Parse error", "key_achievements": [], "insights": []}
    
    async def test_connection(self) -> bool:
        """Test if AI service is working."""
        try:
            response = await self._call_openroute_api(
                prompt="Respond with 'OK' if you can process this request.",
                max_tokens=10,
                temperature=0
            )
            return response and "OK" in response
        except Exception as e:
            logger.error(f"AI service test failed: {e}")
            return False 