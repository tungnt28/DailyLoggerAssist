"""
AI Processing Schemas - Daily Logger Assist

Pydantic schemas for enhanced AI processing endpoints (Phase 3).
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

# ==================== BASE SCHEMAS ====================

class AIResponseBase(BaseModel):
    """Base response schema for AI operations."""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

class TaskResponse(AIResponseBase):
    """Response for asynchronous task operations."""
    task_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# ==================== CONTENT ANALYSIS ====================

class ContentAnalysisContext(BaseModel):
    """Context information for content analysis."""
    source: Optional[str] = Field(None, description="Source of the content (teams, email, etc.)")
    sender: Optional[str] = Field(None, description="Content sender")
    timestamp: Optional[str] = Field(None, description="Content timestamp")
    project: Optional[str] = Field(None, description="Related project")
    urgency_hints: Optional[List[str]] = Field(None, description="Urgency indicators")

class ContentAnalysisRequest(BaseModel):
    """Request for enhanced content analysis."""
    content: str = Field(..., description="Content to analyze", min_length=1, max_length=10000)
    context: Optional[ContentAnalysisContext] = Field(None, description="Additional context")

class WorkItemExtracted(BaseModel):
    """Extracted work item from content analysis."""
    activity_type: str = Field(..., description="Type of activity")
    description: str = Field(..., description="Work item description")
    estimated_time: float = Field(..., description="Estimated time in hours")
    priority: str = Field(..., description="Priority level")
    project_reference: Optional[str] = Field(None, description="Project or ticket reference")

class SentimentAnalysis(BaseModel):
    """Sentiment analysis results."""
    sentiment: str = Field(..., description="Overall sentiment (positive, neutral, negative)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    emotional_tone: str = Field(..., description="Emotional tone")
    urgency_indicators: List[str] = Field(default_factory=list, description="Detected urgency indicators")

class UrgencyDetection(BaseModel):
    """Urgency detection results."""
    urgency_level: str = Field(..., description="Urgency level (low, medium, high)")
    urgency_score: int = Field(..., description="Numerical urgency score")
    detected_keywords: List[str] = Field(default_factory=list, description="Detected urgency keywords")

class CollaborationPatterns(BaseModel):
    """Collaboration pattern analysis."""
    collaboration_type: str = Field(..., description="Type of collaboration")
    patterns: Dict[str, int] = Field(default_factory=dict, description="Detected patterns")

class ProductivityIndicators(BaseModel):
    """Productivity indicators from content."""
    productivity_score: int = Field(..., description="Overall productivity score")
    completion_indicators: int = Field(..., description="Number of completion indicators")
    progress_indicators: int = Field(..., description="Number of progress indicators")
    planning_indicators: int = Field(..., description="Number of planning indicators")

class ContentAnalysisResponse(AIResponseBase):
    """Response for content analysis."""
    work_items: List[WorkItemExtracted] = Field(default_factory=list)
    sentiment_analysis: Optional[SentimentAnalysis] = None
    urgency_detection: Optional[UrgencyDetection] = None
    skill_classification: List[str] = Field(default_factory=list)
    collaboration_patterns: Optional[CollaborationPatterns] = None
    productivity_indicators: Optional[ProductivityIndicators] = None

# ==================== TASK CATEGORIZATION ====================

class TaskCategorizationContext(BaseModel):
    """Context for task categorization."""
    project_type: Optional[str] = Field(None, description="Type of project")
    team_size: Optional[int] = Field(None, description="Team size")
    deadline: Optional[str] = Field(None, description="Task deadline")
    existing_tools: Optional[List[str]] = Field(None, description="Available tools/frameworks")

class TaskCategorizationRequest(BaseModel):
    """Request for task categorization."""
    task_description: str = Field(..., description="Task to categorize", min_length=1, max_length=5000)
    context: Optional[TaskCategorizationContext] = Field(None, description="Additional context")

class TaskCategorization(BaseModel):
    """Task categorization results."""
    category: str = Field(..., description="Primary category")
    secondary_categories: List[str] = Field(default_factory=list, description="Secondary categories")
    technical_domain: str = Field(..., description="Technical domain")
    complexity: str = Field(..., description="Complexity level")
    priority: str = Field(..., description="Priority level")
    effort_level: str = Field(..., description="Effort level")
    required_skills: List[str] = Field(default_factory=list, description="Required skills")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")

class TaskCategorizationResponse(AIResponseBase):
    """Response for task categorization."""
    categorization: Optional[TaskCategorization] = None

class BatchCategorizationRequest(BaseModel):
    """Request for batch categorization."""
    work_item_ids: List[str] = Field(..., description="List of work item IDs to categorize")

# ==================== TIME ESTIMATION ====================

class TimeEstimationContext(BaseModel):
    """Context for time estimation."""
    similar_tasks_completed: Optional[int] = Field(None, description="Number of similar tasks completed")
    team_velocity: Optional[float] = Field(None, description="Team velocity")
    available_resources: Optional[List[str]] = Field(None, description="Available resources")
    constraints: Optional[List[str]] = Field(None, description="Known constraints")

class TimeEstimationRequest(BaseModel):
    """Request for time estimation."""
    task_description: str = Field(..., description="Task to estimate", min_length=1, max_length=5000)
    context: Optional[TimeEstimationContext] = Field(None, description="Additional context")
    use_historical_data: bool = Field(True, description="Whether to use historical data")

class ConfidenceInterval(BaseModel):
    """Confidence interval for time estimation."""
    min: float = Field(..., description="Minimum estimated hours")
    max: float = Field(..., description="Maximum estimated hours")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level")

class TimeBreakdown(BaseModel):
    """Breakdown of time estimation."""
    analysis: Optional[float] = Field(None, description="Analysis time")
    implementation: Optional[float] = Field(None, description="Implementation time")
    testing: Optional[float] = Field(None, description="Testing time")
    documentation: Optional[float] = Field(None, description="Documentation time")
    review: Optional[float] = Field(None, description="Review time")

class TimeEstimation(BaseModel):
    """Time estimation results."""
    estimated_hours: float = Field(..., description="Estimated hours")
    confidence_interval: Optional[ConfidenceInterval] = None
    breakdown: Optional[TimeBreakdown] = None
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made")
    historical_accuracy: str = Field(..., description="Historical accuracy level")

class TimeEstimationResponse(AIResponseBase):
    """Response for time estimation."""
    estimation: Optional[TimeEstimation] = None

class BatchTimeEstimationRequest(BaseModel):
    """Request for batch time estimation."""
    work_item_ids: List[str] = Field(..., description="List of work item IDs to estimate")

# ==================== JIRA WORK LOGGING ====================

class JiraWorkLoggingRequest(BaseModel):
    """Request for JIRA work logging."""
    work_item_ids: List[str] = Field(..., description="List of work item IDs to log")
    auto_log_threshold: float = Field(0.7, description="Confidence threshold for auto-logging", ge=0.0, le=1.0)

class JiraWorkLoggingResponse(AIResponseBase):
    """Response for JIRA work logging."""
    task_id: Optional[str] = None
    auto_logged_count: Optional[int] = None
    total_recommendations: Optional[int] = None
    automation_rate: Optional[float] = None

# ==================== PRODUCTIVITY ANALYTICS ====================

class GenerateAnalyticsRequest(BaseModel):
    """Request for analytics generation."""
    timeframes: List[str] = Field(..., description="Timeframes to generate (daily, weekly, monthly)")
    date: Optional[str] = Field(None, description="Target date (YYYY-MM-DD)")

class ProductivityMetrics(BaseModel):
    """Calculated productivity metrics."""
    total_logged_hours: float = Field(..., description="Total logged hours")
    completion_rate: float = Field(..., description="Task completion rate")
    high_priority_ratio: float = Field(..., description="High priority task ratio")
    average_task_duration: float = Field(..., description="Average task duration")
    productivity_index: float = Field(..., description="Custom productivity index")

class ProductivityAnalytics(BaseModel):
    """Productivity analytics results."""
    productivity_score: float = Field(..., description="Overall productivity score")
    efficiency_rating: str = Field(..., description="Efficiency rating")
    focus_areas: List[str] = Field(default_factory=list, description="Main focus areas")
    time_distribution: Dict[str, float] = Field(default_factory=dict, description="Time distribution")
    patterns: Dict[str, Any] = Field(default_factory=dict, description="Detected patterns")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    insights: List[str] = Field(default_factory=list, description="Key insights")
    metrics: Optional[ProductivityMetrics] = None

class ProductivityAnalyticsResponse(AIResponseBase):
    """Response for productivity analytics."""
    analytics: Optional[ProductivityAnalytics] = None
    generated_at: Optional[datetime] = None
    from_cache: bool = Field(False, description="Whether data is from cache")
    task_id: Optional[str] = None

# ==================== PROCESSING STATUS ====================

class ProcessingStatistics(BaseModel):
    """AI processing statistics."""
    recent_work_items: int = Field(..., description="Recent work items count")
    analyzed_items: int = Field(..., description="Analyzed items count")
    analysis_coverage: float = Field(..., description="Analysis coverage ratio")
    recent_reports: int = Field(..., description="Recent reports count")
    ai_service_status: str = Field(..., description="AI service status")

class ProcessingStatusResponse(AIResponseBase):
    """Response for processing status."""
    statistics: Optional[ProcessingStatistics] = None

# ==================== USER PATTERNS ====================

class UserPatterns(BaseModel):
    """User behavior patterns."""
    common_skills: Dict[str, int] = Field(default_factory=dict, description="Common skills and frequency")
    productivity_trends: List[Dict[str, Any]] = Field(default_factory=list, description="Productivity trends")
    preferred_categories: Dict[str, int] = Field(default_factory=dict, description="Preferred work categories")
    insights: List[str] = Field(default_factory=list, description="Generated insights")

class UserPatternsResponse(AIResponseBase):
    """Response for user patterns."""
    patterns: Optional[UserPatterns] = None 