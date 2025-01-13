import json
from typing import Dict, Any
from agent import Agent
import config
import logging

logger = logging.getLogger(__name__)

with open('system_messages.json', 'r') as f:
    system_messages = json.load(f)

class Debugger(Agent):
    def __init__(self, api_key: str):
        super().__init__("Debugger", api_key)

    def handle_error(self, error_message: str, context: str) -> Dict[str, Any]:
        """Handle errors and provide quick fixes."""
        system_message = system_messages["Debugger"]["handle_error"]
        
        user_message = f"Error Message:\n{error_message}\n\nContext:\n{context}\n\nPlease provide a quick fix for the encountered error, along with an explanation of the reason for the error. Respond with the fix in JSON format, including any necessary commands to be executed in the correct order."
        
        try:
            debugger_response = self.generate_response("Command_Monitor", user_message, system_message, response_format={"type": "json_object"})
            self.print_agent_output(text=debugger_response)
            return json.loads(debugger_response)
        except Exception as e:
            logger.error(f"Error handling error: {str(e)}")
            raise
