import random
from typing import List, AsyncGenerator
from models.personality import Personality
from core.llm_service import LLMService
from core.personality import PersonalityManager

class Debate:
    def __init__(self, input_statement: str, personalities: List[Personality], llm_service: LLMService):
        self.input_statement = input_statement
        self.personalities = personalities
        self.llm_service = llm_service
        self.history = []
        self.current_round = 0
        self.max_rounds = random.randint(3, 6)  # Random number of rounds between 3 and 6

    async def run_rounds(self) -> AsyncGenerator[str, None]:
        while self.current_round < self.max_rounds:
            for personality in self.personalities:
                # Generate response based on personality and debate history
                response = await self.llm_service.generate_response(
                    personality=personality,
                    input_statement=self.input_statement,
                    debate_history=self.history
                )
                
                self.history.append({
                    'personality': personality.name,
                    'response': response
                })
                
                yield f"**{personality.name}**: {response}"
            
            self.current_round += 1
            
            # Check if we should end the debate early
            if await self._should_end_debate():
                break
        
        # Generate final summary
        summary = await self.llm_service.generate_summary(
            input_statement=self.input_statement,
            debate_history=self.history
        )
        yield f"\n**Debate Summary**:\n{summary}"

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