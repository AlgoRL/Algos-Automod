import datetime
import discord
import utils
import json
import os

# server required storage: user_id, timestamp
# total_warnings will be derived from a count of the user_id's warning count stored on server
# can use json file to store, user_id being key, timestamps being multiple values for dict

class Report:
    def __init__(self, user_id, username, reporter, msg_content=None, rsn_content=None):
        self.user_id = str(user_id)
        self.username = username
        self.reporter = reporter
        self.msg_content = msg_content
        self.rsn_content = rsn_content
        self.timestamp = utils.format_datetime(datetime.datetime.now())
        self.total_warnings = None
        self.log_report()

    def log_report(self):
        file_path = "./data/user_data.json"
        
        # Load existing data or create an empty dictionary
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                data = json.load(file)
        else:
            print("user_data not found!")
            data = {}

        # Update data with new timestamp
        if self.user_id not in data:
            data[self.user_id] = []
            print(f"{self.user_id} not found in data.")
        data[self.user_id].append(self.timestamp)

        # Write updated data back to file
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

        # Update total_warnings attribute
        self.total_warnings = len(data[self.user_id])

    def get_warning_count(self):
        file_path = "./data/user_data.json"
        if not os.path.exists(file_path):
            return "Data not found..."
    
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        if self.user_id in data:
            return len(data[self.user_id])
        else:
            return 0

    def compile_report(self):
        report_message = {
            "title": "Report Made",
            "description": (
                f'''
                **User ID**: {self.user_id}\n
                **Username**: {self.username}\n
                **Reporter**: {self.reporter}\n
                **Message Content**: {self.msg_content}\n
                **Reason Content**: {self.rsn_content}\n
                **Date & Time**: {self.timestamp}\n
                **Total Warnings**: {self.total_warnings}
                '''
            ),
            'colour': discord.Colour.blue()
        }
        return report_message


            



