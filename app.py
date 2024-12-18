import os
import sqlite3
import subprocess
import signal
from flask import Flask, render_template, request, jsonify, Response, redirect, url_for

app = Flask(__name__)

DB_PATH = 'db/main.db'
RESULTS_DIR = 'results'
UPLOAD_DIR = 'uploaded_files'
os.makedirs(UPLOAD_DIR, exist_ok=True)

running_process = None

def get_conversations():
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Include id in the select
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
    conversations = get_conversations()
    return render_template('index.html', conversations=conversations)

@app.route('/get_conversation', methods=['POST'])
def get_conversation():
    id = request.form.get('id', '')
    if not os.path.exists(DB_PATH):
        return jsonify({'history': ''})
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT history FROM chains WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({'history': row[0]})
    return jsonify({'history': ''})

@app.route('/delete_conversation', methods=['POST'])
def delete_conversation():
    id = request.form.get('id', '')
    if not id:
        return jsonify({'status': 'error', 'message': 'No id provided'})
    if not os.path.exists(DB_PATH):
        return jsonify({'status': 'error', 'message': 'Database not found'})

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chains WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return jsonify({'status': 'deleted'})

@app.route('/run_agent')
def run_agent():
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

    # Use unbuffered Python so output streams immediately
    running_process = subprocess.Popen(
        ['python', '-u', 'main.py', '--query', user_query, '--ip', ollama_ip, '--port', ollama_port, '--attached_files', attached_files_json],
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
        if os.name == 'posix':
            os.killpg(os.getpgid(running_process.pid), signal.SIGTERM)
        else:
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

@app.route('/upload_file', methods=['POST'])
def upload_file():
    # Handles file uploads from the client. Store them in UPLOAD_DIR and return the server path.
    file = request.files.get('file')
    if not file:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    filename = file.filename
    server_path = os.path.join(UPLOAD_DIR, filename)
    file.save(server_path)
    abs_path = os.path.abspath(server_path)
    return jsonify({'status':'ok', 'path': abs_path})

@app.route('/latest_conversations', methods=['GET'])
def latest_conversations():
    # Returns updated conversation list
    convs = get_conversations()
    return jsonify(convs)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
