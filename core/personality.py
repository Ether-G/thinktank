import json
import os
from typing import Dict, Optional
from models.personality import Personality

class PersonalityManager:
    def __init__(self):
        self.personalities: Dict[str, Personality] = {}
        self.personalities_dir = "personalities"
        self._load_personalities()

    def _load_personalities(self):
        """Load all personality JSON files from the personalities directory."""
        if not os.path.exists(self.personalities_dir):
            os.makedirs(self.personalities_dir)
            return

        for filename in os.listdir(self.personalities_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.personalities_dir, filename), 'r') as f:
                        personality_data = json.load(f)
                        personality = Personality(**personality_data)
                        self.personalities[personality.name.lower()] = personality
                except Exception as e:
                    print(f"Error loading personality {filename}: {str(e)}")

    async def get_personality(self, name: str) -> Optional[Personality]:
        """Get a personality by name (case-insensitive)."""
        return self.personalities.get(name.lower())

    def list_personalities(self) -> list[str]:
        """Get a list of all available personality names."""
        return list(self.personalities.keys())

    def add_personality(self, personality: Personality) -> bool:
        """Add a new personality and save it to a JSON file."""
        try:
            # Save to JSON file
            filename = f"{personality.name.lower()}.json"
            filepath = os.path.join(self.personalities_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(personality.model_dump(), f, indent=4)
            
            # Add to in-memory dictionary
            self.personalities[personality.name.lower()] = personality
            return True
        except Exception as e:
            print(f"Error adding personality {personality.name}: {str(e)}")
            return False 