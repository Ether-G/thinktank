import os
import json
from typing import List, Dict, Any
import openai
from anthropic import Anthropic
from models.personality import Personality, ModelPreference

class LLMService:
    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # Initialize Anthropic client
        self.anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        # Load model configurations
        self.model_configs = self._load_model_configs()
        
        # Default model configuration
        self.default_model = ModelPreference(
            provider="openai",
            model_name="gpt-4-turbo-preview",
            temperature=0.7,
            max_tokens=500
        )

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

    async def generate_response(
        self,
        personality: Personality,
        input_statement: str,
        debate_history: List[Dict[str, str]]
    ) -> str:
        # Get model configuration
        model_config = self._get_model_config(personality)
        
        # Construct the conversation history
        messages = [
            {"role": "system", "content": personality.get_full_system_prompt()},
            {"role": "user", "content": f"Debate topic: {input_statement}\n\nPrevious debate history:"}
        ]
        
        # Add debate history
        for entry in debate_history:
            messages.append({
                "role": "assistant",
                "content": f"{entry['personality']}: {entry['response']}"
            })
        
        # Add the current prompt
        messages.append({
            "role": "user",
            "content": f"As {personality.name}, provide your response to the debate topic and previous arguments. Be true to your philosophical perspective and engage with the previous arguments."
        })

        try:
            if model_config.provider == "openai":
                response = await self.openai_client.chat.completions.create(
                    model=model_config.model_name,
                    messages=messages,
                    temperature=model_config.temperature,
                    max_tokens=model_config.max_tokens
                )
                return response.choices[0].message.content
            elif model_config.provider == "anthropic":
                response = await self.anthropic_client.messages.create(
                    model=model_config.model_name,
                    messages=messages,
                    max_tokens=model_config.max_tokens,
                    temperature=model_config.temperature
                )
                return response.content[0].text
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
        
        messages = [
            {"role": "system", "content": "You are an impartial debate moderator. Your task is to summarize the key points of the debate and identify areas of agreement and disagreement."},
            {"role": "user", "content": f"Debate topic: {input_statement}\n\nDebate history:"}
        ]
        
        # Add debate history
        for entry in debate_history:
            messages.append({
                "role": "assistant",
                "content": f"{entry['personality']}: {entry['response']}"
            })
        
        messages.append({
            "role": "user",
            "content": "Please provide a comprehensive summary of the debate, highlighting the main arguments, points of agreement, and areas of contention."
        })

        try:
            if model_config.provider == "openai":
                response = await self.openai_client.chat.completions.create(
                    model=model_config.model_name,
                    messages=messages,
                    temperature=model_config.temperature,
                    max_tokens=model_config.max_tokens
                )
                return response.choices[0].message.content
            elif model_config.provider == "anthropic":
                response = await self.anthropic_client.messages.create(
                    model=model_config.model_name,
                    messages=messages,
                    max_tokens=model_config.max_tokens,
                    temperature=model_config.temperature
                )
                return response.content[0].text
            else:
                raise ValueError(f"Unknown provider: {model_config.provider}")
        except Exception as e:
            raise Exception(f"LLM service failed: {str(e)}") 