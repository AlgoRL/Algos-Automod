import discord
import datetime
import json
def log_process(process_type, message):
    print(f"[{process_type}] {message}")

def fatal(process_type, message):
    print(f"FATAL: [{process_type}] {message}")
    exit()

# if names == True, return role names instead of IDs
# default return list of IDs
def get_roles(member: discord.Member, names=False):
    if names:
        return [y.name.lower() for y in member.roles]
    else:
        return [y.id for y in member.roles]

def message_has_steam_gift(message: discord.Message):
    return ("steamcommunity.com/gift" or "50$") in message.content

def message_has_invite(message: discord.Message):
    return "https://discord" in message.content

def message_has_link(message: discord.Message):
    return ("http://" or "https://") in message.content

def format_datetime(timestamp: datetime.datetime):
    formatted = timestamp.strftime('%m/%d @ %H:%M:%S EST')
    return formatted

def contains_banned_phrase(message: discord.Message, banned_phrases: list):
    if any(word in message.content.lower() for word in banned_phrases):
        return True
    return False

def get_member_data(member: discord.Member):
    with open('./data/user_data.json', 'r') as file:
        data = json.load(file)
    if data[str(member.id)]:
        return data[str(member.id)]
    else:
        return None

class MemberData:
    def __init__(self, member):
        self.member = member
        self.reports = get_member_data(member)
    
    def reports_count(self):
        return len(self.reports)
    
    def reports_today(self):
        date = datetime.datetime.now().strftime('%m/%d')
        reports_count = 0
        for report in self.reports:
            if date in report:
                reports_count += 1
        return reports_count
    
    def reports_at_date(self, date: str):
        # date format: 'mm/dd'
        reports_count = 0
        for report in self.reports:
            if date in report:
                reports_count += 1
        return reports_count
    
    def __str__(self):
        return f"{self.reports}"
