import json
from typing import Dict, Any
from agent import Agent
import config
import logging

logger = logging.getLogger(__name__)

with open('system_messages.json', 'r') as f:
    system_messages = json.load(f)

class Manager(Agent):
    def __init__(self, api_key: str):
        super().__init__("Manager", api_key)

    def review_strategy(self, strategy: Dict[str, Any], scan_description: str) -> Dict[str, Any]:
        """Review the proposed strategy and provide feedback."""
        system_message = system_messages["Manager"]["review_strategy"]
        
        user_message = f"Client's request: {scan_description}\nHere is the proposed Strategy:\n{json.dumps(strategy, indent=2)}\n\nPlease review the proposed strategy and provide your feedback. Ensure that all commands are complete and can be executed without manual modifications. Indicate if the strategy is approved and suggest any necessary adjustments. Ensure that Strategist proposes a strategy that is well thought out and implements the steps of a penetration test in a logical order."
        
        try:
            reviewed_strategy = self.generate_response("Strategist", user_message, system_message, response_format={"type": "json_object"})
            self.print_agent_output(text=reviewed_strategy)
            return json.loads(reviewed_strategy)
        except Exception as e:
            logger.error(f"Error reviewing strategy: {str(e)}")
            raise

    def review_output(self, output: str, scan_description: str) -> Dict[str, Any]:
        """Review the command output and assess if it meets the client's requirements."""
        system_message = system_messages["Manager"]["review_output"]
        
        user_message = f"Client's request: {scan_description}\nCommand Output:\n{output}\n\nPlease review the command output and determine if it meets the client's requirements based on the initial scan description. Indicate if the output is satisfactory or if additional commands are needed. If there are no more commands to be executed, set the 'satisfactory' key to true. Note that the results of the scan must meet the requirement of the client; missing any vulnerabilities can be very damaging to our firm's reputation. Provide your assessment in JSON format, along with any necessary feedback and suggestions."
        
        try:
            manager_assessment = self.generate_response("Strategist", user_message, system_message, response_format={"type": "json_object"})
            self.print_agent_output(text=manager_assessment)
            return json.loads(manager_assessment)
        except Exception as e:
            logger.error(f"Error reviewing output: {str(e)}")
            raise

    def review_report(self, report: str) -> Dict[str, Any]:
        """Review the findings report and provide feedback."""
        system_message = system_messages["Manager"]["review_report"]
        
        user_message = f"Findings Report:\n{report}\n\nPlease review the findings report and provide your feedback. Indicate if the report is approved by setting the 'Report Approval' key to True or False. If improvements are needed, provide specific suggestions and recommendations in the 'feedback' key. Respond in JSON format."
        
        try:
            manager_review = self.generate_response("Reporter", user_message, system_message, response_format={"type": "json_object"})
            self.print_agent_output(text=manager_review)
            return json.loads(manager_review)
        except Exception as e:
            logger.error(f"Error reviewing report: {str(e)}")
            raise
