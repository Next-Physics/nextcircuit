import os
import sqlite3
import subprocess
import signal
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)

DB_PATH = 'db/main.db'
RESULTS_DIR = 'results'

# Global reference to the running process
running_process = None

def get_conversations():
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT chain_title, history, chain_last_modified FROM chains ORDER BY chain_last_modified DESC")
    rows = cursor.fetchall()
    conn.close()
    conversations = []
    for r in rows:
        conversations.append({
            'title': r[0],
            'history': r[1],
            'last_modified': r[2]
        })
    return conversations

@app.route('/')
def index():
    conversations = get_conversations()
    return render_template('index.html', conversations=conversations)

@app.route('/get_conversation', methods=['POST'])
def get_conversation():
    title = request.form.get('title', '')
    if not os.path.exists(DB_PATH):
        return jsonify({'history': ''})
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT history FROM chains WHERE chain_title = ?", (title,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({'history': row[0]})
    return jsonify({'history': ''})

@app.route('/run_agent')
def run_agent():
    user_query = request.args.get('user_query', '')
    ollama_ip = request.args.get('ollama_ip', 'localhost')
    ollama_port = request.args.get('ollama_port', '11411')

    global running_process

    # Set up a separate process group so we can kill all children together.
    # For UNIX:
    preexec = None
    creationflags = 0

    if os.name == 'posix':
        # On UNIX, setsid creates a new process group.
        preexec = os.setsid
    elif os.name == 'nt':
        # On Windows, CREATE_NEW_PROCESS_GROUP creates a new process group.
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    running_process = subprocess.Popen(
        ['python', 'main.py', '--query', user_query, '--ip', ollama_ip, '--port', ollama_port],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        preexec_fn=preexec,
        creationflags=creationflags
    )

    def stream_output():
        for line in running_process.stdout:
            yield f"data: {line.strip()}\n\n"
        running_process.wait()
        yield "data: [DONE]\n\n"
    
    return Response(stream_output(), mimetype='text/event-stream')

@app.route('/stop_agent', methods=['POST'])
def stop_agent():
    global running_process
    if running_process and running_process.poll() is None:
        # Process is still running, kill it
        if os.name == 'posix':
            # UNIX
            os.killpg(os.getpgid(running_process.pid), signal.SIGTERM)
        else:
            # Windows
            running_process.terminate()
        running_process = None
        return jsonify({"status": "stopped"})
    return jsonify({"status": "no_active_process"})

@app.route('/get_results', methods=['GET'])
def get_results():
    if not os.path.exists(RESULTS_DIR):
        return jsonify([])
    files = [f for f in os.listdir(RESULTS_DIR) if os.path.isfile(os.path.join(RESULTS_DIR, f))]
    return jsonify(files)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
