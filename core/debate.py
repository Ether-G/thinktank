import random
import logging
from typing import List, AsyncGenerator, Tuple
from models.personality import Personality
from core.llm_service import LLMService
from core.personality import PersonalityManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Debate:
    def __init__(self, input_statement: str, personalities: List[Personality], llm_service: LLMService):
        self.input_statement = input_statement
        self.personalities = personalities
        self.llm_service = llm_service
        self.history = []
        self.current_round = 0
        self.max_rounds = random.randint(3, 6)  # Random number of rounds between 3 and 6
        self.max_retries = 1  # Maximum number of retries for failed responses

    async def _get_response(self, personality: Personality, retry_count: int = 0) -> str:
        try:
            response = await self.llm_service.generate_response(
                personality=personality,
                input_statement=self.input_statement,
                debate_history=self.history
            )
            
            # Check for failure response
            if "sorry" in response.lower() and "can't fulfill" in response.lower():
                if retry_count < self.max_retries:
                    logger.warning(f"Personality {personality.name} failed to generate response. Retrying... (Attempt {retry_count + 1})")
                    # Add a debug message to help understand the context
                    logger.debug(f"Debate context: Round {self.current_round + 1}, History length: {len(self.history)}")
                    return await self._get_response(personality, retry_count + 1)
                else:
                    logger.error(f"Personality {personality.name} failed to generate response after {self.max_retries} attempts")
                    return f"I'm having trouble understanding this debate. Could we try a simpler topic?"
            
            return response
        except Exception as e:
            logger.error(f"Error generating response for {personality.name}: {str(e)}")
            return f"I'm having trouble understanding this debate. Could we try a simpler topic?"

    async def run_rounds(self) -> AsyncGenerator[Tuple[str, str, str], None]:
        # Send debate start message
        yield "DEBATE STARTED", f"Topic: {self.input_statement}\nParticipants: {', '.join(p.name for p in self.personalities)}", None

        while self.current_round < self.max_rounds:
            # Send round start message
            yield f"ROUND {self.current_round + 1}", "", None
            
            for personality in self.personalities:
                # Get response with retry mechanism
                response = await self._get_response(personality)
                
                # Get the last message to respond to
                last_message = self.history[-1] if self.history else None
                
                # Store the response in history
                self.history.append({
                    'personality': personality.name,
                    'response': response
                })
                
                # Yield the response with the personality name and the message to reply to
                yield personality.name, response.strip(), last_message['response'] if last_message else None
            
            self.current_round += 1
            
            # Check if we should end the debate early
            if await self._should_end_debate():
                break
        
        # Generate final summary
        summary = await self.llm_service.generate_summary(
            input_statement=self.input_statement,
            debate_history=self.history
        )
        
        # Send debate end and summary
        yield "DEBATE ENDED", "", None
        yield "FINAL SUMMARY", summary, None

    async def _should_end_debate(self) -> bool:
        # Implement logic to determine if debate should end early
        # This could be based on consensus, stalemate, or other criteria
        return False

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