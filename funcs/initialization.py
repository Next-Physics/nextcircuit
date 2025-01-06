import os
import ast
import psutil
import sqlite3
import platform
import socket
import subprocess
from funcs.query_llm import query_llm
from funcs.db_funcs import update_chains_db


### Get the next stage of the chain ###
def get_next_stage(d):

    if d["id"] == "None":

        # Update the next stage
        d["next_stage"] = "generate_new_chain_id"

    else:

        cols_to_fetch = ','.join(["next_stage","plan","detected_hardware","detected_os","internet_connection","history"])

        chain_id = d["id"]
        conn = sqlite3.connect('db/main.db')
        c = conn.cursor()
        query = f"SELECT {cols_to_fetch} FROM chains WHERE id = ?"
        c.execute(query, (chain_id,))
        cols = [col[0] for col in c.description]
        res = c.fetchone()
        conn.close()

        # Make dict from cols and res
        res_dict = dict(zip(cols,res)) 

        d["next_stage"] = res_dict["next_stage"]
        if res_dict["plan"] is not None:
            d["plan"] = ast.literal_eval(res_dict["plan"])
        else:
            d["plan"] = None

### Setup Directories to host the database and results ###
def setup_dirs(script_folder,d):

    print("Setting up result directories...")
    # List of directory names to create
    directories_to_create = ["db", "results"]

    # Iterate through the list of directories
    for directory in directories_to_create:
        # Full path to the directory
        dir_path = os.path.join(script_folder, directory)
        
        # Check if the directory exists
        if not os.path.exists(dir_path):
            # Create the directory
            os.makedirs(dir_path)

        if directory == "results" and d['next_stage'] == "generate_new_chain_id":
            d["results_dir"] = dir_path
        else:
            d["results_dir"] = os.path.join(dir_path, str(d["id"]))


### Setup sqlite3 databases to store progress and data###
def setup_dbs():

    print("Setting up databases...")

    # Database name
    db_name = "db/main.db"

    # Check if the database exists
    if not os.path.exists(db_name):
        # Create the database
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        # Create the table
        c.execute('''
              CREATE TABLE chains
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 chain_title TEXT, 
                 user_query TEXT,
                 plan TEXT,
                 progress_stage TEXT,
                 progress_pct INTEGER,
                 next_stage TEXT,
                 curret_step TEXT,
                 attached_files TEXT,
                 proof_of_achievement TEXT, 
                 detected_hardware TEXT,
                 detected_os TEXT,
                 internet_connection TEXT,
                 history TEXT,
                 run_time TEXT,
                 chain_created_time TEXT, 
                 chain_last_modified TEXT)
              ''')

        # Commit the changes
        conn.commit()

        # Close the connection
        conn.close()

    print("Success!\n")


### Create folder to store results of the chain ###
def create_chain_results_dir(d):

    # Update the progress stage
    update_chains_db(d["id"], "progress_stage", "Set up chain_id results directory...")
    update_chains_db(d["id"], "progress_pct", 0)

    chain_id = d["id"]
    results_dir = os.path.join(d["results_dir"], str(chain_id))
    os.makedirs(results_dir, exist_ok=True)

    # Assign dir to d["results_dir"]
    d["results_dir"] = results_dir
    update_chains_db(d["id"], "next_stage", "Set up chain_id results directory...")
    return results_dir


### Generate a new chain ID ###
def generate_new_chain_id():
    conn = sqlite3.connect('db/main.db')
    c = conn.cursor()
    query = "INSERT INTO chains (chain_created_time, chain_last_modified) VALUES (datetime('now'), datetime('now'))"
    c.execute(query)
    conn.commit()
    chain_id = c.lastrowid
    conn.close()
    return chain_id


### Submit attached files information to the database ###
def submit_attached_files_info(d):

    info = "Submitting supplimentary information to database..."
    print(info)
    update_chains_db(d["id"], "progress_stage", info)

    # Submit supplimentary information to the database
    conn = sqlite3.connect('db/main.db')
    c = conn.cursor()
    query = "UPDATE chains SET attached_files = ?, chain_last_modified = datetime('now') WHERE id = ?"
    c.execute(query, (str(d["attached_files"]),d["id"]))
    conn.commit()
    conn.close()

    d["next_stage"] = "generate_agent_title"
    update_chains_db(d["id"], "next_stage", "generate_agent_title")


def generate_agent_title(d):

    ### Provide information on this stage
    info = "Generating agent title..."
    print(info)
    update_chains_db(d["id"], "progress_stage", info)

    print("Generating chain ID and agent title...")

    pre_prompt = """
    Given the user query below, write an ultra short title that summerizes what the user wants to achieve. Maximum 200 characters:

    """

    d["exe_prompt"] = pre_prompt + d["prompt"]
    
    ### Genrate title and id for the chain ###
    d["title"] = query_llm(d)

    update_chain_title(d)

    # Update the next stage
    d["next_stage"] = "create_elaboration_prompt"
    update_chains_db(d["id"], "next_stage", "create_elaboration_prompt")

    print("Success!\n")

    return d


def update_chain_title(d):
    conn = sqlite3.connect('db/main.db')
    c = conn.cursor()
    query = "UPDATE chains SET chain_title = ?, user_query = ? WHERE id = ?"
    c.execute(query, (d["title"], d["prompt"],d["id"]))
    conn.commit()
    conn.close()

