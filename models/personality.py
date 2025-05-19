from pydantic import BaseModel
from typing import Optional, List, Dict

class ModelPreference(BaseModel):
    provider: str  # "openai" or "anthropic"
    model_name: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500

class Personality(BaseModel):
    name: str
    description: str
    system_prompt: str
    philosophical_school: Optional[str] = None
    key_philosophers: Optional[list[str]] = None
    core_beliefs: Optional[list[str]] = None
    debate_style: Optional[str] = None
    model_preferences: Optional[List[ModelPreference]] = None
    
    def get_full_system_prompt(self) -> str:
        """Generate a comprehensive system prompt for the personality."""
        prompt = f"""You are {self.name}, a philosophical thinker with the following characteristics:

Description: {self.description}

Philosophical School: {self.philosophical_school or 'Not specified'}

Key Influences: {', '.join(self.key_philosophers) if self.key_philosophers else 'Not specified'}

Core Beliefs:
{chr(10).join(f'- {belief}' for belief in self.core_beliefs) if self.core_beliefs else 'Not specified'}

Debate Style: {self.debate_style or 'Not specified'}

Additional Instructions:
1. Stay true to your philosophical perspective
2. Engage directly with other arguments
3. Use examples and analogies to illustrate your points
4. Be passionate but respectful
5. Reference relevant philosophical concepts and thinkers
6. Maintain consistency with your stated beliefs and style

{self.system_prompt}"""
        return prompt 