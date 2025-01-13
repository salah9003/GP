import asyncio
import websockets
import json
import os
import time
import subprocess
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

PORT = 8000
WS_PORT = 8001
LAST_UPDATE_TIME = time.time()
CLIENTS = set()
MAIN_PROCESS = None
SYSTEM_MESSAGES_FILE = 'system_messages.json'

class LogViewerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_response(HTTPStatus.OK) 
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('log_viewer.html', 'rb') as file:
                self.wfile.write(file.read())
        elif parsed_path.path == '/api/runs':
            self.send_json(get_runs())
        elif parsed_path.path == '/api/log':
            query = parse_qs(parsed_path.query)
            run = query.get('run', [''])[0]
            self.send_json(get_log(run))
        elif parsed_path.path == '/api/latest_run':
            self.send_json({'latest_run': get_latest_run()})
        elif parsed_path.path == '/api/json_content':
            query = parse_qs(parsed_path.query)
            run = query.get('run', [''])[0]
            agent = query.get('agent', [''])[0]
            order = query.get('order', [''])[0]
            self.send_json(get_json_content(run, agent, order))
        elif parsed_path.path == '/api/system_messages':
            self.send_json(get_system_messages())
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/start':
            self.send_json(start_main_script())
        elif parsed_path.path == '/api/stop':
            self.send_json(stop_main_script())
        elif parsed_path.path == '/api/update_system_message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            self.send_json(update_system_message(data['agent'], data['key'], data['content']))
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def send_json(self, data):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def start_main_script():
    global MAIN_PROCESS
    if MAIN_PROCESS is None or MAIN_PROCESS.poll() is not None:
        try:
            MAIN_PROCESS = subprocess.Popen(['python', 'main.py'])
            return {'status': 'success', 'message': 'Script started successfully'}
        except Exception as e:
            return {'status': 'error', 'message': f'Failed to start script: {str(e)}'}
    else:
        return {'status': 'error', 'message': 'Script is already running'}

def stop_main_script():
    global MAIN_PROCESS
    if MAIN_PROCESS is not None and MAIN_PROCESS.poll() is None:
        try:
            MAIN_PROCESS.terminate()
            MAIN_PROCESS.wait(timeout=5)
            MAIN_PROCESS = None
            return {'status': 'success', 'message': 'Script stopped successfully'}
        except subprocess.TimeoutExpired:
            MAIN_PROCESS.kill()
            MAIN_PROCESS = None
            return {'status': 'success', 'message': 'Script forcefully terminated'}
        except Exception as e:
            return {'status': 'error', 'message': f'Failed to stop script: {str(e)}'}
    else:
        return {'status': 'error', 'message': 'No script is currently running'}

def get_runs():
    runs = [d for d in os.listdir('context_logs') if d.startswith('run')]
    runs.sort(key=lambda x: int(x[3:]), reverse=True)  # Sort runs in descending order
    return runs

def get_latest_run():
    runs = get_runs()
    return runs[0] if runs else None

def get_log(run):
    global LAST_UPDATE_TIME
    run_dir = os.path.join('context_logs', run)
    all_logs = {}
    for agent_file in os.listdir(run_dir):
        if agent_file.endswith('.json'):
            agent_name = agent_file.split('.')[0]
            file_path = os.path.join(run_dir, agent_file)
            file_mtime = os.path.getmtime(file_path)
            if file_mtime > LAST_UPDATE_TIME:
                LAST_UPDATE_TIME = file_mtime
            with open(file_path, 'r') as file:
                agent_log = json.load(file)
                for key, value in agent_log.items():
                    order = value.get('Order', int(key.split()[1]))
                    all_logs[order] = {
                        'agent': agent_name,
                        'response': value['Response'],
                        'order': order
                    }
            # Map old agent names to new ones
            agent_name_mapping = {
                'ammar': 'Strategist',
                'hassan': 'Manager',
                'kofahi': 'Debugger',
                'rakan': 'Command_Monitor',
                'sajed': 'Reporter'
            }
            all_logs[order]['agent'] = agent_name_mapping.get(agent_name.lower(), agent_name)
    return sorted(all_logs.values(), key=lambda x: x['order'])

def get_json_content(run, agent, order):
    run_dir = os.path.join('context_logs', run)
    file_path = os.path.join(run_dir, f"{agent}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            agent_log = json.load(file)
            for key, value in agent_log.items():
                if value.get('Order', int(key.split()[1])) == int(order):
                    return value
    return {"error": "Content not found"}

async def websocket_handler(websocket):
    CLIENTS.add(websocket)
    try:
        await websocket.send(json.dumps({"type": "connection", "status": "connected"}))
        async for message in websocket:
            print(f"Received message: {message}")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"WebSocket connection closed: {e}")
    except Exception as e:
        print(f"Error in websocket handler: {e}")
    finally:
        CLIENTS.remove(websocket)

async def check_for_updates():
    global LAST_UPDATE_TIME
    while True:
        try:
            await asyncio.sleep(1)
            current_time = time.time()
            if current_time > LAST_UPDATE_TIME:
                LAST_UPDATE_TIME = current_time
                latest_run = get_latest_run()
                if latest_run:
                    update_message = json.dumps({
                        'type': 'update',
                        'latest_run': latest_run,
                        'log': get_log(latest_run)
                    })
                    await broadcast(update_message)
        except Exception as e:
            print(f"Error in check_for_updates: {e}")

async def broadcast(message):
    for client in CLIENTS.copy():
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosed:
            CLIENTS.remove(client)

async def main():
    http_server = HTTPServer(('', PORT), LogViewerHandler)
    print(f"HTTP server serving at port {PORT}")
    
    try:
        ws_server = await websockets.serve(websocket_handler, "localhost", WS_PORT)
        print(f"WebSocket server serving at port {WS_PORT}")
        
        asyncio.create_task(check_for_updates())
        
        await asyncio.gather(
            asyncio.to_thread(http_server.serve_forever),
            ws_server.wait_closed()
        )
    except Exception as e:
        print(f"Error starting WebSocket server: {e}")

def get_system_messages():
    try:
        with open(SYSTEM_MESSAGES_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def update_system_message(agent, key, content):
    system_messages = get_system_messages()
    if agent not in system_messages:
        system_messages[agent] = {}
    system_messages[agent][key] = content
    with open(SYSTEM_MESSAGES_FILE, 'w') as file:
        json.dump(system_messages, file, indent=2)
    return {'status': 'success', 'message': 'System message updated successfully'}

if __name__ == "__main__":
    asyncio.run(main())
