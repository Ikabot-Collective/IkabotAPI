import json
import logging
import os

from apps.token.TokenGenerator import TokenGenerator

logger = logging.getLogger()

current_directory = os.path.dirname(os.path.abspath(__file__))
supported_user_agents = json.load(open(f"{current_directory}/SupportedUserAgents.json"))
token_generator = TokenGenerator(supported_user_agents=supported_user_agents)
