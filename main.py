import json
from typing import List, Dict, Any
from Agents.ammar import Strategist
from Agents.hassan import Manager
from Agents.kofahi import Debugger
from Agents.rakan import Command_Monitor
from Agents.salah import Salah
from Agents.sajed import Reporter
from agent import Agent
import config

def initialize_agents() -> Dict[str, Agent]:
    """Initialize all agent instances."""
    return {
        "strategist": Strategist(config.API_KEY),
        "manager": Manager(config.API_KEY),
        "debugger": Debugger(config.API_KEY),
        "command_monitor": Command_Monitor(config.API_KEY),
        "salah": Salah(config.API_KEY),
        "reporter": Reporter(config.API_KEY)
    }

def generate_and_review_strategy(agents: Dict[str, Agent], findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate and review the strategy."""
    strategy = agents["strategist"].generate_strategy(config.TARGET_IP, config.SCAN_DESCRIPTION)
    findings.append({"strategy": strategy})
    print("Initial Strategy:")
    print(json.dumps(strategy, indent=2))

    reviewed_strategy = agents["manager"].review_strategy(strategy, config.SCAN_DESCRIPTION)
    findings.append({"reviewed_strategy": reviewed_strategy})
    print("Manager's Review:")
    print(json.dumps(reviewed_strategy, indent=2))

    return reviewed_strategy

def execute_commands(agents: Dict[str, Agent], commands: List[str], findings: List[Dict[str, Any]]) -> str:
    """Execute commands and return the output."""
    output = agents["salah"].execute_commands(
        commands, config.TARGET_IP, config.SCAN_DESCRIPTION,
        agents["debugger"], agents["strategist"], agents["command_monitor"]
    )
    print("Command Output:")
    print(output)
    findings.append({"commands": commands, "output": output})
    return output

def review_output(agents: Dict[str, Agent], output: str, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Review the command output."""
    manager_assessment = agents["manager"].review_output(output, config.SCAN_DESCRIPTION)
    findings.append({"manager_assessment": manager_assessment})
    print("Manager's Thoughts on the scan result:")
    print(json.dumps(manager_assessment, indent=2))
    return manager_assessment

def generate_and_review_report(agents: Dict[str, Agent], findings: List[Dict[str, Any]]) -> str:
    """Generate and review the findings report."""
    report = agents["reporter"].generate_report(config.TARGET_IP, config.SCAN_DESCRIPTION, config.FINDINGS_FILE)
    print("Findings Report:")
    print(report)

    while True:
        manager_review = agents["manager"].review_report(report)
        findings.append({"manager_review": manager_review})
        print("Manager's Review:")
        print(json.dumps(manager_review, indent=2))

        if manager_review["Report Approval"]:
            print("Findings report has been approved by Manager.")
            break
        else:
            feedback = manager_review["feedback"]
            print("Manager's feedback:")
            print(feedback)
            report = agents["reporter"].generate_report(config.TARGET_IP, config.SCAN_DESCRIPTION, config.FINDINGS_FILE, feedback=feedback)
            print("Updated Findings Report:")
            print(report)

    return report

def main():
    Agent.increment_run_number()
    current_run = Agent.run_number
    print(f"Starting run {current_run}")

    agents = initialize_agents()
    findings: List[Dict[str, Any]] = []

    strategy = agents["strategist"].generate_strategy(config.TARGET_IP, config.SCAN_DESCRIPTION)
    findings.append({"initial_strategy": strategy})
    print("Initial Strategy:")
    print(json.dumps(strategy, indent=2))

    while True:
        reviewed_strategy = agents["manager"].review_strategy(strategy, config.SCAN_DESCRIPTION)
        findings.append({"reviewed_strategy": reviewed_strategy})
        print("Manager's Review:")
        print(json.dumps(reviewed_strategy, indent=2))

        if reviewed_strategy.get("approved", False):
            commands = strategy.get("strategy", [])
            if not commands:
                print("Error: No commands found in the strategy. Skipping execution.")
                break
            
            output = execute_commands(agents, commands, findings)
            manager_assessment = review_output(agents, output, findings)

            if manager_assessment.get("satisfactory", False):
                print("Scan completed. Client's requirements have been met.")
                break
            else:
                feedback = manager_assessment.get("feedback", "")
                strategy = agents["strategist"].generate_strategy(config.TARGET_IP, config.SCAN_DESCRIPTION, feedback=feedback)
                findings.append({"updated_strategy_based_on_output": strategy})
                print("Updated strategy based on scan output:")
                print(json.dumps(strategy, indent=2))
        else:
            feedback = reviewed_strategy.get("feedback", "")
            print("Manager's feedback:")
            print(feedback)
            strategy = agents["strategist"].generate_strategy(config.TARGET_IP, config.SCAN_DESCRIPTION, feedback=feedback)
            findings.append({"updated_strategy_based_on_review": strategy})
            print("Updated strategy based on Manager's feedback:")
            print(json.dumps(strategy, indent=2))

    with open(config.FINDINGS_FILE, "w") as f:
        json.dump(findings, f, indent=2)

    report = generate_and_review_report(agents, findings)

    with open(config.REPORT_FILE, "w") as f:
        f.write(report)
    print(f"Findings report saved as {config.REPORT_FILE}")

if __name__ == '__main__':
    main()
