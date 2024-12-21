import os
import sqlite3
import subprocess
import signal
import ast
import json
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)

DB_PATH = 'db/main.db'
RESULTS_DIR = 'results'
UPLOAD_DIR = 'uploaded_files'
os.makedirs(UPLOAD_DIR, exist_ok=True)

running_process = None

def get_conversations():
    """Fetches existing conversations from the DB."""
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, chain_title, history, chain_last_modified FROM chains ORDER BY chain_last_modified DESC")
    rows = cursor.fetchall()
    conn.close()
    conversations = []
    for r in rows:
        conversations.append({
            'id': r[0],
            'title': r[1],
            'history': r[2],
            'last_modified': r[3]
        })
    return conversations

@app.route('/')
def index():
    """Loads the main page with the conversation list."""
    conversations = get_conversations()
    return render_template('index.html', conversations=conversations)

@app.route('/get_conversation', methods=['POST'])
def get_conversation():
    """Returns the conversation history for a given conversation ID."""
    chain_id = request.form.get('id', '')
    if not os.path.exists(DB_PATH):
        return jsonify({'history': ''})

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT history FROM chains WHERE id = ?", (chain_id,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0]:
        return jsonify({'history': row[0]})
    return jsonify({'history': ''})

@app.route('/delete_conversation', methods=['POST'])
def delete_conversation():
    """Deletes a conversation from the DB."""
    chain_id = request.form.get('id', '')
    if not chain_id:
        return jsonify({'status': 'error', 'message': 'No id provided'})
    if not os.path.exists(DB_PATH):
        return jsonify({'status': 'error', 'message': 'Database not found'})

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chains WHERE id = ?", (chain_id,))
    conn.commit()
    conn.close()

    return jsonify({'status': 'deleted'})

@app.route('/run_agent')
def run_agent():
    """Starts main.py as a subprocess and streams stdout via SSE."""
    user_query = request.args.get('user_query', '')
    ollama_ip = request.args.get('ollama_ip', 'localhost')
    ollama_port = request.args.get('ollama_port', '11411')
    attached_files_json = request.args.get('attached_files', '[]')

    global running_process

    preexec = None
    creationflags = 0

    if os.name == 'posix':
        preexec = os.setsid
    elif os.name == 'nt':
        import subprocess
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    # Use python -u for unbuffered stdout, so prints stream immediately
    running_process = subprocess.Popen(
        ['python', '-u', 'main.py',
         '--query', user_query,
         '--ip', ollama_ip,
         '--port', ollama_port,
         '--attached_files', attached_files_json],
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
    """Stops the currently running agent process."""
    global running_process
    if running_process and running_process.poll() is None:
        if os.name == 'posix':
            os.killpg(os.getpgid(running_process.pid), signal.SIGTERM)
        else:
            running_process.terminate()
        running_process = None
        return jsonify({"status": "stopped"})
    return jsonify({"status": "no_active_process"})

@app.route('/get_results', methods=['GET'])
def get_results():
    """Lists all files in the results/ directory."""
    if not os.path.exists(RESULTS_DIR):
        return jsonify([])
    files = [f for f in os.listdir(RESULTS_DIR) if os.path.isfile(os.path.join(RESULTS_DIR, f))]
    return jsonify(files)

@app.route('/upload_file', methods=['POST'])
def upload_file():
    """
    Endpoint for uploading a local file to the server.
    We save it in uploaded_files/ and return its absolute path.
    """
    file = request.files.get('file')
    if not file:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400

    filename = file.filename
    server_path = os.path.join(UPLOAD_DIR, filename)
    file.save(server_path)
    abs_path = os.path.abspath(server_path)
    return jsonify({'status': 'ok', 'path': abs_path})

@app.route('/latest_conversations', methods=['GET'])
def latest_conversations():
    """Returns the entire conversation list as JSON to detect newly added chains."""
    convs = get_conversations()
    return jsonify(convs)

@app.route('/get_plan', methods=['GET'])
def get_plan():
    """
    Returns the plan stored in 'chains.plan' for a given chain_id.
    If the plan is stored in a Python-esque format, we try ast.literal_eval -> JSON.
    """
    chain_id = request.args.get('chain_id', '')
    if not chain_id:
        return jsonify({'status': 'error', 'message': 'No chain_id provided'}), 400
    if not os.path.exists(DB_PATH):
        return jsonify({'status': 'error', 'message': 'Database not found'}), 404

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT plan FROM chains WHERE id = ?", (chain_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        # No plan stored
        return jsonify({'plan': None})

    plan_data_raw = row[0]  # This could be JSON or Pythonic string

    # Try to parse:
    plan_dict = None
    if isinstance(plan_data_raw, (str, bytes)):
        # It's a string that might be JSON or a Python dict string
        try:
            # First try JSON
            plan_dict = json.loads(plan_data_raw)
        except (json.JSONDecodeError, TypeError):
            # If not valid JSON, try ast.literal_eval
            try:
                maybe_py = ast.literal_eval(plan_data_raw)
                if isinstance(maybe_py, dict):
                    plan_dict = maybe_py
                else:
                    # If it's not a dict, fallback
                    plan_dict = None
            except:
                plan_dict = None
    else:
        # It's not even a string?
        plan_dict = None

    return jsonify({'plan': plan_dict})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
