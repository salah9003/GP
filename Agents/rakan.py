import json
from typing import Dict, Any, List
from agent import Agent
import config
import logging

logger = logging.getLogger(__name__)

with open('system_messages.json', 'r') as f:
    system_messages = json.load(f)

class Command_Monitor(Agent):
    def __init__(self, api_key: str):
        super().__init__("Command_Monitor", api_key)

    def monitor_output(self, target_ip: str, scan_description: str, command_output: str, executed_commands: List[str], pending_commands: List[str]) -> Dict[str, Any]:
        """Monitor command output and determine if input is required."""
        system_message = system_messages["Command_Monitor"]["monitor_output"]
        
        user_message = f"Target IP: {target_ip}\nScan Description: {scan_description}\nCommand Output:\n{command_output}\nExecuted Commands: {json.dumps(executed_commands)}\nPending Commands: {json.dumps(pending_commands)}\n\nAnalyze the command output and determine if input is required or if the command is still running or loading up. Respond with your analysis in JSON format, using the 'input_needed' key as a boolean value."
        
        try:
            command_monitor_response = self.generate_response("Command_Monitor", user_message, system_message, response_format={"type": "json_object"})
            self.add_to_chat_history("Command_Monitor", "user", user_message)
            self.add_to_chat_history("Command_Monitor", "assistant", command_monitor_response)
            self.print_agent_output(text=command_monitor_response)
            return json.loads(command_monitor_response)
        except Exception as e:
            logger.error(f"Error monitoring output: {str(e)}")
            raise