def investigate_platform():

    platform_info = {
        "system_name": platform.system(),
        "node_name": platform.node(),
        "release": platform.release(),
        "version": platform.version(),
        "platform_info": platform.platform(),
        "processor": platform.processor(),
        "machine": platform.machine()
    }


    return platform_info



def investigate_hardware():
    
    hardware_info = {}

    hardware_info['logical_cpus'] = psutil.cpu_count(logical=True)
    hardware_info['physical_cpus'] = psutil.cpu_count(logical=False)
    cpu_freq = psutil.cpu_freq()
    hardware_info['cpu_frequency_mhz'] = cpu_freq.current
    hardware_info['cpu_usage_percent'] = psutil.cpu_percent(interval=1)
    virtual_mem = psutil.virtual_memory()
    hardware_info['total_memory_gb'] = virtual_mem.total / (1024 ** 3)
    hardware_info['available_memory_gb'] = virtual_mem.available / (1024 ** 3)
    partitions = psutil.disk_partitions()
    hardware_info['disk_partitions'] = []
    for partition in partitions:
        partition_info = {
            'device': partition.device,
            'mountpoint': partition.mountpoint,
            'fstype': partition.fstype,
            'opts': partition.opts,
            'usage': psutil.disk_usage(partition.mountpoint)._asdict()
        }
        hardware_info['disk_partitions'].append(partition_info)

    return hardware_info


def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    try:
        # Attempt to create a socket and connect to the server
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def investigate_circumstances(d):

    update_chains_db(d["id"], "progress_stage", "Gathering details on users physical hardware...")
    
    chain_id = d["id"]
    print("Investigating physical circumstances and updating DB...")
    
    # Detect the OS
    detected_os = investigate_platform()
    d["detected_os"] = detected_os
    update_chains_db(chain_id,"detected_os",detected_os)

    # Detect the hardware
    detected_hardware = investigate_hardware()
    d["detected_hardware"] = detected_hardware
    update_chains_db(chain_id,"detected_hardware",detected_hardware)

    # Check for internet connection
    internet_connection = check_internet_connection()
    d["internet_connection"] = internet_connection
    update_chains_db(chain_id,"internet_connection",internet_connection)

    d["next_stage"] = "propose_step_by_step_plan"
    update_chains_db(d["id"], "next_stage", "propose_step_by_step_plan")

    print("Updated DB with physical circumstances...")
    print("Success!\n")




##############################################
############## UNSUED FUNCTIONS #############
##############################################
# def get_ollama_port():

#     print("Identifying Ollama port...")

#     # Default port number
#     ollama_port = None

#     # # Check if Ollama is running on Windows
#     # if platform.system() == "Windows":
#     #     # Command to get the process ID of Ollama
#     #     command = 'tasklist /FI "IMAGENAME eq ollama.exe"'

#     #     # Execute the command and get the result
#     #     result = os.popen(command).read()

#     #     # Check if Ollama is running
#     #     if "No tasks are running" not in result:
#     #         # Parse the result to get the PID
#     #         lines = result.strip().split("\n")
#     #         if len(lines) >= 4:
#     #             # The PID is in the second column
#     #             pid = lines[3].split()[1]

#     #             # Command to get the port number
#     #             netstat_command = f'netstat -ano | findstr {pid}'

#     #             # Execute the command
#     #             netstat_result = os.popen(netstat_command).read()

#     #             # Parse the netstat result to find the listening port
#     #             for line in netstat_result.strip().split('\n'):
#     #                 if 'LISTENING' in line:
#     #                     cols = line.strip().split()
#     #                     local_address = cols[1]
#     #                     # Extract the port from the local address
#     #                     ollama_port = local_address.split(":")[-1]
#     #                     break
#     #     else:
#     #         print("Ollama is not running.")
#     #         ollama_port = None

#     # Check if Ollama is running on Linux
#     if platform.system() == "Linux":
#         try:
#             # Use sudo to ensure visibility into all processes
#             command = 'sudo netstat -tulnp | grep ollama'

#             # Execute the command using subprocess
#             result = subprocess.check_output(command, shell=True, text=True)

#             # Initialize variables to store the desired port and lowest PID
#             chosen_port = None
#             lowest_pid = float('inf')

#             # Parse the result to find the port based on criteria
#             for line in result.strip().split('\n'):
#                 if 'ollama' in line:
#                     # Split the line into components
#                     parts = line.split()
#                     local_address = parts[3]  # Typically in the format IP:PORT
#                     pid_process = parts[6]   # PID/Process
#                     pid = int(pid_process.split('/')[0])  # Extract the PID
                    
#                     # Check for the ":::" pattern in the local address
#                     if ":::" in local_address and pid < lowest_pid:
#                         # Extract the port and update the lowest PID
#                         chosen_port = local_address.split(":")[-1]
#                         lowest_pid = pid
#                         print("Success!\n")
#                         return chosen_port

#             if chosen_port:
#                 print(f"The chosen port is: {chosen_port} with PID: {lowest_pid}")
#             else:
#                 print("No matching process found.")
#                 exit()
                
#         except subprocess.CalledProcessError:
#             print("Ollama is not running or the port could not be found.")
#             exit()
#         except Exception as e:
#             print(f"An error occurred: {e}")
#             exit()


# def get_local_ip():

#     print("Getting local IP address...")

#     try:
#         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         s.connect(("8.8.8.8", 80))
#         local_ip = s.getsockname()[0]
#         s.close()
#         print("Local IP: ", local_ip)
#         print("Success!\n")
#         return local_ip
    
#     except Exception as e:
#         return f"Error occurred: {e}"

