import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Load the environment variables from the .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
LEADERBOARD_CHANNEL_ID = int(os.getenv('LEADERBOARD_CHANNEL_ID'))

# Create an instance of a bot
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary to keep track of command usage
command_usage = {}

# Message ID of the leaderboard message (will be updated once the message is sent)
leaderboard_message_id = None

# Format the leaderboard message
def format_leaderboard():
    sorted_users = sorted(command_usage.items(), key=lambda x: x[1], reverse=True)
    leaderboard_message = "**Bump Leaderboard**\n\n"
    for user_id, count in sorted_users:
        leaderboard_message += f"<@{user_id}> - {count}\n"
    return leaderboard_message

# Event that triggers when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await setup_leaderboard()

# Function to setup the leaderboard message
async def setup_leaderboard():
    global leaderboard_message_id
    channel = bot.get_channel(LEADERBOARD_CHANNEL_ID)
    if channel is not None:
        leaderboard_message = format_leaderboard()
        message = await channel.send(leaderboard_message)
        leaderboard_message_id = message.id

# Event that triggers on every new message
@bot.event
async def on_message(message):
    if message.content == "/bump":
        user_id = message.author.id
        if user_id not in command_usage:
            command_usage[user_id] = 0
        command_usage[user_id] += 1

        await update_leaderboard()
    
    await bot.process_commands(message)

# Function to update the leaderboard message
async def update_leaderboard():
    global leaderboard_message_id
    channel = bot.get_channel(LEADERBOARD_CHANNEL_ID)
    if channel is not None:
        leaderboard_message = format_leaderboard()
        if leaderboard_message_id is not None:
            message = await channel.fetch_message(leaderboard_message_id)
            await message.edit(content=leaderboard_message)

# Keep-Alive HTTP Server
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"I'm alive")

def run_keep_alive_server():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, KeepAliveHandler)
    httpd.serve_forever()

# Start the keep-alive server in a background thread
keep_alive_thread = threading.Thread(target=run_keep_alive_server)
keep_alive_thread.daemon = True
keep_alive_thread.start()

# Run the bot with the token
bot.run(TOKEN)
