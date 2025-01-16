import json
import paramiko
import time
from typing import List, Dict, Any, Tuple
from agent import Agent
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import config
import logging

logger = logging.getLogger(__name__)

with open('system_messages.json', 'r') as f:
    system_messages = json.load(f)

class Salah(Agent):
    def __init__(self, api_key: str):
        super().__init__("Salah", api_key)

    def prepare_command(self, command: str) -> str:
        """Prepare command by properly quoting script arguments"""
        if '--script' in command and '*' in command:
            parts = command.split()
            for i, part in enumerate(parts):
                if part.startswith('--script'):
                    if '=' in part:
                        prefix, script = part.split('=', 1)
                        parts[i] = f'{prefix}="{script}"'
                    else:
                        parts[i+1] = f'"{parts[i+1]}"'
            return ' '.join(parts)
        return command

    def execute_command(self, ssh: paramiko.SSHClient, prepared_command: str) -> Tuple[str, int]:
        command_output = ""
        exit_status = None

        stdin, stdout, stderr = ssh.exec_command(prepared_command, get_pty=True)
        
        while not (stdout.channel.exit_status_ready() and stdout.channel.recv_ready() == False):
            if stdout.channel.recv_ready():
                chunk = stdout.channel.recv(1024).decode('utf-8', errors='replace')
                if chunk:
                    command_output += chunk
                    print(f"{self.name}: {chunk}", end='')
                    
            if stderr.channel.recv_stderr_ready():
                error_chunk = stderr.channel.recv_stderr(1024).decode('utf-8', errors='replace')
                if error_chunk:
                    command_output += error_chunk
                    print(f"{self.name} Error: {error_chunk}", end='')
            
            time.sleep(0.01)
        
        exit_status = stdout.channel.recv_exit_status()

        return command_output, exit_status or -1

    def execute_commands(self, commands: List[str], target_ip: str, scan_description: str, kofahi: Agent, ammar: Agent, rakan: Agent) -> str:
        output = ""
        executed_commands = []
        pending_commands = commands.copy()
        command_index = 0
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(**config.SSH_CONFIG)
            logger.info(f"{self.name}: Connected to SSH server...")

            while command_index < len(commands):
                command = commands[command_index]
                try:
                    prepared_command = self.prepare_command(command)
                    logger.info(f"{self.name}: Executing command: {prepared_command}")
                    
                    command_output, exit_status = self.execute_command(ssh, prepared_command)
                    
                    log_entry = {
                        "command": prepared_command,
                        "raw_output": command_output,
                        "exit_status": exit_status
                    }
                    self.print_agent_output(text=json.dumps(log_entry))
                    
                    output += command_output
                    executed_commands.append(command)
                    pending_commands = commands[command_index+1:]

                    rakan_response = rakan.monitor_output(target_ip, scan_description, output, executed_commands, pending_commands)
                    
                    if rakan_response["input_needed"]:
                        ammar_response = ammar.generate_input(target_ip, scan_description, output, pending_commands)
                        input_command = ammar_response["input"]

                        if input_command:
                            command_index += 1
                            prepared_input_command = self.prepare_command(input_command)
                            logger.info(f"{self.name}: Executing input command: {prepared_input_command}")
                            
                            input_output, input_exit_status = self.execute_command(ssh, prepared_input_command)
                            
                            input_log_entry = {
                                "command": prepared_input_command,
                                "raw_output": input_output,
                                "type": "input_command",
                                "exit_status": input_exit_status
                            }
                            self.print_agent_output(text=json.dumps(input_log_entry))
                            
                            output += input_output
                        else:
                            command_index += 1
                            break

                    command_index += 1

                except Exception as e:
                    error_message = f"Error executing command: {command}\nError message: {str(e)}\n\n"
                    logger.error(f"{self.name}: {error_message}")
                    
                    error_log_entry = {
                        "command": command,
                        "error": str(e),
                        "partial_output": command_output if 'command_output' in locals() else ""
                    }
                    self.print_agent_output(text=json.dumps(error_log_entry))
                    
                    context = f"Target IP: {target_ip}\nScan Description: {scan_description}\nCommand Output:\n{output}"
                    kofahi_response = kofahi.handle_error(error_message, context)
                    self.add_to_chat_history("Kofahi", "user", f"Error Message:\n{error_message}\n\nContext:\n{context}")
                    self.add_to_chat_history("Kofahi", "assistant", json.dumps(kofahi_response))
                    
                    if "fix" in kofahi_response:
                        fix_commands = kofahi_response["fix"]
                        logger.info(f"{self.name}: Executing fix commands:")
                        
                        for fix_command in fix_commands:
                            logger.info(f"{self.name}: {fix_command}")
                            try:
                                prepared_fix_command = self.prepare_command(fix_command)
                                
                                fix_output, fix_exit_status = self.execute_command(ssh, prepared_fix_command)
                                
                                fix_log_entry = {
                                    "command": prepared_fix_command,
                                    "raw_output": fix_output,
                                    "type": "fix_command",
                                    "exit_status": fix_exit_status
                                }
                                self.print_agent_output(text=json.dumps(fix_log_entry))
                                
                                output += fix_output
                            except Exception as e:
                                logger.error(f"{self.name}: Error executing fix command: {fix_command}")
                                logger.error(f"{self.name}: Error message: {str(e)}")
                                fix_error_entry = {
                                    "command": fix_command,
                                    "error": str(e),
                                    "type": "fix_command"
                                }
                                self.print_agent_output(text=json.dumps(fix_error_entry))

                    output += error_message
                    command_index += 1

        finally:
            ssh.close()
            logger.info(f"{self.name}: SSH connection closed.")

        return output
