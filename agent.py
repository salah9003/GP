from openai import OpenAI
from colorama import init, Fore, Style
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Agent:
    run_number = 0
    global_order = 0

    @classmethod
    def increment_run_number(cls) -> None:
        """Increment the run number and reset the global order."""
        cls.run_number = cls.get_next_run_number()
        cls.global_order = 0

    @classmethod
    def get_next_run_number(cls) -> int:
        """Get the next run number based on existing log directories."""
        if not os.path.exists(config.LOG_DIR):
            return 1
        existing_runs = [d for d in os.listdir(config.LOG_DIR) if d.startswith("run")]
        if not existing_runs:
            return 1
        return max(int(run.replace("run", "")) for run in existing_runs) + 1

    def __init__(self, name: str, api_key: str):
        """Initialize an Agent instance."""
        self.name = name
        self.client = OpenAI(api_key=api_key)
        self.chat_histories: Dict[str, List[Dict[str, str]]] = {}
        self.request_counter = 0

    def get_chat_history(self, recipient: str) -> List[Dict[str, str]]:
        """Get or initialize chat history for a recipient."""
        if recipient not in self.chat_histories:
            self.chat_histories[recipient] = [
                {"role": "system", "content": f"You are {self.name}, an AI agent. You are communicating with {recipient}."},
            ]
        return self.chat_histories[recipient]

    def add_to_chat_history(self, recipient: str, role: str, content: str) -> None:
        """Add a message to the chat history."""
        chat_history = self.get_chat_history(recipient)
        chat_history.append({"role": role, "content": content})

    def print_agent_output(self, text: Optional[str] = None) -> None:
        """Print agent output with color coding."""
        color = {
            "Strategist": Fore.BLUE,
            "Manager": Fore.GREEN,
            "Debugger": Fore.LIGHTGREEN_EX,
            "Command_Monitor": Fore.MAGENTA,
            "Salah": Fore.YELLOW,
            "Reporter": Fore.CYAN,
            "Output": Fore.RED
        }.get(self.name, Fore.RESET)
        
        print(f"{color}{self.name}:{Style.RESET_ALL}")
        
        if text:
            try:
                data = json.loads(text)
                for key, value in data.items():
                    formatted_key = key.capitalize()
                    if isinstance(value, bool):
                        formatted_value = "Yes" if value else "No"
                    elif isinstance(value, list):
                        formatted_value = ", ".join(value)
                    else:
                        formatted_value = value
                    print(f"{color}{formatted_key}: {formatted_value}{Style.RESET_ALL}")
            except json.JSONDecodeError:
                print(f"{color}Text: {text}{Style.RESET_ALL}")
        
        print()

    def generate_chat_messages(self, recipient: str, system_message: str, user_message: str) -> List[Dict[str, str]]:
        """Generate chat messages for OpenAI API."""
        chat_history = self.get_chat_history(recipient)
        return [
            {"role": "system", "content": system_message},
            *chat_history[-20:],
            {"role": "user", "content": user_message}
        ]

    def generate_response(self, recipient: str, user_message: str, system_message: str, model: str = config.OPENAI_MODEL, response_format: Optional[Dict[str, str]] = None) -> str:
        """Generate a response using the OpenAI API."""
        self.request_counter += 1
        chat_history = self.get_chat_history(recipient)
        self.add_to_chat_history(recipient, "user", user_message)
        messages = chat_history.copy()
        messages[0] = {"role": "system", "content": system_message}
        
        try:
            if response_format:
                response = self.client.chat.completions.create(
                    model=model,
                    response_format=response_format,
                    messages=messages
                )
            else:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages
                )
            assistant_response = response.choices[0].message.content
            self.add_to_chat_history(recipient, "assistant", assistant_response)
            self.log_response(messages, assistant_response)
            return assistant_response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

    def log_response(self, messages: List[Dict[str, str]], assistant_response: str) -> None:
        """Log the response to a JSON file."""
        log_dir = os.path.join(config.LOG_DIR, f"run{self.run_number}")
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, f"{self.name}.json")

        Agent.global_order += 1
        log_entry = {
            f"Request {self.request_counter}": {
                "Order": Agent.global_order,
                "Context": messages,
                "Response": assistant_response
            }
        }

        try:
            with open(log_file_path, "r+") as log_file:
                existing_data = json.load(log_file)
                existing_data.update(log_entry)
                log_file.seek(0)
                json.dump(existing_data, log_file, indent=2)
                log_file.truncate()
        except (FileNotFoundError, json.JSONDecodeError):
            with open(log_file_path, "w") as log_file:
                json.dump(log_entry, log_file, indent=2)
        except Exception as e:
            logger.error(f"Error logging response: {str(e)}")
