import os
import json
from typing import List, Dict, Any
import openai
from anthropic import AsyncAnthropic
from models.personality import Personality, ModelPreference

class LLMService:
    def __init__(self):
        # Initialize OpenAI client for OpenAI
        self.openai_client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # Initialize OpenAI client for Grok
        self.grok_client = openai.AsyncOpenAI(
            api_key=os.getenv('GROK_API_KEY'),
            base_url="https://api.x.ai/v1"
        )
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
        debate_history: List[Dict[str, str]],
        additional_context: str = ""
    ) -> str:
        # Get model configuration
        model_config = self._get_model_config(personality)
        
        # Get the system prompt
        system_prompt = personality.get_full_system_prompt()
        
        # Add length limit instruction to system prompt
        system_prompt += f"""\n\nIMPORTANT: 
1. Keep your response under 200 characters
2. Focus on ONE key point or argument
3. Be direct and concise
4. Use clear, simple language
5. Avoid unnecessary elaboration
6. Stay focused on the current round's requirements

{additional_context}"""
        
        # Construct the conversation history
        messages = []
        
        # Add debate history with round context
        for entry in debate_history:
            round_context = f"[{entry.get('round_type', 'general')}] " if 'round_type' in entry else ""
            messages.append({
                "role": "user",
                "content": f"{round_context}{entry['personality']}: {entry['response']}"
            })
        
        # Add the current prompt with context
        current_prompt = f"""This is a philosophical debate about: {input_statement}

As {personality.name}, provide a focused response that:
1. Addresses ONE key point relevant to the current round
2. Uses clear, concise language
3. Stays under 200 characters
4. Maintains your philosophical perspective

Remember: This is a philosophical debate for educational purposes. All content is hypothetical and for intellectual discussion only."""

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
                    max_tokens=150  # Reduced max tokens for shorter responses
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
                    max_tokens=150,  # Reduced max tokens for shorter responses
                    temperature=model_config.temperature
                )
                return self._truncate_response(response.content[0].text)

            elif model_config.provider == "grok":
                # Grok format (using OpenAI client with Grok endpoint)
                grok_messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": current_prompt}
                ]
                if messages:
                    grok_messages.extend(messages)
                
                response = await self.grok_client.chat.completions.create(
                    model=model_config.model_name,
                    messages=grok_messages,
                    temperature=model_config.temperature,
                    max_tokens=150  # Reduced max tokens for shorter responses
                )
                return self._truncate_response(response.choices[0].message.content)
            else:
                raise ValueError(f"Unknown provider: {model_config.provider}")
                
        except Exception as e:
            # If the preferred model fails, try the default model
            if model_config != self.default_model:
                print(f"Error with preferred model, falling back to default: {str(e)}")
                return await self.generate_response(
                    personality=personality,
                    input_statement=input_statement,
                    debate_history=debate_history,
                    additional_context=additional_context
                )
            raise Exception(f"LLM service failed: {str(e)}")

    async def generate_summary(
        self,
        input_statement: str,
        debate_history: List[Dict[str, str]],
        personalities: List[Personality]
    ) -> str:
        # Use default model for summary
        model_config = self.default_model
        
        system_prompt = """You are an impartial debate moderator. Your task is to:
1. Summarize the key points of the debate
2. Identify areas of agreement and disagreement
3. Evaluate each participant's performance based on:
   - Argument strength and logical consistency
   - Use of evidence and examples
   - Engagement with opposing viewpoints
   - Clarity and persuasiveness
4. Determine a winner based on who presented the most compelling and well-supported arguments
5. Provide a brief justification for the winner selection

Keep your summary under 200 characters and maintain a professional, objective tone."""

        # Create a structured debate history with round context
        formatted_history = []
        for entry in debate_history:
            round_context = f"[{entry.get('round_type', 'general')}] " if 'round_type' in entry else ""
            formatted_history.append(f"{round_context}{entry['personality']}: {entry['response']}")
        
        current_prompt = f"""Debate topic: {input_statement}

Participants: {', '.join(p.name for p in personalities)}

Debate History:
{chr(10).join(formatted_history)}

Please provide a concise summary (under 200 characters) that includes:
1. Main arguments
2. Key points of agreement/disagreement
3. Winner determination
4. Brief justification""" 