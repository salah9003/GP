import json
from typing import Dict, Any, Optional
from agent import Agent
import config
import logging

logger = logging.getLogger(__name__)

with open('system_messages.json', 'r') as f:
    system_messages = json.load(f)

class Strategist(Agent):
    def __init__(self, api_key: str):
        super().__init__("Strategist", api_key)

    def generate_strategy(self, target_ip: str, scan_description: str, approved_strategy: Optional[Dict[str, Any]] = None, feedback: Optional[str] = None) -> Dict[str, Any]:
        """Generate a strategy for vulnerability scanning."""
        system_message = system_messages["Strategist"]["generate_strategy"]
        
        user_message = f"Target IP: {target_ip}\nScan Description: {scan_description}\n\nGenerate a comprehensive strategy to complete the vulnerability scan based on the provided IP and description. Provide the strategy in JSON format, along with any relevant explanation or context. Ensure that all commands are complete and can be executed as-is without requiring manual changes. Send it to Manager, your senior, for review. Always include your name and role at the end of each Description. Make sure to introduce yourself first if you haven't, and always write the message directed to Manager."
        
        if approved_strategy:
            user_message += f"\n\nApproved Strategy:\n{json.dumps(approved_strategy, indent=2)}\n\nPlease update the strategy based on the approved strategy, ensuring that all commands are complete and ready to be executed without modifications."
        elif feedback:
            user_message += f"\n\nFeedback from Hassan: {feedback}\n\nPlease generate an updated strategy based on the provided feedback, ensuring that all commands are complete and ready to be executed without modifications. Consider multiple approaches internally, but return only the best single strategy in JSON format. Include a brief explanation of why this strategy was chosen."

        try:
            response = self.generate_response("Manager", user_message, system_message, response_format={"type": "json_object"})
            self.print_agent_output(text=response)
            strategy = json.loads(response)
            
            return strategy
        except Exception as e:
            logger.error(f"Error generating strategy: {str(e)}")
            raise

    def generate_input(self, target_ip: str, scan_description: str, command_output: str, commands: list[str]) -> Dict[str, Any]:
        """Generate input based on command output."""
        system_message = system_messages["Strategist"]["generate_input"]
        
        user_message = f"Target IP: {target_ip}\nScan Description: {scan_description}\nCommand Output:\n{command_output}\nCommands: {json.dumps(commands)}\n\nBased on the command output, determine if input is required. If input is required, provide the next command from the given list of commands in the correct order. If no input is required or the output suggests the current task is complete, provide an empty string. Respond with the input in JSON format."
        
        try:
            strategist_response = self.generate_response("Command_Monitor", user_message, system_message, response_format={"type": "json_object"})
            self.add_to_chat_history("Command_Monitor", "user", user_message)
            self.add_to_chat_history("Command_Monitor", "assistant", strategist_response)
            self.print_agent_output(text=strategist_response)
            return json.loads(strategist_response)
        except Exception as e:
            logger.error(f"Error generating input: {str(e)}")
            raise
