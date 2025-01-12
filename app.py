import os
import sqlite3
import subprocess
import signal
import ast
import json
import shutil
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)

DB_PATH = 'db/main.db'
UPLOAD_DIR = 'upload'  # Where we'll store temp and final uploads
RESULTS_DIR = 'results'  # Root results directory
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

running_process = None

def get_latest_chain_id():
    """Fetches the latest chain_id from the DB."""
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM chains ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def get_conversations():
    """Fetches existing conversations from the DB."""
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
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
    """Returns the conversation history + user_query + attached_files for a given conversation ID."""
    chain_id = request.form.get('id', '')
    if not os.path.exists(DB_PATH):
        return jsonify({'history': '', 'user_query': '', 'attached_files': '[]'})

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT history, user_query, attached_files
          FROM chains
         WHERE id = ?
    """, (chain_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({
            'history': row[0] or '',
            'user_query': row[1] or '',
            'attached_files': row[2] or '[]'
        })
    return jsonify({'history': '', 'user_query': '', 'attached_files': '[]'})

@app.route('/delete_conversation', methods=['POST'])
def delete_conversation():
    """Deletes a conversation from the DB, plus any associated upload and results folders."""
    chain_id = request.form.get('id', '')
    if not chain_id:
        return jsonify({'status': 'error', 'message': 'No id provided'})
    if not os.path.exists(DB_PATH):
        return jsonify({'status': 'error', 'message': 'Database not found'})

    # Remove the folder results/<chain_id> if it exists.
    results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), RESULTS_DIR, str(chain_id)))
    if os.path.exists(results_dir) and os.path.isdir(results_dir):
        shutil.rmtree(results_dir, ignore_errors=True)

    # Remove the folder upload/<chain_id> if it exists.
    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), UPLOAD_DIR, str(chain_id)))
    if os.path.exists(upload_dir) and os.path.isdir(upload_dir):
        shutil.rmtree(upload_dir, ignore_errors=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chains WHERE id = ?", (chain_id,))
    conn.commit()
    conn.close()

    return jsonify({'status': 'deleted'})

@app.route('/upload_file', methods=['POST'])
def upload_file():
    """
    Endpoint for uploading a local file to the server.
    If no chain exists yet, we temporarily store them under upload/None/.
    Otherwise, we store in upload/<latest_chain_id>/.
    """
    file = request.files.get('file')
    if not file:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400

    # Figure out if we have a chain_id from the database
    # If not, put the files in upload/None
    latest_chain_id = get_latest_chain_id()
    if not latest_chain_id:
        chain_for_upload = 'None'
    else:
        chain_for_upload = str(latest_chain_id)

    chain_upload_dir = os.path.join(UPLOAD_DIR, chain_for_upload)
    os.makedirs(chain_upload_dir, exist_ok=True)

    filename = file.filename
    # Very basic sanitization
    secure_filename = filename.replace('/', '_').replace('\\', '_')
    save_path = os.path.join(chain_upload_dir, secure_filename)

    try:
        file.save(save_path)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save file: {str(e)}'}), 500

    # We return only the sanitized filename
    return jsonify({'status': 'ok', 'path': secure_filename})

@app.route('/rename_upload_folder', methods=['POST'])
def rename_upload_folder():
    """
    Rename the folder 'None' to an actual chain ID once the DB is created 
    and a new chain is detected.
    """
    old_folder = request.form.get('old_folder', '')
    new_folder = request.form.get('new_folder', '')
    if not old_folder or not new_folder or old_folder == new_folder:
        return jsonify({'status': 'nop'})  # no operation needed

    old_dir = os.path.join(UPLOAD_DIR, old_folder)
    new_dir = os.path.join(UPLOAD_DIR, new_folder)

    if os.path.exists(old_dir) and os.path.isdir(old_dir):
        # Move/rename the entire folder
        shutil.move(old_dir, new_dir)

    return jsonify({'status': 'ok'})

@app.route('/run_agent')
def run_agent():
    """Starts main.py as a subprocess and streams stdout via SSE."""
    user_query = request.args.get('user_query', '')
    mode = request.args.get('mode', 'ollama')  # Default to Ollama
    ollama_ip = request.args.get('ollama_ip', 'localhost')
    ollama_port = request.args.get('ollama_port', '11411')
    chatgpt_api_key = request.args.get('chatgpt_api_key', '')
    chatgpt_model = request.args.get('chatgpt_model', 'gpt-3.5-turbo')
    attached_files_json = request.args.get('attached_files', '[]')
    chain_id = request.args.get('chain_id', 'None')

    global running_process

    preexec = None
    creationflags = 0

    if os.name == 'posix':
        preexec = os.setsid
    elif os.name == 'nt':
        import subprocess
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    # Build the command
    cmd = [
        'python', '-u', 'main.py',
        '--query', user_query,
        '--mode', mode,
        '--attached_files', attached_files_json,
        '--chain_id', chain_id
    ]

    if mode.lower() == 'ollama':
        model = request.args.get('ollama_model', 'default-ollama-model')
        cmd.extend(['--ip', ollama_ip, '--port', ollama_port, '--model', model])
    elif mode.lower() == 'chatgpt':
        cmd.extend(['--api_key', chatgpt_api_key, '--model', chatgpt_model])

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
    """Returns chain_title from chains for a given chain_id."""
    chain_id = request.args.get('chain_id', '')
    if not chain_id or not os.path.exists(DB_PATH):
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
    results_dir = os.path.join(RESULTS_DIR, str(chain_id))
    if not os.path.exists(results_dir) or not os.path.isdir(results_dir):
        return jsonify([])

    files = [f for f in os.listdir(results_dir) if os.path.isfile(os.path.join(results_dir, f))]
    return jsonify(files)

@app.route('/latest_conversations', methods=['GET'])
def latest_conversations():
    """Returns the entire conversation list as JSON to detect newly added chains."""
    convs = get_conversations()
    return jsonify(convs)

@app.route('/get_plan', methods=['GET'])
def get_plan():
    """
    Returns the plan stored in 'chains.plan' for a given chain_id.
    If the plan is stored in Pythonic format, parse with ast.literal_eval -> JSON.
    """
    chain_id = request.args.get('chain_id', '')
    if not chain_id or not os.path.exists(DB_PATH):
        return jsonify({'plan': None})

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT plan FROM chains WHERE id = ?", (chain_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        return jsonify({'plan': None})

    plan_data_raw = row[0]
    plan_dict = None
    if isinstance(plan_data_raw, (str, bytes)):
        # Attempt JSON first
        try:
            plan_dict = json.loads(plan_data_raw)
        except (json.JSONDecodeError, TypeError):
            # fallback to literal_eval
            try:
                maybe_py = ast.literal_eval(plan_data_raw)
                if isinstance(maybe_py, dict):
                    plan_dict = maybe_py
                else:
                    plan_dict = None
            except:
                plan_dict = None
    return jsonify({'plan': plan_dict})

@app.route('/get_progress', methods=['GET'])
def get_progress():
    """Returns progress_pct and progress_stage for a given chain_id."""
    chain_id = request.args.get('chain_id', '')
    if not chain_id or not os.path.exists(DB_PATH):
        return jsonify({'progress_pct': 0, 'progress_stage': ''})

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT progress_pct, progress_stage FROM chains WHERE id = ?", (chain_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({'progress_pct': row[0] or 0, 'progress_stage': row[1] or ''})
    return jsonify({'progress_pct': 0, 'progress_stage': ''})

if __name__ == '__main__':
    app.run( host='0.0.0.0', port=5000)