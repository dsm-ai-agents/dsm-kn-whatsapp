"""
Personalization Engine for Context-Aware Conversations
Adapts response strategies based on user journey, engagement, and behavioral patterns
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from src.services.enhanced_context_service import (
    EnhancedCustomerContext, 
    PersonalizationLevel,
    get_enhanced_context_service
)

logger = logging.getLogger(__name__)

class ResponseStrategy(Enum):
    """Response adaptation strategies"""
    EDUCATIONAL = "educational"          # Teach and inform
    CONSULTATIVE = "consultative"       # Ask questions, understand needs
    SOLUTION_FOCUSED = "solution_focused" # Present solutions
    CLOSING = "closing"                  # Push for decision/action

class CommunicationStyle(Enum):
    """Communication style preferences"""
    TECHNICAL = "technical"             # Technical details, data-driven
    BUSINESS = "business"              # Business benefits, ROI-focused
    CONVERSATIONAL = "conversational"  # Friendly, casual tone
    FORMAL = "formal"                  # Professional, structured

@dataclass
class PersonalizationStrategy:
    """Complete personalization strategy for a user"""
    response_strategy: ResponseStrategy
    communication_style: CommunicationStyle
    personalization_level: PersonalizationLevel
    key_focus_areas: List[str]
    pain_points_to_address: List[str]
    goals_to_highlight: List[str]
    examples_to_include: List[str]
    call_to_action_type: str
    urgency_level: str
    relationship_building_approach: str

class PersonalizationEngine:
    """Engine for determining personalized response strategies"""
    
    def __init__(self):
        self.context_service = get_enhanced_context_service()
    
    def get_personalization_strategy(self, context: EnhancedCustomerContext) -> PersonalizationStrategy:
        """Generate complete personalization strategy based on customer context"""
        try:
            # Determine response strategy
            response_strategy = self._determine_response_strategy(context)
            
            # Determine communication style
            communication_style = self._determine_communication_style(context)
            
            # Get personalization level
            personalization_level = self.context_service.get_personalization_level(context)
            
            # Determine focus areas
            key_focus_areas = self._determine_key_focus_areas(context)
            
            # Get pain points and goals to address
            pain_points_to_address = self._prioritize_pain_points(context)
            goals_to_highlight = self._prioritize_goals(context)
            
            # Determine examples to include
            examples_to_include = self._select_relevant_examples(context)
            
            # Determine call-to-action type
            call_to_action_type = self._determine_cta_type(context)
            
            # Determine urgency level
            urgency_level = self._determine_urgency_level(context)
            
            # Determine relationship building approach
            relationship_building = self._determine_relationship_approach(context)
            
            strategy = PersonalizationStrategy(
                response_strategy=response_strategy,
                communication_style=communication_style,
                personalization_level=personalization_level,
                key_focus_areas=key_focus_areas,
                pain_points_to_address=pain_points_to_address,
                goals_to_highlight=goals_to_highlight,
                examples_to_include=examples_to_include,
                call_to_action_type=call_to_action_type,
                urgency_level=urgency_level,
                relationship_building_approach=relationship_building
            )
            
            logger.info(f"Generated personalization strategy: {response_strategy.value} + {communication_style.value} for {context.phone_number}")
            return strategy
            
        except Exception as e:
            logger.error(f"Error generating personalization strategy: {e}")
            return self._get_default_strategy()
    
    def _determine_response_strategy(self, context: EnhancedCustomerContext) -> ResponseStrategy:
        """Determine the best response strategy based on journey stage and engagement"""
        
        # Decision stage - focus on closing
        if context.journey_stage == "decision":
            return ResponseStrategy.CLOSING
        
        # Evaluation stage - present solutions
        if context.journey_stage == "evaluation":
            return ResponseStrategy.SOLUTION_FOCUSED
        
        # Interest stage - consult and understand
        if context.journey_stage == "interest":
            return ResponseStrategy.CONSULTATIVE
        
        # Discovery stage - educate and inform
        if context.journey_stage == "discovery":
            return ResponseStrategy.EDUCATIONAL
        
        # Default based on engagement level
        if context.engagement_level == "high":
            return ResponseStrategy.SOLUTION_FOCUSED
        elif context.engagement_level == "low":
            return ResponseStrategy.EDUCATIONAL
        else:
            return ResponseStrategy.CONSULTATIVE
    
    def _determine_communication_style(self, context: EnhancedCustomerContext) -> CommunicationStyle:
        """Determine communication style based on technical level and decision making style"""
        
        # Technical users prefer technical communication
        if context.technical_level == "technical_user":
            return CommunicationStyle.TECHNICAL
        
        # Analytical decision makers prefer business-focused communication
        if context.decision_making_style == "analytical":
            return CommunicationStyle.BUSINESS
        
        # High engagement users can handle more conversational tone
        if context.engagement_level == "high":
            return CommunicationStyle.CONVERSATIONAL
        
        # Decision makers often prefer formal communication
        if context.decision_maker:
            return CommunicationStyle.FORMAL
        
        # Default to business style
        return CommunicationStyle.BUSINESS
    
    def _determine_key_focus_areas(self, context: EnhancedCustomerContext) -> List[str]:
        """Determine key areas to focus on based on context"""
        focus_areas = []
        
        # Based on pain points
        if "manual" in context.pain_points_mentioned or "time-consuming" in context.pain_points_mentioned:
            focus_areas.append("automation_benefits")
        
        if "inefficient" in context.pain_points_mentioned or "slow" in context.pain_points_mentioned:
            focus_areas.append("efficiency_gains")
        
        # Based on goals
        if "automate" in context.goals_expressed or "streamline" in context.goals_expressed:
            focus_areas.append("workflow_automation")
        
        if "improve" in context.goals_expressed or "increase" in context.goals_expressed:
            focus_areas.append("performance_improvement")
        
        # Based on topics discussed
        if "pricing" in context.topics_discussed:
            focus_areas.append("value_proposition")
        
        if "implementation" in context.topics_discussed:
            focus_areas.append("implementation_ease")
        
        # Based on industry
        if context.industry_focus:
            focus_areas.append(f"{context.industry_focus}_specific_solutions")
        
        # Default focus areas if none identified
        if not focus_areas:
            focus_areas = ["core_benefits", "ease_of_use", "roi"]
        
        return focus_areas[:3]  # Limit to top 3 focus areas
    
    def _prioritize_pain_points(self, context: EnhancedCustomerContext) -> List[str]:
        """Prioritize pain points to address in responses"""
        pain_points = context.pain_points_mentioned.copy()
        
        # Priority mapping
        priority_map = {
            "manual": 10,
            "time-consuming": 9,
            "inefficient": 8,
            "slow": 7,
            "frustrated": 6,
            "problem": 5,
            "issue": 4,
            "challenge": 3,
            "difficulty": 2,
            "struggle": 1
        }
        
        # Sort by priority
        pain_points.sort(key=lambda x: priority_map.get(x, 0), reverse=True)
        
        return pain_points[:2]  # Focus on top 2 pain points
    
    def _prioritize_goals(self, context: EnhancedCustomerContext) -> List[str]:
        """Prioritize goals to highlight in responses"""
        goals = context.goals_expressed.copy()
        
        # Priority mapping
        priority_map = {
            "automate": 10,
            "streamline": 9,
            "improve": 8,
            "increase": 7,
            "reduce": 6,
            "want to": 5,
            "need to": 4,
            "goal": 3,
            "objective": 2,
            "target": 1
        }
        
        # Sort by priority
        goals.sort(key=lambda x: priority_map.get(x, 0), reverse=True)
        
        return goals[:2]  # Focus on top 2 goals
    
    def _select_relevant_examples(self, context: EnhancedCustomerContext) -> List[str]:
        """Select relevant examples based on context"""
        examples = []
        
        # Industry-specific examples
        if context.industry_focus:
            examples.append(f"{context.industry_focus}_case_study")
        
        # Company size examples
        if context.company_size:
            examples.append(f"{context.company_size}_company_example")
        
        # Pain point examples
        for pain_point in context.pain_points_mentioned[:2]:
            examples.append(f"{pain_point}_solution_example")
        
        # Technical level examples
        if context.technical_level == "technical_user":
            examples.append("technical_implementation_example")
        else:
            examples.append("business_outcome_example")
        
        # Default examples
        if not examples:
            examples = ["general_success_story", "roi_example"]
        
        return examples[:2]  # Limit to 2 examples
    
    def _determine_cta_type(self, context: EnhancedCustomerContext) -> str:
        """Determine the appropriate call-to-action type"""
        
        # Decision stage - direct action
        if context.journey_stage == "decision":
            return "schedule_call"
        
        # Evaluation stage - detailed information
        if context.journey_stage == "evaluation":
            return "request_demo"
        
        # Interest stage - learn more
        if context.journey_stage == "interest":
            return "learn_more"
        
        # Discovery stage - educational content
        if context.journey_stage == "discovery":
            return "educational_content"
        
        # High engagement - push for action
        if context.engagement_level == "high":
            return "schedule_call"
        
        # Low engagement - soft touch
        if context.engagement_level == "low":
            return "stay_connected"
        
        return "learn_more"
    
    def _determine_urgency_level(self, context: EnhancedCustomerContext) -> str:
        """Determine urgency level for responses"""
        
        # Urgent timeline
        if context.timeline == "urgent":
            return "high"
        
        # Short timeline
        if context.timeline == "short":
            return "medium"
        
        # High engagement with decision maker
        if context.engagement_level == "high" and context.decision_maker:
            return "medium"
        
        # Decision stage
        if context.journey_stage == "decision":
            return "medium"
        
        # Default
        return "low"
    
    def _determine_relationship_approach(self, context: EnhancedCustomerContext) -> str:
        """Determine relationship building approach"""
        
        # New customers - build trust
        if context.conversation_count <= 1:
            return "trust_building"
        
        # Engaged customers - deepen relationship
        if context.engagement_level == "high":
            return "relationship_deepening"
        
        # Decision makers - executive rapport
        if context.decision_maker:
            return "executive_rapport"
        
        # Analytical types - credibility focused
        if context.decision_making_style == "analytical":
            return "credibility_focused"
        
        # Default
        return "professional_friendly"
    
    def generate_personalized_prompt_additions(self, strategy: PersonalizationStrategy, 
                                             context: EnhancedCustomerContext) -> str:
        """Generate personalized additions to the system prompt"""
        try:
            prompt_additions = []
            
            # Response strategy guidance
            strategy_guidance = self._get_strategy_guidance(strategy.response_strategy)
            prompt_additions.append(f"RESPONSE STRATEGY: {strategy_guidance}")
            
            # Communication style guidance
            style_guidance = self._get_style_guidance(strategy.communication_style)
            prompt_additions.append(f"COMMUNICATION STYLE: {style_guidance}")
            
            # Personalization level guidance
            personalization_guidance = self._get_personalization_guidance(strategy.personalization_level)
            prompt_additions.append(f"PERSONALIZATION LEVEL: {personalization_guidance}")
            
            # Customer context
            if context.name:
                prompt_additions.append(f"CUSTOMER: {context.name} from {context.company or 'their company'}")
            
            # Journey stage context
            journey_guidance = self._get_journey_guidance(context.journey_stage)
            prompt_additions.append(f"CUSTOMER JOURNEY: {journey_guidance}")
            
            # Pain points to address
            if strategy.pain_points_to_address:
                pain_points_str = ", ".join(strategy.pain_points_to_address)
                prompt_additions.append(f"ADDRESS PAIN POINTS: {pain_points_str}")
            
            # Goals to highlight
            if strategy.goals_to_highlight:
                goals_str = ", ".join(strategy.goals_to_highlight)
                prompt_additions.append(f"HIGHLIGHT GOALS: {goals_str}")
            
            # Focus areas
            if strategy.key_focus_areas:
                focus_str = ", ".join(strategy.key_focus_areas)
                prompt_additions.append(f"KEY FOCUS AREAS: {focus_str}")
            
            # Examples to include
            if strategy.examples_to_include and context.prefers_examples:
                examples_str = ", ".join(strategy.examples_to_include)
                prompt_additions.append(f"INCLUDE EXAMPLES: {examples_str}")
            
            # Call to action
            cta_guidance = self._get_cta_guidance(strategy.call_to_action_type)
            prompt_additions.append(f"CALL TO ACTION: {cta_guidance}")
            
            # Urgency level
            urgency_guidance = self._get_urgency_guidance(strategy.urgency_level)
            prompt_additions.append(f"URGENCY LEVEL: {urgency_guidance}")
            
            # Relationship building
            relationship_guidance = self._get_relationship_guidance(strategy.relationship_building_approach)
            prompt_additions.append(f"RELATIONSHIP APPROACH: {relationship_guidance}")
            
            return "\n\n--- PERSONALIZATION GUIDANCE ---\n" + "\n".join(prompt_additions)
            
        except Exception as e:
            logger.error(f"Error generating personalized prompt additions: {e}")
            return ""
    
    def _get_strategy_guidance(self, strategy: ResponseStrategy) -> str:
        """Get guidance for response strategy"""
        guidance_map = {
            ResponseStrategy.EDUCATIONAL: "Focus on educating and informing. Provide valuable insights and build awareness.",
            ResponseStrategy.CONSULTATIVE: "Ask thoughtful questions to understand needs. Listen actively and provide tailored advice.",
            ResponseStrategy.SOLUTION_FOCUSED: "Present specific solutions that address their identified needs. Be direct about benefits.",
            ResponseStrategy.CLOSING: "Guide toward decision-making. Create urgency and provide clear next steps."
        }
        return guidance_map.get(strategy, "Provide helpful, relevant information.")
    
    def _get_style_guidance(self, style: CommunicationStyle) -> str:
        """Get guidance for communication style"""
        guidance_map = {
            CommunicationStyle.TECHNICAL: "Use technical language, provide detailed specifications, focus on implementation details.",
            CommunicationStyle.BUSINESS: "Focus on business benefits, ROI, efficiency gains, and strategic value.",
            CommunicationStyle.CONVERSATIONAL: "Use friendly, approachable tone. Be personable and engaging.",
            CommunicationStyle.FORMAL: "Maintain professional tone. Be structured and respectful."
        }
        return guidance_map.get(style, "Use professional, business-appropriate tone.")
    
    def _get_personalization_guidance(self, level: PersonalizationLevel) -> str:
        """Get guidance for personalization level"""
        guidance_map = {
            PersonalizationLevel.BASIC: "Use general information. Keep responses helpful but not overly specific.",
            PersonalizationLevel.CONTEXTUAL: "Reference their expressed interests and basic context.",
            PersonalizationLevel.RELATIONSHIP: "Leverage conversation history and demonstrated preferences.",
            PersonalizationLevel.CLOSING: "Use deep context knowledge to create compelling, personalized responses."
        }
        return guidance_map.get(level, "Provide helpful, contextual responses.")
    
    def _get_journey_guidance(self, journey_stage: str) -> str:
        """Get guidance for journey stage"""
        guidance_map = {
            "discovery": "They're learning about solutions. Focus on education and awareness building.",
            "interest": "They've shown interest. Help them understand how you can help their specific situation.",
            "evaluation": "They're comparing options. Differentiate your solution and address concerns.",
            "decision": "They're ready to decide. Provide confidence and clear next steps."
        }
        return guidance_map.get(journey_stage, "Adapt to their current needs and interests.")
    
    def _get_cta_guidance(self, cta_type: str) -> str:
        """Get guidance for call-to-action type"""
        guidance_map = {
            "schedule_call": "Suggest scheduling a call to discuss their specific needs.",
            "request_demo": "Offer a demo or detailed walkthrough of relevant features.",
            "learn_more": "Provide additional resources or offer to answer specific questions.",
            "educational_content": "Share helpful resources or insights related to their interests.",
            "stay_connected": "Offer to keep them updated on relevant developments."
        }
        return guidance_map.get(cta_type, "Offer appropriate next steps.")
    
    def _get_urgency_guidance(self, urgency_level: str) -> str:
        """Get guidance for urgency level"""
        guidance_map = {
            "high": "Create appropriate urgency. Mention time-sensitive opportunities or limited availability.",
            "medium": "Gently encourage action. Mention benefits of acting sooner rather than later.",
            "low": "Be patient and supportive. Focus on building relationship over pushing for immediate action."
        }
        return guidance_map.get(urgency_level, "Match their pace and comfort level.")
    
    def _get_relationship_guidance(self, approach: str) -> str:
        """Get guidance for relationship building approach"""
        guidance_map = {
            "trust_building": "Focus on establishing credibility and demonstrating expertise.",
            "relationship_deepening": "Build on existing rapport and show genuine interest in their success.",
            "executive_rapport": "Communicate at their level with strategic focus and respect for their time.",
            "credibility_focused": "Provide evidence, data, and logical reasoning to build confidence.",
            "professional_friendly": "Balance professionalism with warmth and approachability."
        }
        return guidance_map.get(approach, "Build positive rapport while maintaining professionalism.")
    
    def _get_default_strategy(self) -> PersonalizationStrategy:
        """Get default personalization strategy for fallback"""
        return PersonalizationStrategy(
            response_strategy=ResponseStrategy.CONSULTATIVE,
            communication_style=CommunicationStyle.BUSINESS,
            personalization_level=PersonalizationLevel.BASIC,
            key_focus_areas=["core_benefits"],
            pain_points_to_address=[],
            goals_to_highlight=[],
            examples_to_include=["general_success_story"],
            call_to_action_type="learn_more",
            urgency_level="low",
            relationship_building_approach="professional_friendly"
        )

# Global service instance
_personalization_engine = None

def get_personalization_engine() -> PersonalizationEngine:
    """Get global personalization engine instance"""
    global _personalization_engine
    if _personalization_engine is None:
        _personalization_engine = PersonalizationEngine()
    return _personalization_engine