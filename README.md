# ThinkTank Discord Bot

A Discord bot that facilitates philosophical debates between AI personalities, each with their own unique reasoning style and characteristics. The bot uses multiple LLM instances to create engaging and thought-provoking discussions.

## Features

- Dynamic philosophical debates between AI personalities
- Customizable personality traits and reasoning styles
- Support for multiple LLM providers (OpenAI and Anthropic)
- Round-robin debate format with random number of interactions
- Automatic debate summarization
- Easy addition of new philosophical personalities

## Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- OpenAI API Key
- Anthropic API Key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/thinktank.git
cd thinktank
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```env
DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

## Project Structure

```
thinktank/
├── bot/
│   ├── __init__.py
│   └── main.py           # Discord bot entry point
├── core/
│   ├── __init__.py
│   ├── debate.py         # Debate orchestration logic
│   ├── personality.py    # Personality management
│   └── llm_service.py    # LLM integration
├── models/
│   ├── __init__.py
│   └── personality.py    # Personality data model
├── config/
│   ├── __init__.py
│   └── models.json       # LLM model configurations
├── personalities/        # Personality JSON files
│   ├── socrates.json
│   └── nietzsche.json
├── .env                  # Environment variables
├── .gitignore
├── requirements.txt
└── README.md
```

## Configuration

### Model Configuration

The `config/models.json` file contains configurations for different LLM models:

```json
{
    "openai": {
        "gpt-4-turbo-preview": {
            "provider": "openai",
            "max_tokens": 500,
            "temperature": 0.7,
            "cost_per_1k_tokens": 0.03
        }
    },
    "anthropic": {
        "claude-3-opus-20240229": {
            "provider": "anthropic",
            "max_tokens": 500,
            "temperature": 0.7,
            "cost_per_1k_tokens": 0.015
        }
    }
}
```

### Adding New Personalities

Create a new JSON file in the `personalities` directory. Example structure:

```json
{
    "name": "PhilosopherName",
    "description": "Brief description",
    "philosophical_school": "School of thought",
    "key_philosophers": ["Influencer1", "Influencer2"],
    "core_beliefs": [
        "Belief 1",
        "Belief 2"
    ],
    "debate_style": "Description of debate style",
    "system_prompt": "Detailed instructions for the AI",
    "model_preferences": [
        {
            "provider": "anthropic",
            "model_name": "claude-3-opus-20240229",
            "temperature": 0.8,
            "max_tokens": 600
        }
    ]
}
```

## Usage

1. Start the bot:
```bash
python bot/main.py
```

2. In Discord, use the `/thinktank` command:
```
/thinktank "Is free will an illusion?" socrates,nietzsche
```

The bot will:
1. Load the specified personalities
2. Start a debate with a random number of rounds (3-6)
3. Each personality will respond in turn
4. Generate a summary at the end

## Available Personalities

- **Socrates**: Uses triangle-based reasoning and the Socratic method
- **Nietzsche**: Provocative and challenging, using powerful metaphors
- Add more by creating new JSON files in the `personalities` directory

## Customizing Personalities

Each personality can be customized through their JSON file:

- `name`: The personality's name
- `description`: Brief description of the philosopher
- `philosophical_school`: Their school of thought
- `key_philosophers`: Influential philosophers
- `core_beliefs`: List of fundamental beliefs
- `debate_style`: How they approach debates
- `system_prompt`: Instructions for the AI
- `model_preferences`: Preferred LLM models and settings

## Error Handling

The bot includes several fallback mechanisms:
- If a preferred model fails, it tries the next preferred model
- If all preferred models fail, it falls back to the default model
- If a personality isn't found, it lists available personalities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT models
- Anthropic for Claude models
- Discord.py for the Discord API wrapper 