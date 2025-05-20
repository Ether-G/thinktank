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
        # Get available personalities for the command
        available_personalities = self.personality_manager.list_personalities()
        
        # Create the thinktank command with auto-populated choices
        @self.tree.command(name="thinktank", description="Start a debate between AI personalities")
        @app_commands.describe(
            input_statement="The topic or statement to debate",
            debators="Choose the personalities to participate in the debate"
        )
        async def thinktank(
            interaction: discord.Interaction,
            input_statement: str,
            debators: str = None
        ):
            # If no debators specified, use all available personalities
            if not debators:
                debators = ",".join(available_personalities)
            
            # Split the debators string into a list
            debator_list = [d.strip() for d in debators.split(',')]
            
            # Start the debate
            await interaction.response.defer()
            
            try:
                # Initialize the debate
                debate = await self.debate_orchestrator.start_debate(
                    input_statement=input_statement,
                    debators=debator_list
                )
                
                # Create a thread for the debate
                thread = await interaction.channel.create_thread(
                    name=f"Debate: {input_statement[:50]}...",
                    type=discord.ChannelType.public_thread
                )
                
                # Send initial message
                last_message = None
                async for title, content, reply_to in debate.run_rounds():
                    if title in ["DEBATE STARTED", "ROUND", "DEBATE ENDED"]:
                        # Send as a new message with a header
                        last_message = await thread.send(f"**{title}**\n{content}")
                    else:
                        # Send as a reply to the last message
                        if reply_to and last_message:
                            last_message = await thread.send(
                                f"**{title}**: {content}",
                                reference=last_message
                            )
                        else:
                            last_message = await thread.send(f"**{title}**: {content}")
                    
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {str(e)}")
        
        # Sync the command tree
        await self.tree.sync()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

bot = ThinkTankBot()

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN')) 