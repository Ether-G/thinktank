import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from core.debate import DebateOrchestrator
from core.personality import PersonalityManager

# Load environment variables
load_dotenv()

class ThinkTankBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='/', intents=intents)
        self.debate_orchestrator = DebateOrchestrator()
        self.personality_manager = PersonalityManager()

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

bot = ThinkTankBot()

@bot.tree.command(name="thinktank", description="Start a debate between AI personalities")
async def thinktank(
    interaction: discord.Interaction,
    input_statement: str,
    debators: str
):
    # Split the debators string into a list
    debator_list = [d.strip() for d in debators.split(',')]
    
    # Start the debate
    await interaction.response.defer()
    
    try:
        # Initialize the debate
        debate = await bot.debate_orchestrator.start_debate(
            input_statement=input_statement,
            debators=debator_list
        )
        
        # Send initial message
        await interaction.followup.send(f"Starting debate on: {input_statement}\nParticipants: {', '.join(debator_list)}")
        
        # Run the debate rounds
        async for message in debate.run_rounds():
            await interaction.followup.send(message)
            
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN')) 