import os

TARGET_IP = '172.20.10.4'
SCAN_DESCRIPTION = 'Check if there are any vulnerabilities for SMB protocol'
SSH_CONFIG = {
    'hostname': '172.20.10.2',
    'username': 'root',
    'password': 'kali',
}

OPENAI_MODEL = 'gpt-4o-mini-2024-07-18'
LOG_DIR = 'context_logs'
FINDINGS_FILE = 'findings.json'
REPORT_FILE = 'findings_report.md'
API_KEY = os.getenv('OPENAI_API_KEY') or ''
