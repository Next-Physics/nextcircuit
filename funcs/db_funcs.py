import sqlite3

def update_chains_db(chain_id,column,value):
    conn = sqlite3.connect('db/main.db')
    c = conn.cursor()
    query = f"UPDATE chains SET {column} = ?, chain_last_modified = datetime('now') WHERE id = ?"
    c.execute(query, (str(value), chain_id))
    conn.commit()
    conn.close()

### FUNCTION TO APPEND THE 'CONTENT' TO THE 'HISTORY' COLUMN (TEXT) IN THE 'CHAINS' TABLE###
def append_to_chain_history(chain_id,content):
    conn = None
    try:
        conn = sqlite3.connect('db/main.db')
        c = conn.cursor()
        query = f"SELECT history FROM chains WHERE id = ?"
        c.execute(query, (chain_id,))
        history = c.fetchone()[0]
        if history:
            history = history + "\n" + content
        else:
            history = content

        query = f"UPDATE chains SET history = ?, chain_last_modified = datetime('now') WHERE id = ?"
        c.execute(query, (history, chain_id))
        conn.commit()
    finally:
        if conn:
            conn.close()

