"""
AI Service - Daily Logger Assist

Enhanced AI service with advanced content analysis, intelligent categorization,
and productivity analytics for Phase 3.
"""

from typing import List, Dict, Any, Optional, Tuple
import aiohttp
import asyncio
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger

from app.config import settings

class AIService:
    """Enhanced AI integration service using OpenRoute API"""
    
    def __init__(self):
        self.api_key = settings.OPENROUTE_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_model = "microsoft/wizardlm-2-8x22b"
        self.context_model = "anthropic/claude-3-haiku"  # For faster context analysis
        
        # Enhanced context tracking
        self.user_patterns = {}
        self.historical_estimates = defaultdict(list)
        self.project_contexts = {}
        
    async def analyze_content_with_context(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhanced content analysis with deep context awareness.
        
        Args:
            content: Text content to analyze
            context: Rich context information
            user_id: User ID for personalized analysis
            
        Returns:
            Dict[str, Any]: Comprehensive analysis results
        """
        try:
            # Build rich context
            enriched_context = await self._build_enriched_context(context, user_id)
            
            # Multi-step analysis
            analysis = {
                "work_items": await self.analyze_content_for_work_items(content, enriched_context),
                "sentiment_analysis": await self._analyze_sentiment(content),
                "urgency_detection": await self._detect_urgency(content),
                "skill_classification": await self._classify_skills_required(content),
                "collaboration_patterns": await self._detect_collaboration_patterns(content, context),
                "productivity_indicators": await self._extract_productivity_indicators(content)
            }
            
            # Update user patterns for future analysis
            if user_id:
                await self._update_user_patterns(user_id, analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Enhanced content analysis failed: {e}")
            return {"work_items": [], "error": str(e)}
    
    async def intelligent_task_categorization(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Intelligent task categorization with priority and complexity assessment.
        
        Args:
            task_description: Task to categorize
            context: Additional context information
            
        Returns:
            Dict[str, Any]: Detailed categorization results
        """
        try:
            prompt = self._build_categorization_prompt(task_description, context)
            
            response = await self._call_openroute_api(
                prompt=prompt,
                max_tokens=800,
                temperature=0.2,
                model=self.context_model
            )
            
            if response:
                return self._parse_categorization_response(response)
            
            return self._default_categorization()
            
        except Exception as e:
            logger.error(f"Task categorization failed: {e}")
            return self._default_categorization()
    
    async def enhanced_time_estimation(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        use_historical_data: bool = True
    ) -> Dict[str, Any]:
        """
        Enhanced time estimation using historical data and machine learning insights.
        
        Args:
            task_description: Task to estimate
            context: Task context
            user_id: User for personalized estimation
            use_historical_data: Whether to use historical estimates
            
        Returns:
            Dict[str, Any]: Enhanced time estimation with confidence intervals
        """
        try:
            # Get categorization first
            categorization = await self.intelligent_task_categorization(task_description, context)
            
            # Build enhanced prompt with historical data
            historical_context = ""
            if use_historical_data and user_id:
                historical_context = self._get_historical_context(
                    user_id, 
                    categorization.get("category", "development")
                )
            
            prompt = self._build_enhanced_time_estimation_prompt(
                task_description, 
                categorization, 
                historical_context,
                context
            )
            
            response = await self._call_openroute_api(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.1
            )
            
            if response:
                estimation = self._parse_enhanced_time_estimate_response(response)
                
                # Store for future historical analysis
                if user_id:
                    self._store_time_estimate(user_id, categorization.get("category"), estimation)
                
                return estimation
            
            return self._default_time_estimate()
            
        except Exception as e:
            logger.error(f"Enhanced time estimation failed: {e}")
            return self._default_time_estimate()
    
    async def automated_jira_work_logging(
        self,
        work_items: List[Dict[str, Any]],
        jira_tickets: List[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Automated JIRA work logging with intelligent time distribution.
        
        Args:
            work_items: Extracted work items
            jira_tickets: Available JIRA tickets
            user_preferences: User logging preferences
            
        Returns:
            Dict[str, Any]: Work log recommendations and automation results
        """
        try:
            # Enhanced ticket matching with confidence scoring
            matched_items = []
            
            for work_item in work_items:
                matches = await self.match_content_to_jira_tickets(
                    work_item.get("description", ""), 
                    jira_tickets
                )
                
                # Smart time distribution
                distributed_time = await self._smart_time_distribution(
                    work_item, 
                    matches,
                    user_preferences
                )
                
                matched_items.append({
                    "work_item": work_item,
                    "ticket_matches": matches,
                    "time_distribution": distributed_time,
                    "automation_confidence": self._calculate_automation_confidence(matches, work_item)
                })
            
            # Generate work log recommendations
            recommendations = await self._generate_work_log_recommendations(matched_items)
            
            return {
                "matched_items": matched_items,
                "recommendations": recommendations,
                "total_time_logged": sum(item["work_item"].get("estimated_time", 0) for item in matched_items),
                "automation_rate": self._calculate_automation_rate(matched_items)
            }
            
        except Exception as e:
            logger.error(f"Automated work logging failed: {e}")
            return {"error": str(e), "matched_items": []}
    
    async def productivity_analytics(
        self,
        work_items: List[Dict[str, Any]],
        timeframe: str = "daily",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate productivity analytics and insights.
        
        Args:
            work_items: Work items to analyze
            timeframe: Analysis timeframe (daily, weekly, monthly)
            user_id: User for personalized analytics
            
        Returns:
            Dict[str, Any]: Comprehensive productivity analytics
        """
        try:
            prompt = self._build_productivity_analytics_prompt(work_items, timeframe, user_id)
            
            response = await self._call_openroute_api(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.3
            )
            
            if response:
                analytics = self._parse_productivity_analytics_response(response)
                
                # Add calculated metrics
                analytics.update(self._calculate_productivity_metrics(work_items))
                
                return analytics
            
            return self._default_productivity_analytics()
            
        except Exception as e:
            logger.error(f"Productivity analytics failed: {e}")
            return self._default_productivity_analytics()
    
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

    # ==================== ENHANCED AI METHODS ====================
    
    async def _build_enriched_context(
        self, 
        context: Optional[Dict[str, Any]] = None, 
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build enriched context for enhanced analysis."""
        enriched = context.copy() if context else {}
        
        if user_id and user_id in self.user_patterns:
            enriched["user_patterns"] = self.user_patterns[user_id]
        
        # Add temporal context
        enriched["time_of_day"] = datetime.now().strftime("%H:%M")
        enriched["day_of_week"] = datetime.now().strftime("%A")
        
        return enriched
    
    async def _analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """Analyze sentiment and emotional tone of content."""
        try:
            prompt = f"""
Analyze the sentiment and emotional tone of this content:

"{content}"

Provide:
- sentiment: (positive, neutral, negative)
- confidence: (0.0 to 1.0)
- emotional_tone: (frustrated, excited, concerned, neutral, etc.)
- urgency_indicators: any urgent language detected

Respond in JSON format:
{{
  "sentiment": "neutral",
  "confidence": 0.8,
  "emotional_tone": "professional",
  "urgency_indicators": []
}}
"""
            
            response = await self._call_openroute_api(
                prompt=prompt,
                max_tokens=300,
                temperature=0.1,
                model=self.context_model
            )
            
            if response:
                return self._parse_json_response(response, {
                    "sentiment": "neutral",
                    "confidence": 0.5,
                    "emotional_tone": "neutral",
                    "urgency_indicators": []
                })
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
        
        return {"sentiment": "neutral", "confidence": 0.5, "emotional_tone": "neutral", "urgency_indicators": []}
    
    async def _detect_urgency(self, content: str) -> Dict[str, Any]:
        """Detect urgency and priority indicators in content."""
        urgency_keywords = {
            "high": ["urgent", "asap", "immediately", "critical", "emergency", "urgent!", "now"],
            "medium": ["soon", "priority", "important", "needed", "please"],
            "low": ["when you can", "eventually", "sometime", "no rush"]
        }
        
        content_lower = content.lower()
        urgency_score = 0
        detected_keywords = []
        
        for level, keywords in urgency_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    detected_keywords.append(keyword)
                    if level == "high":
                        urgency_score += 3
                    elif level == "medium":
                        urgency_score += 1
                    else:
                        urgency_score -= 1
        
        urgency_level = "low"
        if urgency_score >= 3:
            urgency_level = "high"
        elif urgency_score >= 1:
            urgency_level = "medium"
        
        return {
            "urgency_level": urgency_level,
            "urgency_score": urgency_score,
            "detected_keywords": detected_keywords
        }
    
    async def _classify_skills_required(self, content: str) -> List[str]:
        """Classify technical skills required based on content."""
        skill_patterns = {
            "programming": ["code", "coding", "programming", "development", "implementation"],
            "testing": ["test", "testing", "qa", "quality", "bug", "debugging"],
            "devops": ["deploy", "deployment", "docker", "kubernetes", "ci/cd", "pipeline"],
            "database": ["database", "sql", "query", "migration", "schema"],
            "frontend": ["ui", "ux", "frontend", "react", "vue", "angular", "css", "html"],
            "backend": ["api", "backend", "server", "microservice", "rest"],
            "design": ["design", "mockup", "wireframe", "prototype", "user experience"],
            "documentation": ["documentation", "docs", "readme", "guide", "manual"],
            "meeting": ["meeting", "standup", "review", "discussion", "call"]
        }
        
        content_lower = content.lower()
        detected_skills = []
        
        for skill, keywords in skill_patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                detected_skills.append(skill)
        
        return detected_skills
    
    async def _detect_collaboration_patterns(
        self, 
        content: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Detect collaboration patterns and team interactions."""
        patterns = {
            "mentioned_people": len(re.findall(r'@\w+', content)),
            "questions_asked": len(re.findall(r'\?', content)),
            "action_items": len(re.findall(r'\b(todo|action|task|need to)\b', content.lower())),
            "decisions_made": len(re.findall(r'\b(decided|decision|agreed|conclude)\b', content.lower())),
            "blockers": len(re.findall(r'\b(blocked|blocker|issue|problem|stuck)\b', content.lower()))
        }
        
        collaboration_type = "individual"
        if patterns["mentioned_people"] > 0 or patterns["questions_asked"] > 2:
            collaboration_type = "collaborative"
        
        return {
            "collaboration_type": collaboration_type,
            "patterns": patterns
        }
    
    async def _extract_productivity_indicators(self, content: str) -> Dict[str, Any]:
        """Extract productivity indicators from content."""
        completion_indicators = len(re.findall(r'\b(completed|finished|done|fixed|resolved)\b', content.lower()))
        progress_indicators = len(re.findall(r'\b(working on|in progress|started|begun)\b', content.lower()))
        planning_indicators = len(re.findall(r'\b(plan|planning|will|going to|next)\b', content.lower()))
        
        productivity_score = completion_indicators * 3 + progress_indicators * 2 + planning_indicators
        
        return {
            "productivity_score": productivity_score,
            "completion_indicators": completion_indicators,
            "progress_indicators": progress_indicators,
            "planning_indicators": planning_indicators
        }
    
    async def _update_user_patterns(self, user_id: str, analysis: Dict[str, Any]) -> None:
        """Update user patterns for personalized analysis."""
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = {
                "common_skills": defaultdict(int),
                "typical_work_hours": [],
                "productivity_trends": [],
                "preferred_categories": defaultdict(int)
            }
        
        patterns = self.user_patterns[user_id]
        
        # Update skill frequency
        for skill in analysis.get("skill_classification", []):
            patterns["common_skills"][skill] += 1
        
        # Update productivity trends
        productivity = analysis.get("productivity_indicators", {})
        patterns["productivity_trends"].append({
            "timestamp": datetime.now().isoformat(),
            "score": productivity.get("productivity_score", 0)
        })
        
        # Keep only last 100 entries
        patterns["productivity_trends"] = patterns["productivity_trends"][-100:]
    
    def _build_categorization_prompt(
        self, 
        task_description: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build prompt for intelligent task categorization."""
        context_info = ""
        if context:
            context_info = f"\nContext: {json.dumps(context, indent=2)}"
        
        return f"""
Analyze and categorize this task with detailed classification:

Task: "{task_description}"{context_info}

Provide comprehensive categorization including:

1. Primary Category: (development, testing, design, documentation, meeting, planning, support, maintenance, research)
2. Secondary Categories: (if applicable)
3. Technical Domain: (frontend, backend, database, devops, mobile, etc.)
4. Complexity Level: (trivial, simple, moderate, complex, expert)
5. Priority Level: (low, medium, high, critical)
6. Estimated Effort Level: (quick, short, medium, long, extended)
7. Required Skills: List of technical skills needed
8. Risk Factors: Potential challenges or blockers
9. Dependencies: What this task depends on

Respond in JSON format:
{{
  "category": "development",
  "secondary_categories": ["testing"],
  "technical_domain": "backend",
  "complexity": "moderate",
  "priority": "medium",
  "effort_level": "medium",
  "required_skills": ["python", "api", "database"],
  "risk_factors": ["unclear requirements"],
  "dependencies": ["database schema"],
  "confidence": 0.85
}}
"""
    
    def _build_enhanced_time_estimation_prompt(
        self,
        task_description: str,
        categorization: Dict[str, Any],
        historical_context: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build enhanced prompt for time estimation."""
        return f"""
Provide detailed time estimation for this task using advanced analysis:

Task: "{task_description}"

Task Classification:
- Category: {categorization.get('category', 'unknown')}
- Complexity: {categorization.get('complexity', 'moderate')}
- Technical Domain: {categorization.get('technical_domain', 'general')}
- Required Skills: {categorization.get('required_skills', [])}

{historical_context}

Consider:
1. Base effort for this type and complexity
2. Setup and context switching time
3. Testing and validation time
4. Documentation and communication time
5. Potential rework and iteration
6. Integration and deployment considerations

Provide estimates with confidence intervals:

{{
  "estimated_hours": 4.5,
  "confidence_interval": {{
    "min": 3.0,
    "max": 6.0,
    "confidence": 0.8
  }},
  "breakdown": {{
    "analysis": 0.5,
    "implementation": 3.0,
    "testing": 0.5,
    "documentation": 0.25,
    "review": 0.25
  }},
  "risk_factors": ["unclear requirements might add 1-2 hours"],
  "assumptions": ["assumes existing test framework"],
  "historical_accuracy": "medium"
}}
"""
    
    def _get_historical_context(self, user_id: str, category: str) -> str:
        """Get historical context for time estimation."""
        if user_id not in self.historical_estimates:
            return "Historical Context: No previous estimates available."
        
        estimates = self.historical_estimates[user_id]
        category_estimates = [e for e in estimates if e.get("category") == category]
        
        if not category_estimates:
            return f"Historical Context: No previous {category} estimates available."
        
        recent_estimates = category_estimates[-5:]  # Last 5 estimates
        avg_time = sum(e.get("estimated_hours", 0) for e in recent_estimates) / len(recent_estimates)
        
        return f"""
Historical Context for {category} tasks:
- Recent estimates: {len(recent_estimates)} tasks
- Average time: {avg_time:.1f} hours
- Typical range: {min(e.get('estimated_hours', 0) for e in recent_estimates):.1f} - {max(e.get('estimated_hours', 0) for e in recent_estimates):.1f} hours
"""
    
    def _store_time_estimate(self, user_id: str, category: str, estimation: Dict[str, Any]) -> None:
        """Store time estimate for historical analysis."""
        estimate_record = {
            "category": category,
            "estimated_hours": estimation.get("estimated_hours", 0),
            "timestamp": datetime.now().isoformat(),
            "confidence": estimation.get("confidence_interval", {}).get("confidence", 0)
        }
        
        self.historical_estimates[user_id].append(estimate_record)
        
        # Keep only last 50 estimates per user
        self.historical_estimates[user_id] = self.historical_estimates[user_id][-50:]
    
    async def _smart_time_distribution(
        self,
        work_item: Dict[str, Any],
        matches: List[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Smart time distribution across JIRA tickets."""
        total_time = work_item.get("estimated_time", 1.0)
        
        if not matches:
            return {"unallocated": total_time}
        
        # Calculate distribution based on confidence scores
        total_confidence = sum(match.get("confidence", 0) for match in matches)
        
        if total_confidence == 0:
            # Equal distribution if no confidence scores
            time_per_ticket = total_time / len(matches)
            return {match.get("ticket_key", "unknown"): time_per_ticket for match in matches}
        
        # Weighted distribution based on confidence
        distribution = {}
        for match in matches:
            confidence = match.get("confidence", 0)
            allocated_time = (confidence / total_confidence) * total_time
            ticket_key = match.get("ticket_key", "unknown")
            distribution[ticket_key] = round(allocated_time, 2)
        
        return distribution
    
    def _calculate_automation_confidence(
        self, 
        matches: List[Dict[str, Any]], 
        work_item: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for automation."""
        if not matches:
            return 0.0
        
        # Base confidence on best match
        best_confidence = max(match.get("confidence", 0) for match in matches)
        
        # Adjust based on work item clarity
        description = work_item.get("description", "")
        if len(description) > 20 and any(keyword in description.lower() for keyword in ["completed", "fixed", "implemented"]):
            best_confidence += 0.1
        
        return min(best_confidence, 1.0)
    
    def _calculate_automation_rate(self, matched_items: List[Dict[str, Any]]) -> float:
        """Calculate overall automation rate."""
        if not matched_items:
            return 0.0
        
        high_confidence_items = sum(
            1 for item in matched_items 
            if item.get("automation_confidence", 0) > 0.7
        )
        
        return high_confidence_items / len(matched_items)
    
    async def _generate_work_log_recommendations(
        self, 
        matched_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate work log recommendations."""
        recommendations = []
        
        for item in matched_items:
            work_item = item["work_item"]
            matches = item["ticket_matches"]
            time_dist = item["time_distribution"]
            confidence = item["automation_confidence"]
            
            if confidence > 0.7:
                action = "auto_log"
            elif confidence > 0.4:
                action = "suggest_log"
            else:
                action = "manual_review"
            
            recommendations.append({
                "work_description": work_item.get("description", ""),
                "recommended_action": action,
                "ticket_allocations": time_dist,
                "confidence": confidence,
                "reasoning": f"Confidence {confidence:.2f} based on ticket matching"
            })
        
        return recommendations
    
    def _build_productivity_analytics_prompt(
        self, 
        work_items: List[Dict[str, Any]], 
        timeframe: str, 
        user_id: Optional[str] = None
    ) -> str:
        """Build prompt for productivity analytics."""
        
        # Aggregate work item data
        total_items = len(work_items)
        total_time = sum(item.get("estimated_time", 0) for item in work_items)
        categories = defaultdict(int)
        priorities = defaultdict(int)
        
        for item in work_items:
            categories[item.get("activity_type", "other")] += 1
            priorities[item.get("priority", "medium")] += 1
        
        work_summary = f"""
Work Items Summary ({timeframe}):
- Total items: {total_items}
- Total time: {total_time} hours
- Categories: {dict(categories)}
- Priorities: {dict(priorities)}
"""
        
        return f"""
Analyze productivity patterns and generate insights for this {timeframe} work data:

{work_summary}

Detailed work items:
{json.dumps(work_items[:10], indent=2)}  # Limit for prompt size

Provide comprehensive productivity analysis:

1. Productivity Patterns: What patterns emerge?
2. Time Allocation: How is time distributed?
3. Focus Areas: What are the main focus areas?
4. Efficiency Indicators: Signs of high/low efficiency
5. Recommendations: Specific improvement suggestions
6. Trend Analysis: Notable trends or changes
7. Work-Life Balance: Indicators of balance/imbalance

{{
  "productivity_score": 8.2,
  "efficiency_rating": "high",
  "focus_areas": ["development", "testing"],
  "time_distribution": {{
    "deep_work": 6.5,
    "meetings": 1.5,
    "administrative": 0.5
  }},
  "patterns": {{
    "peak_productivity_hours": "10am-12pm",
    "common_task_types": ["bug fixes", "feature development"],
    "multitasking_frequency": "low"
  }},
  "recommendations": [
    "Consider blocking more time for deep work",
    "Reduce context switching between projects"
  ],
  "insights": [
    "High completion rate indicates good planning",
    "Balanced mix of development and testing work"
  ]
}}
"""
    
    def _calculate_productivity_metrics(self, work_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate productivity metrics from work items."""
        if not work_items:
            return {"metrics_available": False}
        
        total_time = sum(item.get("estimated_time", 0) for item in work_items)
        completed_items = sum(1 for item in work_items if "completed" in item.get("description", "").lower())
        high_priority_items = sum(1 for item in work_items if item.get("priority") == "high")
        
        return {
            "metrics_available": True,
            "total_logged_hours": total_time,
            "completion_rate": completed_items / len(work_items) if work_items else 0,
            "high_priority_ratio": high_priority_items / len(work_items) if work_items else 0,
            "average_task_duration": total_time / len(work_items) if work_items else 0,
            "productivity_index": (completed_items * 2 + len(work_items)) / (total_time + 1)  # Custom metric
        }
    
    def _default_categorization(self) -> Dict[str, Any]:
        """Default categorization response."""
        return {
            "category": "development",
            "secondary_categories": [],
            "technical_domain": "general",
            "complexity": "moderate",
            "priority": "medium",
            "effort_level": "medium",
            "required_skills": [],
            "risk_factors": [],
            "dependencies": [],
            "confidence": 0.5
        }
    
    def _default_time_estimate(self) -> Dict[str, Any]:
        """Default time estimation response."""
        return {
            "estimated_hours": 2.0,
            "confidence_interval": {"min": 1.0, "max": 4.0, "confidence": 0.5},
            "breakdown": {"implementation": 2.0},
            "risk_factors": [],
            "assumptions": [],
            "historical_accuracy": "unknown"
        }
    
    def _default_productivity_analytics(self) -> Dict[str, Any]:
        """Default productivity analytics response."""
        return {
            "productivity_score": 5.0,
            "efficiency_rating": "medium",
            "focus_areas": [],
            "time_distribution": {},
            "patterns": {},
            "recommendations": [],
            "insights": []
        }
    
    def _parse_categorization_response(self, response: str) -> Dict[str, Any]:
        """Parse categorization response."""
        return self._parse_json_response(response, self._default_categorization())
    
    def _parse_enhanced_time_estimate_response(self, response: str) -> Dict[str, Any]:
        """Parse enhanced time estimation response."""
        return self._parse_json_response(response, self._default_time_estimate())
    
    def _parse_productivity_analytics_response(self, response: str) -> Dict[str, Any]:
        """Parse productivity analytics response."""
        return self._parse_json_response(response, self._default_productivity_analytics())
    
    def _parse_json_response(self, response: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JSON response with fallback to default."""
        try:
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:-3]
            elif response.startswith("```"):
                response = response[3:-3]
            return json.loads(response)
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return default

    # ==================== REPORT GENERATION METHODS ====================
    
    async def generate_report(
        self,
        work_items: List[Dict[str, Any]],
        report_type: str = "daily",
        template: str = "standard_daily"
    ) -> Dict[str, Any]:
        """Generate a formatted report using AI based on work items and template."""
        logger.info(f"Generating {report_type} report using template {template}")
        
        try:
            prompt = self._build_report_generation_prompt(work_items, report_type, template)
            response = await self._call_openroute_api(prompt, max_tokens=2000, temperature=0.4)
            
            if response:
                parsed_response = self._parse_report_response(response)
                
                # Calculate quality score
                quality_score = self._calculate_report_quality(parsed_response, work_items)
                parsed_response["quality_score"] = quality_score
                
                return parsed_response
            else:
                return self._default_report_response(work_items, report_type)
                
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return self._default_report_response(work_items, report_type)
    
    async def generate_weekly_report(
        self,
        work_items: List[Dict[str, Any]],
        daily_distribution: Dict[str, Any],
        week_start: str,
        template: str = "weekly_summary"
    ) -> Dict[str, Any]:
        """Generate a comprehensive weekly report with daily distribution analysis."""
        logger.info(f"Generating weekly report starting {week_start} using template {template}")
        
        try:
            prompt = self._build_weekly_report_prompt(
                work_items, daily_distribution, week_start, template
            )
            response = await self._call_openroute_api(prompt, max_tokens=2500, temperature=0.4)
            
            if response:
                parsed_response = self._parse_weekly_report_response(response)
                
                # Calculate quality score
                quality_score = self._calculate_weekly_report_quality(
                    parsed_response, work_items, daily_distribution
                )
                parsed_response["quality_score"] = quality_score
                
                return parsed_response
            else:
                return self._default_weekly_report_response(work_items, daily_distribution, week_start)
                
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return self._default_weekly_report_response(work_items, daily_distribution, week_start)
    
    def _build_report_generation_prompt(
        self,
        work_items: List[Dict[str, Any]],
        report_type: str,
        template: str
    ) -> str:
        """Build prompt for daily report generation."""
        
        # Summarize work items
        work_summary = ""
        total_time = 0
        categories = {}
        
        for item in work_items:
            work_summary += f"- {item.get('description', 'N/A')} ({item.get('time_spent_minutes', 0)} min)\n"
            total_time += item.get('time_spent_minutes', 0)
            
            category = item.get('ai_analysis', {}).get('category', 'Other')
            categories[category] = categories.get(category, 0) + 1
        
        total_hours = total_time / 60.0
        
        template_instructions = self._get_template_instructions(template)
        
        return f"""
Generate a professional {report_type} work report based on the following information:

WORK COMPLETED:
{work_summary if work_summary else "No work items recorded"}

SUMMARY STATISTICS:
- Total time logged: {total_hours:.1f} hours ({total_time} minutes)
- Number of tasks: {len(work_items)}
- Task categories: {', '.join(f'{k}({v})' for k, v in categories.items())}

TEMPLATE: {template}
{template_instructions}

Please generate a comprehensive, professional report that:
1. Summarizes the day's accomplishments clearly
2. Organizes information logically
3. Highlights key achievements and productivity
4. Uses professional language suitable for status updates
5. Includes relevant time breakdowns and metrics

Respond in JSON format:
{{
  "content": "Full formatted report content as markdown",
  "summary": "Brief executive summary",
  "key_accomplishments": ["Accomplishment 1", "Accomplishment 2"],
  "time_breakdown": {{
    "development": 4.5,
    "meetings": 2.0,
    "testing": 1.0,
    "other": 0.5
  }},
  "productivity_insights": ["Insight 1", "Insight 2"],
  "next_steps": ["Next step 1", "Next step 2"]
}}
"""
    
    def _build_weekly_report_prompt(
        self,
        work_items: List[Dict[str, Any]],
        daily_distribution: Dict[str, Any],
        week_start: str,
        template: str
    ) -> str:
        """Build prompt for weekly report generation."""
        
        # Analyze weekly patterns
        total_time = sum(item.get('time_spent_minutes', 0) for item in work_items)
        total_hours = total_time / 60.0
        
        # Daily breakdown
        daily_summary = ""
        for day_key in sorted(daily_distribution.keys()):
            day_data = daily_distribution[day_key]
            daily_summary += f"- {day_data['date']}: {day_data['work_items']} tasks, {day_data['total_hours']:.1f}h\n"
        
        # Category analysis
        categories = {}
        for item in work_items:
            category = item.get('ai_analysis', {}).get('category', 'Other')
            categories[category] = categories.get(category, 0) + item.get('time_spent_minutes', 0)
        
        template_instructions = self._get_template_instructions(template)
        
        return f"""
Generate a comprehensive weekly work report for the week starting {week_start}:

WEEKLY OVERVIEW:
- Total time logged: {total_hours:.1f} hours
- Total tasks completed: {len(work_items)}
- Average daily productivity: {total_hours/7:.1f} hours/day

DAILY BREAKDOWN:
{daily_summary}

TIME BY CATEGORY:
{chr(10).join(f'- {cat}: {time/60:.1f}h' for cat, time in categories.items())}

TEMPLATE: {template}
{template_instructions}

Generate a professional weekly report that includes:
1. Executive summary of the week's work
2. Daily productivity analysis and patterns
3. Key achievements and deliverables
4. Time allocation insights
5. Productivity trends and observations
6. Planning for next week

Respond in JSON format:
{{
  "content": "Full formatted weekly report content as markdown",
  "executive_summary": "High-level overview of the week",
  "daily_analysis": {{
    "most_productive_day": "2024-01-15",
    "least_productive_day": "2024-01-17",
    "average_daily_hours": 7.2,
    "consistency_score": 0.85
  }},
  "key_achievements": ["Achievement 1", "Achievement 2"],
  "productivity_patterns": ["Pattern 1", "Pattern 2"],
  "time_allocation": {{
    "development": 25.5,
    "meetings": 8.0,
    "testing": 6.5,
    "planning": 2.0
  }},
  "insights": ["Insight 1", "Insight 2"],
  "next_week_planning": ["Plan 1", "Plan 2"]
}}
"""
    
    def _get_template_instructions(self, template: str) -> str:
        """Get specific instructions for different report templates."""
        templates = {
            "standard_daily": """
Focus on: Brief summary, key tasks completed, time spent, next steps.
Format: Professional but concise. Suitable for daily standups or status emails.
""",
            "detailed_daily": """
Focus on: Comprehensive details, technical challenges, solutions implemented, lessons learned.
Format: Technical depth with explanations. Suitable for technical documentation or detailed status reports.
""",
            "weekly_summary": """
Focus on: Week overview, productivity patterns, major accomplishments, planning insights.
Format: Strategic level summary with metrics and trends. Suitable for management reporting.
""",
            "sprint_summary": """
Focus on: Sprint velocity, story completion, blockers, team productivity metrics.
Format: Agile-focused with sprint terminology. Suitable for scrum retrospectives and planning.
"""
        }
        return templates.get(template, "Generate a professional, well-structured report.")
    
    def _parse_report_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for daily report generation."""
        try:
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:-3]
            elif response.startswith("```"):
                response = response[3:-3]
            
            parsed = json.loads(response)
            
            # Ensure required fields exist
            return {
                "content": parsed.get("content", "Report content not available"),
                "summary": parsed.get("summary", ""),
                "key_accomplishments": parsed.get("key_accomplishments", []),
                "time_breakdown": parsed.get("time_breakdown", {}),
                "productivity_insights": parsed.get("productivity_insights", []),
                "next_steps": parsed.get("next_steps", [])
            }
            
        except Exception as e:
            logger.error(f"Error parsing report response: {e}")
            return {
                "content": "Error generating report content",
                "summary": "Report generation failed",
                "key_accomplishments": [],
                "time_breakdown": {},
                "productivity_insights": [],
                "next_steps": []
            }
    
    def _parse_weekly_report_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for weekly report generation."""
        try:
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:-3]
            elif response.startswith("```"):
                response = response[3:-3]
            
            parsed = json.loads(response)
            
            # Ensure required fields exist
            return {
                "content": parsed.get("content", "Weekly report content not available"),
                "executive_summary": parsed.get("executive_summary", ""),
                "daily_analysis": parsed.get("daily_analysis", {}),
                "key_achievements": parsed.get("key_achievements", []),
                "productivity_patterns": parsed.get("productivity_patterns", []),
                "time_allocation": parsed.get("time_allocation", {}),
                "insights": parsed.get("insights", []),
                "next_week_planning": parsed.get("next_week_planning", [])
            }
            
        except Exception as e:
            logger.error(f"Error parsing weekly report response: {e}")
            return {
                "content": "Error generating weekly report content",
                "executive_summary": "Weekly report generation failed",
                "daily_analysis": {},
                "key_achievements": [],
                "productivity_patterns": [],
                "time_allocation": {},
                "insights": [],
                "next_week_planning": []
            }
    
    def _calculate_report_quality(
        self, 
        report: Dict[str, Any], 
        work_items: List[Dict[str, Any]]
    ) -> float:
        """Calculate quality score for generated report."""
        quality_factors = []
        
        # Content length and detail
        content_length = len(report.get("content", ""))
        if content_length > 500:
            quality_factors.append(0.3)
        elif content_length > 200:
            quality_factors.append(0.2)
        else:
            quality_factors.append(0.1)
        
        # Key accomplishments coverage
        accomplishments = report.get("key_accomplishments", [])
        if len(accomplishments) >= len(work_items) // 3:  # At least 1/3 coverage
            quality_factors.append(0.2)
        elif len(accomplishments) > 0:
            quality_factors.append(0.1)
        else:
            quality_factors.append(0.0)
        
        # Time breakdown accuracy
        time_breakdown = report.get("time_breakdown", {})
        if len(time_breakdown) >= 3:  # Multiple categories
            quality_factors.append(0.2)
        elif len(time_breakdown) > 0:
            quality_factors.append(0.1)
        else:
            quality_factors.append(0.0)
        
        # Insights quality
        insights = report.get("productivity_insights", [])
        if len(insights) >= 2:
            quality_factors.append(0.15)
        elif len(insights) > 0:
            quality_factors.append(0.1)
        else:
            quality_factors.append(0.0)
        
        # Next steps planning
        next_steps = report.get("next_steps", [])
        if len(next_steps) >= 2:
            quality_factors.append(0.15)
        elif len(next_steps) > 0:
            quality_factors.append(0.1)
        else:
            quality_factors.append(0.0)
        
        return min(sum(quality_factors), 1.0)
    
    def _calculate_weekly_report_quality(
        self,
        report: Dict[str, Any],
        work_items: List[Dict[str, Any]],
        daily_distribution: Dict[str, Any]
    ) -> float:
        """Calculate quality score for generated weekly report."""
        quality_factors = []
        
        # Content comprehensiveness
        content_length = len(report.get("content", ""))
        if content_length > 1000:
            quality_factors.append(0.25)
        elif content_length > 500:
            quality_factors.append(0.2)
        else:
            quality_factors.append(0.1)
        
        # Daily analysis depth
        daily_analysis = report.get("daily_analysis", {})
        if len(daily_analysis) >= 4:  # Multiple metrics
            quality_factors.append(0.2)
        elif len(daily_analysis) > 0:
            quality_factors.append(0.1)
        else:
            quality_factors.append(0.0)
        
        # Time allocation coverage
        time_allocation = report.get("time_allocation", {})
        if len(time_allocation) >= 4:  # Multiple categories
            quality_factors.append(0.2)
        elif len(time_allocation) > 0:
            quality_factors.append(0.1)
        else:
            quality_factors.append(0.0)
        
        # Productivity patterns analysis
        patterns = report.get("productivity_patterns", [])
        if len(patterns) >= 3:
            quality_factors.append(0.15)
        elif len(patterns) > 0:
            quality_factors.append(0.1)
        else:
            quality_factors.append(0.0)
        
        # Strategic insights
        insights = report.get("insights", [])
        next_week = report.get("next_week_planning", [])
        if len(insights) >= 2 and len(next_week) >= 2:
            quality_factors.append(0.2)
        elif len(insights) > 0 or len(next_week) > 0:
            quality_factors.append(0.1)
        else:
            quality_factors.append(0.0)
        
        return min(sum(quality_factors), 1.0)
    
    def _default_report_response(
        self, 
        work_items: List[Dict[str, Any]], 
        report_type: str
    ) -> Dict[str, Any]:
        """Generate default report response when AI fails."""
        total_time = sum(item.get('time_spent_minutes', 0) for item in work_items)
        total_hours = total_time / 60.0
        
        content = f"""# {report_type.title()} Work Report

## Summary
Completed {len(work_items)} tasks with a total time investment of {total_hours:.1f} hours.

## Tasks Completed
"""
        
        for item in work_items:
            content += f"- {item.get('description', 'Task')} ({item.get('time_spent_minutes', 0)} minutes)\n"
        
        content += f"\n## Total Time: {total_hours:.1f} hours"
        
        return {
            "content": content,
            "summary": f"Completed {len(work_items)} tasks in {total_hours:.1f} hours",
            "key_accomplishments": [item.get('description', 'Task') for item in work_items[:5]],
            "time_breakdown": {"work": total_hours},
            "productivity_insights": [f"Completed {len(work_items)} tasks today"],
            "next_steps": ["Continue with scheduled work"],
            "quality_score": 0.5
        }
    
    def _default_weekly_report_response(
        self,
        work_items: List[Dict[str, Any]],
        daily_distribution: Dict[str, Any],
        week_start: str
    ) -> Dict[str, Any]:
        """Generate default weekly report response when AI fails."""
        total_time = sum(item.get('time_spent_minutes', 0) for item in work_items)
        total_hours = total_time / 60.0
        avg_daily = total_hours / 7
        
        content = f"""# Weekly Work Report - Week of {week_start}

## Executive Summary
Completed {len(work_items)} tasks with {total_hours:.1f} total hours logged.
Average daily productivity: {avg_daily:.1f} hours.

## Daily Breakdown
"""
        
        for day_key in sorted(daily_distribution.keys()):
            day_data = daily_distribution[day_key]
            content += f"- {day_data['date']}: {day_data['work_items']} tasks, {day_data['total_hours']:.1f}h\n"
        
        content += f"\n## Total Weekly Hours: {total_hours:.1f}"
        
        return {
            "content": content,
            "executive_summary": f"Productive week with {len(work_items)} tasks completed",
            "daily_analysis": {
                "average_daily_hours": avg_daily,
                "total_tasks": len(work_items)
            },
            "key_achievements": [item.get('description', 'Task') for item in work_items[:5]],
            "productivity_patterns": ["Consistent daily work"],
            "time_allocation": {"work": total_hours},
            "insights": [f"Maintained {avg_daily:.1f}h average daily productivity"],
            "next_week_planning": ["Continue current productivity levels"],
            "quality_score": 0.5
        } 