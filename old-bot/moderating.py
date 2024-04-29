# Import necessary libraries
import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import json
from report import Report
from datetime import date
import asyncio

# Load environment variables
load_dotenv('../.env')
token = os.environ.get("MODERATOR_DISCORD_TOKEN")
if not token:
    print("Token is unreachable")
    exit()

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Initialize bot
client = commands.Bot(command_prefix="--", intents=intents)

# Define immune and moderator roles
immune_roles = ["algo", "developer", "moderator", "algomod helper", "ALG", "Mod", "mee6"]
mod_roles = ["Mod", "Moderator", "ALG", "Developer", "Admin"]

# Load banned words from file
with open("banned_words.json", 'r') as f:
    banned_words = json.load(f)['banned_words']

# Check if a message contains an invite link
def message_has_invite(message):
    return "https://discord" in message.content

def message_has_steam_gift(message):
    return ("steamcommunity.com/gift" or "50$") in message.content

async def mod(message, response, ban=False, kick=False, delete=True, delete_response=False):
    sent_message = await message.channel.send(response)
    report(message.author, content=message.content, reason="Use of banned phrase.", manual=False)
    if delete:
        await message.delete()
    if ban:
        print(f"Banning user: {message.author}\nMessage: {message.content}")
        await message.author.ban()
    elif kick:
        print(f"Kicking user: {message.author}\nMessage: {message.content}")
        await message.author.kick()

    if delete_response:
        async def delete_message():
            await asyncio.sleep(5)
            await sent_message.delete()

        # Create a task to delete the sent message
        asyncio.create_task(delete_message())



# Function to send warning report
def report(user, content=None, sev=1, reason=None, manual=False):
    doc = Report(user, content, sev, reason, manual)
    print(f"Sending warning report:\nUser: {user}\nContent: {content}\nSeverity: {sev}\nReason: {reason}")
    doc.log()

# Command to echo a message
@client.command()
async def echo(ctx, *msg):
    await ctx.message.channel.send(' '.join(msg))

# Command to ping
@client.command()
async def ping(ctx):
    await ctx.message.channel.send("Pong!")

# Check if user has moderator permissions
async def has_perms(user: discord.Member):
    user_roles = [role.name.lower() for role in user.roles]
    return any(role.lower() in user_roles for role in mod_roles)

# Check if user is immune
async def is_immune(user: discord.Member):
    user_roles = [role.name.lower() for role in user.roles]
    return any(role.lower() in user_roles for role in immune_roles)

# Function to retrieve log data for a member
def get_member_log(member: discord.Member):
    try:
        with open("reports_log.json", 'r') as f:
            data = json.load(f)
        user_data = data.get(str(member))
        return user_data
    except FileNotFoundError:
        print("Log file not found.")
        return None

# Function to get the number of warnings issued to a user today
def warnings_today(user_id: str) -> int:
    try:
        with open("reports_log.json", 'r') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = {}

    user_data = existing_data.get(user_id, {})
    if not user_data:
        return 0
    else:
        today_str = str(date.today())
        user_warnings_today = sum(1 for warning in user_data.get('warnings', []) if warning['date'] == today_str)
        return user_warnings_today

# Command to send log file
@client.command()
async def sendlog(ctx, member: discord.Member = None):
    if not await has_perms(ctx.message.author):
        await ctx.message.channel.send("You don't have permission to do that!")
        return
    everyone_perms = ctx.channel.overwrites_for(ctx.channel.guild.default_role)
    if everyone_perms.read_messages:
        await ctx.message.channel.send("Logs cannot be sent to public channels. (@everyone has read permissions in this channel.)")
        return
    try:
        if not member:
            with open("reports_log.json", "rb") as f:
                log_file = discord.File(f, filename="warnings_log.json")
                await ctx.send(file=log_file)
        else:
            with open('log_cache.txt', 'w') as f:
                json.dump(get_member_log(member), f, indent=4)
            with open('log_cache.txt', 'rb') as f:   
                log_file = discord.File(f, filename=f"{member}_log_file.json")
            await ctx.send(file=log_file)
    except FileNotFoundError:
        await ctx.send("JSON File not found. Please contact the bot administrator.")

# Command to warn users
@client.command()
async def warn(ctx, *args):
    if not await has_perms(ctx.message.author):
        await ctx.message.channel.send("You don't have permission to do that!")
        return
    if args:
        first_arg = args[0]
        try:
            sev = int(first_arg)
            reason = ' '.join(args[1:])
        except ValueError:
            sev = 1
            reason = ' '.join(args)
    else:
        sev = 1
        reason = None

    if ctx.message.reference:
        replied_message = await ctx.message.channel.fetch_message(ctx.message.reference.message_id)
        replied_author = replied_message.author
        await replied_message.delete()
        await ctx.message.channel.send(f"<@{replied_author.id}> you have been warned. Reason: {reason}")
        report(user=replied_author, content=replied_message.content, sev=sev, reason=reason, manual=True)
    else:
        await ctx.message.channel.send("You can only use --warn in a message reply to the target user. Try /warn")
    await ctx.message.delete()

# Check every message sent to the server
@client.event
async def on_message(message):
    await client.process_commands(message)

    if message.author == client.user:
        return
    # message = message to be checked (checks every message)
    # don't moderate if message is a DM
    if not message.guild:
        return
    member = message.guild.get_member(message.author.id)
    if member:
        # do not moderate messages from immune users (see `immune_roles`)
        if await is_immune(member):
            print(f"[Log] You are immune! Member: {message.author}")
            return
        
        if message_has_steam_gift(message=message):
            await mod(message, "Compromised account!", ban=True, delete_response=True)
            return
        
        if any(word in message.content for word in banned_words):
            if warnings_today(str(message.author)) >= 3:
                await mod(message, f"<@{message.author.id}> you cant say that idiot", kick=True, delete=True)
            else:
                await mod(message, f"<@{message.author.id}> you can't say that", delete_response=True)
            return
        
        if message_has_invite(message):
            if message.channel.id == 814757332944814100:
                return
            await mod(message, "You cannot send Discord server invites in this channel.", delete=True, delete_response=True)
            if message:
                await message.delete()
            return
    
# Start bot
client.run(token)
