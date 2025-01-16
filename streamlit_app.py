import streamlit as st
import json
import os
import ast
import subprocess
import signal

# Load and save system messages
def load_system_messages():
    with open('system_messages.json', 'r') as file:
        return json.load(file)

def save_system_messages(messages):
    with open('system_messages.json', 'w') as file:
        json.dump(messages, file, indent=2)

# Custom CSS for bordered box and red button
st.markdown("""
<style>
.bordered-box {
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 10px;
    margin-bottom: 10px;
}
.stButton > button {
    width: 100%;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
    background-color: #ff4b4b;
    color: white;
}
</style>
""", unsafe_allow_html=True)

def load_json_files(run_path):
    json_files = [f for f in os.listdir(run_path) if f.endswith('.json')]
    data = {}
    for file in json_files:
        agent_name = file.split('.')[0]
        with open(os.path.join(run_path, file), 'r') as f:
            data[agent_name] = json.load(f)
    return data

def extract_messages(data):
    messages = []
    for agent, content in data.items():
        for request, details in content.items():
            order = details.get('Order', 0)
            context = details.get('Context', [])
            response = details.get('Response', '')
            messages.append({
                'order': order,
                'agent': agent,
                'request': request,
                'context': context,
                'response': response
            })
    return sorted(messages, key=lambda x: x['order'])

def parse_response(response):
    try:
        parsed = json.loads(response)
        if isinstance(parsed, dict):
            return parsed
        elif isinstance(parsed, list):
            return parsed
        return response
    except json.JSONDecodeError:
        return response

def display_message(msg):
    st.markdown(f"<div class='bordered-box'><h3>{msg['agent']}: {msg['request']}</h3>", unsafe_allow_html=True)
    
    if msg['context']:
        with st.expander("Show Context"):
            for item in msg['context']:
                st.markdown(f"<div class='bordered-box'><strong>{item['role']}:</strong> {item['content']}</div>", unsafe_allow_html=True)
    
    parsed_response = parse_response(msg['response'])
    
    if isinstance(parsed_response, dict):
        for key, value in parsed_response.items():
            st.markdown(f"<h4>{key}</h4>", unsafe_allow_html=True)
            if isinstance(value, (dict, list)):
                st.json(value)
            else:
                st.markdown(f"<div class='bordered-box'>{value}</div>", unsafe_allow_html=True)
    elif isinstance(parsed_response, list):
        st.json(parsed_response)
    else:
        st.markdown(f"<div class='bordered-box'><strong>Response</strong><br><br>{parsed_response}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")

def load_config():
    with open('config.py', 'r') as file:
        content = file.read()
    return content

def save_config(content):
    with open('config.py', 'w') as file:
        file.write(content)

def parse_config(content):
    tree = ast.parse(content)
    config = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    key = target.id
                    if isinstance(node.value, ast.Str):
                        value = node.value.s
                    elif isinstance(node.value, ast.Num):
                        value = node.value.n
                    elif isinstance(node.value, ast.NameConstant):
                        value = node.value.value
                    elif isinstance(node.value, ast.Dict):
                        value = {k.s: v.s for k, v in zip(node.value.keys, node.value.values) if isinstance(k, ast.Str) and isinstance(v, ast.Str)}
                    elif isinstance(node.value, (ast.BoolOp, ast.Compare, ast.Call)):
                        # For complex expressions, we'll keep them as strings
                        value = ast.unparse(node.value)
                    else:
                        value = ast.unparse(node.value)
                    config[key] = value
    return config

def config_ui():
    st.header("Configuration")
    content = load_config()
    config = parse_config(content)
    
    updated_config = {}
    for key, value in config.items():
        if key != 'API_KEY':  # Skip API_KEY
            if isinstance(value, dict):
                st.subheader(key)
                updated_dict = {}
                for k, v in value.items():
                    updated_dict[k] = st.text_input(f"{key}.{k}", v)
                updated_config[key] = updated_dict
            else:
                updated_config[key] = st.text_input(key, value)
    
    if st.button("Update Configuration"):
        new_content = "import os\n\n"
        for key, value in updated_config.items():
            if isinstance(value, dict):
                new_content += f"{key} = {{\n"
                for k, v in value.items():
                    new_content += f"    '{k}': '{v}',\n"
                new_content += "}\n\n"
            elif key in ['OPENAI_MODEL', 'TARGET_IP', 'SCAN_DESCRIPTION', 'LOG_DIR', 'FINDINGS_FILE', 'REPORT_FILE']:
                new_content += f"{key} = '{value}'\n"
            else:
                new_content += f"{key} = {value}\n"
        
        # Add API_KEY back to the configuration without modification
        new_content += "API_KEY = os.getenv('OPENAI_API_KEY') or ''\n"
        
        save_config(new_content)
        st.success("Configuration updated successfully! Please refresh the page to see the changes.")

