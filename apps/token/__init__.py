import json
import logging
import os

logger = logging.getLogger()

current_directory = os.path.dirname(os.path.abspath(__file__))
with open(f"{current_directory}/SupportedUserAgents.json") as user_agents_file:
    supported_user_agents = json.load(user_agents_file)
