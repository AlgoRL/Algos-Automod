from dotenv import load_dotenv
import os
import utils
import discord
from discord.ext import commands
import datetime
import json
from report import Report
import prereqs

class Mod:
    def __init__(self):
        pass

    async def check_user_reports(self, member: discord.Member):
        user_data = utils.MemberData(member)
        user_warnings_today = user_data.reports_today()
        if user_warnings_today < 2:
            pass
        if user_warnings_today == 2:
            await member.timeout(datetime.timedelta(hours=1))
            try:
                await member.send("You were timed out for 1 hour. Another warning today and you will be kicked.")
                await self.log_action(title="Timed Out User", description=f"**Member**: {member.name}\n**Member ID**: {member.id}")
            except discord.errors.Forbidden:
                if member.is_timed_out():
                    await self.log_action(title="Timed Out User", description=f"**Member**: {member.name}\n**Member ID**: {member.id}")
                    print("Could not DM user, but member was timed out.")
                else:
                    print("Member could not be timed out.")
        if user_warnings_today == 3:
            await member.kick()
            await self.log_action(title="Kicked User", description=f"**Member**: {member.name}\n**Member ID**: {member.id}")
        if user_warnings_today == 4:
            await member.ban()
            await self.log_action(title="Banned User", description=f"**Member**: {member.name}\n**Member ID**: {member.id}")
    
    async def log_action(self, title, description):
        embed_data = {
            "title": title,
            "description": description
        }
        await client.get_channel(1230350408233517156).send(embed=discord.Embed.from_dict(embed_data))

    async def check_message(self, message: discord.Message):
        guild_data_path = "./data/guild_data.json"
        with open(guild_data_path, 'r') as file:
            guild_data = json.load(file)
        apartment_channels = guild_data["apartment"]["channels"]
        algomod_channels = guild_data["algoMod"]["channels"]
        links_allowed = [
            apartment_channels["selfPromo"],
            apartment_channels["commands"],
            apartment_channels["clipShowcase"],
            apartment_channels["petPics"],
            apartment_channels["mediaArt"],
            apartment_channels["memes"],
            apartment_channels["carDesigns"]
        ]
        banned_words = guild_data["banned-words"]
        
        if utils.contains_banned_phrase(message, banned_words):
            reason = "Use of banned phrase."
            await self.report_message(message, reason)
            await message.delete()
            response = f"<@{message.author.id}> you have been warned.\nReason: {reason}"
            await message.channel.send(response)

        if utils.message_has_invite(message) and not message.channel.id == apartment_channels['selfPromo']:
            reason = "You cannot send server invites in this channel."
            await self.report_message(message, reason)
            await message.delete()
            response = f"<@{message.author.id}> you have been warned.\nReason: {reason}"
            await message.channel.send(response)

        if utils.message_has_steam_gift(message):
            reason = "Steam gifts are not allowed on this server."
            await self.report_message(message, reason)
            await message.delete()
            response = f"<@{message.author.id}> you have been warned.\nReason: {reason}"
            await message.channel.send(response)
        
    async def report_message(self, message: discord.Message, reason: str):
        if message.author.id == 262167257277399040: 
            return
        report = Report(
            user_id = message.author.id, 
            username = message.author.name,
            reporter = "Algo's Automod (Automatic)",
            msg_content = message.content,
            rsn_content = reason
        )
        await send_report_to_discord(report)
        await self.check_user_reports(message.author)

mod = Mod()

GUILD_DATA_PATH = './data/guild_data.json'
USER_DATA_PATH = './data/user_data.json'

# Load environment variables
load_dotenv('/core/.env')
token = os.environ.get("TOKEN")
if not token:
    utils.fatal("*TOKEN ERROR*", "Token not reachable.")

def load_guild_data():
    utils.log_process("UTIL", "Mounting Guild Data...")
    try:
        with open(GUILD_DATA_PATH, 'r') as data:
            guild_data = json.load(data)
    except FileNotFoundError:
        utils.fatal("*DATA ERROR*", "Guild Data could not be loaded.")
        return None
    return guild_data

guild_data = load_guild_data()

utils.log_process("UTIL", "Loading Bot Intents...")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
prefix = '--'
utils.log_process("INFO", f"Prefix is: '{prefix}'")
client = commands.Bot(command_prefix=prefix, intents=intents)

utils.log_process("UTIL", "Loading Immune Roles...")
# type: 2D tuple list
immune_roles = [(role, value) for role, value in guild_data['immune-roles'].items()]
role_ids = [role_id for _, role_id in immune_roles] # unpack role IDs from data extraction
role_names = [name for name, _ in immune_roles] # unpack role names from data extraction
# super inefficient but idc!! ^^ (only happens during initialization anyways)

@client.event
async def on_ready():
    await client.tree.sync()
    print("Ready!")

async def send_report_to_discord(report: Report):
    LOG_CHANNEL = guild_data["mod-log"]
    embed = report.compile_report()
    embed = discord.Embed.from_dict(embed)
    await client.get_channel(LOG_CHANNEL).send(embed=embed)

async def get_username_from_id(id: int):
    return await client.fetch_user(id)

async def is_immune(member: discord.Member) -> bool:
    if member == client.user: return True   # that should work right????
    roles = utils.get_roles(member) # list of IDs
    return any(role_id in roles for role_id in role_ids)

@client.event
async def on_message(message: discord.Message):
    await client.process_commands(message)
    if await is_immune(message.author): 
        print(f"You are immune! Name: {message.author.name}")
        return
    if message.author == client.user:
        return
    await mod.check_message(message)

# /report command
@client.tree.command(name="report", description="Reports a user.")
async def report(interaction, member: discord.Member, reason: str, message_content: str = None):
    if not await is_immune(interaction.user): 
        await interaction.response.send_message("You don't have permission to do that!", ephemeral=True)
        return
    report = Report(user_id=member.id, username=member.name, reporter=interaction.user.name, msg_content=message_content, rsn_content=reason)
    await send_report_to_discord(report=report)
    response = f"<@{member.id}> you have been warned.\nReason: {reason}"
    await interaction.response.send_message(response)
    await mod.check_user_reports(member)

# /getreport (member: discord.Member)
@client.tree.command(name="getreport", description="Gets the report data of a specified user.")
async def getreport(interaction, member: discord.Member):
    if not await is_immune(interaction.user): 
        await interaction.response.send_message("You don't have permission to do that!", ephemeral=True)
        return
    utils.log_process("TOOL", "User is using /getreport")
    member_data = utils.MemberData(member=member)
    if not member_data.reports:
        await interaction.response.send_message(f"User **{member.name}** has no reports on record.", ephemeral=True)
    else:
        embed_data = {
            "title": "User Reports",
            "description": (
                f'''
                **Member**: {member.name}\n
                **Reports on Record**: {member_data.reports_count()}\n
                **Reports Today**: {member_data.reports_at_date(datetime.datetime.now().strftime('%m/%d'))}
                '''
            ),
            'colour': discord.Colour.blue()
        }
        embed = discord.Embed.from_dict(embed_data)
        await interaction.response.send_message(embed=embed, ephemeral=True)


utils.log_process("INIT", "Initializing Bot...")
if prereqs.files_present():
    client.run(token)