def parse_config(content):
    tree = ast.parse(content)
    config = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    key = target.id
                    if isinstance(node.value, (ast.Str, ast.Constant)):
                        value = node.value.value if isinstance(node.value, ast.Constant) else node.value.s
                    elif isinstance(node.value, ast.Num):
                        value = node.value.n
                    elif isinstance(node.value, ast.Dict):
                        value = {k.value: v.value for k, v in zip(node.value.keys, node.value.values) if isinstance(k, (ast.Str, ast.Constant)) and isinstance(v, (ast.Str, ast.Constant))}
                    elif isinstance(node.value, (ast.BoolOp, ast.Compare, ast.Call)):
                        value = ast.unparse(node.value)
                    else:
                        value = ast.unparse(node.value)
                    config[key] = value
    return config

def parse_config(content):
    tree = ast.parse(content)
    config = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    key = target.id
                    if isinstance(node.value, (ast.Str, ast.Constant)):
                        value = node.value.value if isinstance(node.value, ast.Constant) else node.value.s
                    elif isinstance(node.value, ast.Num):
                        value = node.value.n
                    elif isinstance(node.value, ast.Dict):
                        value = {k.value: v.value for k, v in zip(node.value.keys, node.value.values) if isinstance(k, (ast.Str, ast.Constant)) and isinstance(v, (ast.Str, ast.Constant))}
                    elif isinstance(node.value, (ast.BoolOp, ast.Compare, ast.Call)):
                        value = ast.unparse(node.value)
                    else:
                        value = ast.unparse(node.value)
                    config[key] = value
    return config

def run_main_script():
    if not st.session_state['running']:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        process = subprocess.Popen(['python', 'main.py'], cwd=current_dir)
        st.session_state['process'] = process
        st.session_state['running'] = True

def stop_main_script():
    if st.session_state['running'] and 'process' in st.session_state:
        st.session_state['process'].send_signal(signal.SIGTERM)
        st.session_state['process'] = None
        st.session_state['running'] = False

def agent_config_ui():
    st.header("Agent Configuration")
    system_messages = load_system_messages()
    
    updated_messages = {}
    for agent, messages in system_messages.items():
        st.subheader(agent)
        for key, value in messages.items():
            updated_messages.setdefault(agent, {})[key] = st.text_area(f"{agent} - {key}", value, height=150)
    
    if st.button("Update Agent Configuration"):
        save_system_messages(updated_messages)
        st.success("Agent configuration updated successfully!")

def main():
    st.title("Agent Conversation Viewer")

    # Initialize session state
    if 'running' not in st.session_state:
        st.session_state['running'] = False

    # Sidebar for navigation
    page = st.sidebar.radio("Navigation", ["Conversation", "Configuration", "Agent Configuration"])

    if page == "Conversation":
        # Sidebar for run selection
        st.sidebar.header("Select Run")
        log_dir = "context_logs"
        run_folders = [f for f in os.listdir(log_dir) if os.path.isdir(os.path.join(log_dir, f))]
        selected_run = st.sidebar.selectbox("Select Run", run_folders, key="run_selector")
        
        # Add Start and Stop buttons in the sidebar
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.sidebar.button("Start", disabled=st.session_state['running'], key="start_button"):
                run_main_script()
        with col2:
            if st.sidebar.button("Stop", disabled=not st.session_state['running'], key="stop_button", use_container_width=True):
                stop_main_script()

        # Display running status in the sidebar
        status = "Script is running..." if st.session_state['running'] else "Script is not running."
        st.sidebar.write(status)
        
        if selected_run:
            run_path = os.path.join(log_dir, selected_run)
            data = load_json_files(run_path)
            messages = extract_messages(data)

            st.header(f"Conversation from Run: {selected_run}")
            for msg in messages:
                display_message(msg)

    elif page == "Configuration":
        config_ui()
    else:
        agent_config_ui()

if __name__ == "__main__":
    main()
