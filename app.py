import os
import sqlite3
import subprocess
import signal
import ast
import json
import datetime
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)

DB_PATH = 'db/main.db'
UPLOAD_DIR = 'uploaded_files'
os.makedirs(UPLOAD_DIR, exist_ok=True)

running_process = None

def get_conversations():
    """Fetches existing conversations from the DB."""
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # We assume there's a user_query and plan columns in the chains table
    cursor.execute("""
        SELECT id, chain_title, history, chain_last_modified, user_query
          FROM chains
         ORDER BY chain_last_modified DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    conversations = []
    for r in rows:
        conversations.append({
            'id': r[0],
            'title': r[1],
            'history': r[2],
            'last_modified': r[3],
            'user_query': r[4] or ''
        })
    return conversations

@app.route('/')
def index():
    """Loads the main page with the conversation list."""
    conversations = get_conversations()
    return render_template('index.html', conversations=conversations)

@app.route('/get_conversation', methods=['POST'])
def get_conversation():
    """Returns the conversation history + user_query for a given conversation ID."""
    chain_id = request.form.get('id', '')
    if not os.path.exists(DB_PATH):
        return jsonify({'history': '', 'user_query': ''})

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT history, user_query
          FROM chains
         WHERE id = ?
    """, (chain_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({'history': row[0] or '', 'user_query': row[1] or ''})
    return jsonify({'history': '', 'user_query': ''})

@app.route('/delete_conversation', methods=['POST'])
def delete_conversation():
    """Deletes a conversation from the DB, plus any associated results folder."""
    chain_id = request.form.get('id', '')
    if not chain_id:
        return jsonify({'status': 'error', 'message': 'No id provided'})
    if not os.path.exists(DB_PATH):
        return jsonify({'status': 'error', 'message': 'Database not found'})

    # Remove the folder results/<chain_id> if it exists.
    results_dir = os.path.join('results', chain_id)
    if os.path.exists(results_dir) and os.path.isdir(results_dir):
        import shutil
        shutil.rmtree(results_dir, ignore_errors=True)

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
    # We'll also pass chain_id or "None"
    chain_id = request.args.get('chain_id', 'None')

    global running_process

    preexec = None
    creationflags = 0

    if os.name == 'posix':
        preexec = os.setsid
    elif os.name == 'nt':
        import subprocess
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    # Use python -u for unbuffered stdout, so prints stream immediately
    cmd = [
        'python', '-u', 'main.py',
        '--query', user_query,
        '--ip', ollama_ip,
        '--port', ollama_port,
        '--attached_files', attached_files_json,
        '--chain_id', chain_id
    ]

    running_process = subprocess.Popen(
        cmd,
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

@app.route('/get_title', methods=['GET'])
def get_title():
    """
    Returns chain_title from chains for a given chain_id.
    If chain_title is NULL or empty, returns empty string.
    """
    chain_id = request.args.get('chain_id', '')
    if not chain_id:
        return jsonify({'title': ''})
    if not os.path.exists(DB_PATH):
        return jsonify({'title': ''})

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT chain_title FROM chains WHERE id = ?", (chain_id,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0]:
        return jsonify({'title': row[0]})
    return jsonify({'title': ''})

@app.route('/get_results/<chain_id>', methods=['GET'])
def get_results(chain_id):
    """
    Lists all files in results/<chain_id>/ directory.
    If it doesn't exist, return empty list.
    """
    results_dir = os.path.join('results', chain_id)
    if not os.path.exists(results_dir) or not os.path.isdir(results_dir):
        return jsonify([])

    files = [f for f in os.listdir(results_dir) if os.path.isfile(os.path.join(results_dir, f))]
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
    If the plan is stored in a Pythonic format, we parse with ast.literal_eval -> JSON.
    """
    chain_id = request.args.get('chain_id', '')
    if not chain_id:
        return jsonify({'plan': None})
    if not os.path.exists(DB_PATH):
        return jsonify({'plan': None})

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT plan FROM chains WHERE id = ?", (chain_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        # No plan stored
        return jsonify({'plan': None})

    plan_data_raw = row[0]
    plan_dict = None
    if isinstance(plan_data_raw, (str, bytes)):
        # Attempt JSON first
        try:
            plan_dict = json.loads(plan_data_raw)
        except (json.JSONDecodeError, TypeError):
            # if that fails, try ast.literal_eval
            try:
                maybe_py = ast.literal_eval(plan_data_raw)
                if isinstance(maybe_py, dict):
                    plan_dict = maybe_py
                else:
                    plan_dict = None
            except:
                plan_dict = None
    # If not a string, do nothing
    return jsonify({'plan': plan_dict})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
