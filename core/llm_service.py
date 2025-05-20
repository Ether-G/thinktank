import os
import json
from typing import List, Dict, Any
import openai
from anthropic import AsyncAnthropic
from models.personality import Personality, ModelPreference

class LLMService:
    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # Initialize Anthropic client
        self.anthropic_client = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        # Load model configurations
        self.model_configs = self._load_model_configs()
        
        # Default model configuration
        self.default_model = ModelPreference(
            provider="openai",
            model_name="gpt-4-turbo-preview",
            temperature=0.9,
            max_tokens=300
        )
        
        # Discord message length limit
        self.discord_limit = 1900  # Setting slightly lower than 2000 for safety

    def _load_model_configs(self) -> Dict:
        """Load model configurations from config file."""
        try:
            with open('config/models.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading model configs: {str(e)}")
            return {}

    def _get_model_config(self, personality: Personality) -> ModelPreference:
        """Get the appropriate model configuration for a personality."""
        if personality.model_preferences:
            # Try each preferred model in order
            for pref in personality.model_preferences:
                provider_config = self.model_configs.get(pref.provider, {})
                if pref.model_name in provider_config:
                    return pref
        return self.default_model

    def _truncate_response(self, response: str) -> str:
        """Truncate response to fit within Discord's character limit."""
        if len(response) > self.discord_limit:
            # Find the last complete sentence before the limit
            truncated = response[:self.discord_limit]
            last_period = truncated.rfind('.')
            if last_period > 0:
                return truncated[:last_period + 1]
            return truncated + "..."
        return response

    async def generate_response(
        self,
        personality: Personality,
        input_statement: str,
        debate_history: List[Dict[str, str]]
    ) -> str:
        # Get model configuration
        model_config = self._get_model_config(personality)
        
        # Get the system prompt
        system_prompt = personality.get_full_system_prompt()
        
        # Add length limit instruction to system prompt
        system_prompt += "\n\nIMPORTANT: Keep your response under 500 characters. Be aggressive and confrontational. Attack the other philosopher's position. Use strong, provocative language. Don't be afraid to be controversial or offensive."
        
        # Construct the conversation history
        messages = []
        
        # Add debate history
        for entry in debate_history:
            messages.append({
                "role": "user",
                "content": f"{entry['personality']}: {entry['response']}"
            })
        
        # Add the current prompt
        current_prompt = f"Debate topic: {input_statement}\n\nAs {personality.name}, provide a short, aggressive response attacking the other philosopher's position. Be confrontational and controversial. Keep your response under 500 characters."

        try:
            if model_config.provider == "openai":
                # OpenAI format
                openai_messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": current_prompt}
                ]
                if messages:
                    openai_messages.extend(messages)
                
                response = await self.openai_client.chat.completions.create(
                    model=model_config.model_name,
                    messages=openai_messages,
                    temperature=model_config.temperature,
                    max_tokens=model_config.max_tokens
                )
                return self._truncate_response(response.choices[0].message.content)
                
            elif model_config.provider == "anthropic":
                # Anthropic format
                anthropic_messages = []
                if messages:
                    anthropic_messages.extend(messages)
                anthropic_messages.append({"role": "user", "content": current_prompt})
                
                response = await self.anthropic_client.messages.create(
                    model=model_config.model_name,
                    system=system_prompt,
                    messages=anthropic_messages,
                    max_tokens=model_config.max_tokens,
                    temperature=model_config.temperature
                )
                return self._truncate_response(response.content[0].text)
            else:
                raise ValueError(f"Unknown provider: {model_config.provider}")
                
        except Exception as e:
            # If the preferred model fails, try the default model
            if model_config != self.default_model:
                print(f"Error with preferred model, falling back to default: {str(e)}")
                return await self.generate_response(
                    personality=personality,
                    input_statement=input_statement,
                    debate_history=debate_history
                )
            raise Exception(f"LLM service failed: {str(e)}")

    async def generate_summary(
        self,
        input_statement: str,
        debate_history: List[Dict[str, str]]
    ) -> str:
        # Use default model for summary
        model_config = self.default_model
        
        system_prompt = "You are an impartial debate moderator. Your task is to summarize the key points of the debate and identify areas of agreement and disagreement. Keep your summary under 500 characters."
        
        messages = []
        for entry in debate_history:
            messages.append({
                "role": "user",
                "content": f"{entry['personality']}: {entry['response']}"
            })
        
        current_prompt = f"Debate topic: {input_statement}\n\nPlease provide a concise summary of the debate, highlighting the main arguments, points of agreement, and areas of contention. Keep your response under 500 characters."

        try:
            if model_config.provider == "openai":
                openai_messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": current_prompt}
                ]
                if messages:
                    openai_messages.extend(messages)
                
                response = await self.openai_client.chat.completions.create(
                    model=model_config.model_name,
                    messages=openai_messages,
                    temperature=model_config.temperature,
                    max_tokens=model_config.max_tokens
                )
                return self._truncate_response(response.choices[0].message.content)
                
            elif model_config.provider == "anthropic":
                anthropic_messages = []
                if messages:
                    anthropic_messages.extend(messages)
                anthropic_messages.append({"role": "user", "content": current_prompt})
                
                response = await self.anthropic_client.messages.create(
                    model=model_config.model_name,
                    system=system_prompt,
                    messages=anthropic_messages,
                    max_tokens=model_config.max_tokens,
                    temperature=model_config.temperature
                )
                return self._truncate_response(response.content[0].text)
            else:
                raise ValueError(f"Unknown provider: {model_config.provider}")
                
        except Exception as e:
            raise Exception(f"LLM service failed: {str(e)}") 