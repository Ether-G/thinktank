import random
import logging
from typing import List, AsyncGenerator, Tuple, Dict
from models.personality import Personality
from core.llm_service import LLMService
from core.personality import PersonalityManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DebateFormat:
    def __init__(self, name: str, description: str, structure: List[Dict[str, str]]):
        self.name = name
        self.description = description
        self.structure = structure

class Debate:
    def __init__(self, input_statement: str, personalities: List[Personality], llm_service: LLMService):
        self.input_statement = input_statement
        self.personalities = personalities
        self.llm_service = llm_service
        self.history = []
        self.current_round = 0
        self.max_rounds = 3  # Fixed number of rounds for structured debate
        self.active_personalities = personalities.copy()
        
        # Standard debate formats
        self.formats = {
            "classical": DebateFormat(
                name="Classical Debate",
                description="A formal debate with opening statements, rebuttals, and closing arguments",
                structure=[
                    {"type": "opening", "description": "Each participant presents their initial position"},
                    {"type": "rebuttal", "description": "Participants address and counter each other's arguments"},
                    {"type": "closing", "description": "Final statements summarizing key points and positions"}
                ]
            ),
            "socratic": DebateFormat(
                name="Socratic Dialogue",
                description="A question-based debate format focusing on critical examination",
                structure=[
                    {"type": "question", "description": "Initial question to explore the topic"},
                    {"type": "response", "description": "Direct responses to questions"},
                    {"type": "followup", "description": "Follow-up questions and clarifications"}
                ]
            ),
            "cross_examination": DebateFormat(
                name="Cross-Examination",
                description="Direct questioning format with focused exchanges",
                structure=[
                    {"type": "direct", "description": "Direct questions to other participants"},
                    {"type": "response", "description": "Answers to questions"},
                    {"type": "rebuttal", "description": "Counter-arguments and clarifications"}
                ]
            ),
            "lincoln_douglas": DebateFormat(
                name="Lincoln-Douglas Debate",
                description="A value-based debate format focusing on moral and philosophical issues",
                structure=[
                    {"type": "constructive", "description": "Present core arguments and value framework"},
                    {"type": "crossfire", "description": "Direct questioning and defense of positions"},
                    {"type": "final_focus", "description": "Final appeal to core values and principles"}
                ]
            ),
            "policy": DebateFormat(
                name="Policy Debate",
                description="A structured debate format focusing on policy proposals and their implications",
                structure=[
                    {"type": "proposal", "description": "Present policy proposal and its benefits"},
                    {"type": "analysis", "description": "Analyze impacts and potential consequences"},
                    {"type": "evaluation", "description": "Evaluate effectiveness and feasibility"}
                ]
            ),
            "parliamentary": DebateFormat(
                name="Parliamentary Debate",
                description="A dynamic debate format with impromptu topics and rapid responses",
                structure=[
                    {"type": "motion", "description": "Present and defend the motion"},
                    {"type": "opposition", "description": "Challenge and counter the motion"},
                    {"type": "rebuttal", "description": "Final defense and summary"}
                ]
            )
        }
        
        # Select a random debate format
        self.current_format = random.choice(list(self.formats.values()))
        logger.info(f"Selected debate format: {self.current_format.name}")

    async def _get_moderator_message(self, round_type: str) -> str:
        """Generate a moderator message for the current round."""
        system_prompt = f"""You are a debate moderator for a {self.current_format.name} debate. Your role is to:
1. Guide the debate structure according to {self.current_format.name} format
2. Ensure participants stay on topic
3. Maintain order and fairness
4. Provide context for each round

Keep your messages under 100 characters and be direct."""

        current_prompt = f"""The debate topic is: {self.input_statement}
Current round type: {round_type}
Format: {self.current_format.name}
Round description: {self.current_format.structure[self.current_round]['description']}

Provide a brief moderator message to introduce this round. Keep it under 100 characters."""

        try:
            response = await self.llm_service.generate_response(
                personality=Personality(
                    name="Moderator",
                    description="Debate moderator",
                    system_prompt=system_prompt
                ),
                input_statement=current_prompt,
                debate_history=self.history
            )
            return response
        except Exception as e:
            logger.error(f"Error generating moderator message: {str(e)}")
            return f"Round {round_type}: Present your arguments."

    async def _get_response(self, personality: Personality, round_type: str, retry_count: int = 0) -> str:
        try:
            logger.info(f"Getting response from {personality.name}")
            
            # Add round context to the system prompt
            round_context = f"""\nCurrent round: {round_type}
Format: {self.current_format.name}
Round description: {self.current_format.structure[self.current_round]['description']}"""
            
            response = await self.llm_service.generate_response(
                personality=personality,
                input_statement=self.input_statement,
                debate_history=self.history,
                additional_context=round_context
            )
            
            logger.info(f"Got response from {personality.name}: {response[:50]}...")
            
            if "sorry" in response.lower() and "can't fulfill" in response.lower():
                if retry_count < 1:
                    logger.warning(f"Personality {personality.name} failed to generate response. Retrying...")
                    return await self._get_response(personality, round_type, retry_count + 1)
                else:
                    logger.error(f"Personality {personality.name} failed to generate response after retries")
                    return f"I need more time to formulate my thoughts on this matter."
            
            return response
        except Exception as e:
            logger.error(f"Error generating response for {personality.name}: {str(e)}")
            return f"I'm having trouble articulating my position at the moment."

    async def run_rounds(self) -> AsyncGenerator[Tuple[str, str, str], None]:
        # Send debate start message
        yield "DEBATE STARTED", f"Topic: {self.input_statement}\nFormat: {self.current_format.name}", None

        # Get moderator's opening message
        moderator_message = await self._get_moderator_message("opening")
        yield "MODERATOR", moderator_message, None

        while self.current_round < self.max_rounds:
            round_type = self.current_format.structure[self.current_round]["type"]
            
            # Get moderator's round introduction
            round_intro = await self._get_moderator_message(round_type)
            yield f"ROUND {self.current_round + 1}", round_intro, None
            
            for personality in self.active_personalities:
                # Get response with retry mechanism
                response = await self._get_response(personality, round_type)
                
                # Get the last message to respond to
                last_message = self.history[-1] if self.history else None
                
                # Store the response in history
                self.history.append({
                    'personality': personality.name,
                    'response': response,
                    'round_type': round_type
                })
                
                # Yield the response
                yield personality.name, response.strip(), last_message['response'] if last_message else None
            
            self.current_round += 1
            
            # Get moderator's round conclusion
            round_conclusion = await self._get_moderator_message(f"{round_type}_conclusion")
            yield "MODERATOR", round_conclusion, None
        
        # Generate final summary and determine winner
        summary = await self.llm_service.generate_summary(
            input_statement=self.input_statement,
            debate_history=self.history,
            personalities=self.personalities
        )
        
        # Send debate end and summary
        yield "DEBATE ENDED", "", None
        yield "FINAL SUMMARY", summary, None

class DebateOrchestrator:
    def __init__(self):
        self.llm_service = LLMService()
        self.personality_manager = PersonalityManager()

    async def start_debate(self, input_statement: str, debators: List[str]) -> Debate:
        # Load personalities for the specified debators
        personalities = []
        for debator_name in debators:
            personality = await self.personality_manager.get_personality(debator_name)
            if personality:
                personalities.append(personality)
            else:
                raise ValueError(f"Personality '{debator_name}' not found. Available personalities: {', '.join(self.personality_manager.list_personalities())}")
        
        if not personalities:
            raise ValueError("No valid personalities found for the debate")
        
        return Debate(input_statement, personalities, self.llm_service) 