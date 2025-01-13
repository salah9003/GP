import os

API_KEY = os.getenv("OPENAI_API_KEY") or 'YOUR_API_KEY'
TARGET_IP = "192.168.1.139"
SCAN_DESCRIPTION = "check for vulnerabilities on the target machine and attempt to exploit"

SSH_CONFIG = {
    'hostname': '192.168.1.113',
    'username': 'root',
    'password': 'kali'
}

OPENAI_MODEL = "gpt-4o"

LOG_DIR = "context_logs"
FINDINGS_FILE = "findings.json"
REPORT_FILE = "findings_report.md"
