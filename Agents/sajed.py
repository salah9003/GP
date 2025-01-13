import json
from typing import Optional
from agent import Agent
import config
import logging

logger = logging.getLogger(__name__)

with open('system_messages.json', 'r') as f:
    system_messages = json.load(f)

class Reporter(Agent):
    def __init__(self, api_key: str):
        super().__init__("Reporter", api_key)

    def generate_report(self, target_ip: str, scan_description: str, findings_file: str, feedback: Optional[str] = None) -> str:
        """Generate a comprehensive findings report based on the vulnerability scan findings."""
        try:
            with open(findings_file, "r") as f:
                findings = json.load(f)
        except Exception as e:
            logger.error(f"Error reading findings file: {str(e)}")
            raise

        system_message = system_messages["Reporter"]["generate_report"]
        
        user_message = f"Target IP: {target_ip}\nScan Description: {scan_description}\nFindings File: {json.dumps(findings, indent=2)}\n\nPlease generate a comprehensive findings report based on the provided vulnerability scan findings. Use Markdown formatting for the report."
        
        if feedback:
            user_message += f"\n\nFeedback from Manager: {feedback}\n\nPlease update the findings report based on the provided feedback, ensuring that the report is comprehensive, professional, and addresses all the necessary aspects."

        try:
            report = self.generate_response("Manager", user_message, system_message)
            self.add_to_chat_history("Manager", "user", user_message)
            self.add_to_chat_history("Manager", "assistant", report)
            self.print_agent_output(text=report)
            return report.strip()
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise
