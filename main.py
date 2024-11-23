import os

### Importing Initialization functions ###
from funcs.initialization import setup_dirs
from funcs.initialization import setup_dbs
from funcs.initialization import get_ollama_port
from funcs.initialization import get_local_ip
from funcs.initialization import make_chain_entry
from funcs.initialization import investigate_circumstances
from funcs.initialization import generate_chain_id_and_title

### Importing Main Agent functions ###
from funcs.planning import propose_step_by_step_plan


def main():

    # Set placeholder values for the user query and error message
    d = {}
    d["prompt"] = "Help me make a busniess plan to start a new ice cream company, including how to get suppliers of raw materials"
    d["model"] = 'llama3.1:8b'

    # List of directory names to create
    print("Setting up directories...")
    setup_dirs(os.path.dirname(os.path.abspath(__file__)))
    print("Success!\n")

    # Setup sqlite3 databases to store progress and data
    print("Setting up databases...")
    setup_dbs()
    print("Success!\n")

    # Identify Ollama port
    print("Identifying Ollama port...")
    d["port"] = get_ollama_port()
    if d["port"]:
        print(d["port"])
        print("Success!\n")
    else:
        print("Oops: Ollama not found on the local machine.\n")
        exit()

    # Get Ip address of the local machine
    print("Getting local IP address...")
    d["local_ip"] = get_local_ip()
    print("Local IP: ", d["local_ip"])
    print("Success!\n")
    
#     
    print("Generating chain ID and title...")
    d = generate_chain_id_and_title(d)
    print("The ID is:", d["id"])
    print("The Title is:",d["title"])
    print("Success!\n")

    print("Investigating physical circumstances and updating DB...")
    investigate_circumstances(id)
    print("Updated DB with physical circumstances\n")
    print("Success!\n")

    ############################################################
    ################## MAIN AGENT CODE #########################
    ############################################################

    # print("Layout step by step plan to achieve the goal...")
    # layout_plan(id,prompt)

    ### Get immediate Plan from the agent ###
    # Input: User Query, 
    # Output: Plan (List of actions)

    ### Review plan and rewrite if necessary (RTDB) ###
    # Input: Plan (List of actions)
    # Output: Revised Plan (List of actions)

    ### Based on final plan, define what is a good proof of achievement ###
    # Input: Revised Plan (List of actions)
    # Output: Proof of Achievement

    ### Execute the plan ###
    # Input: Revised Plan (List of actions)
    # Output: Proof of Achievement

    ### Submit Proof of Achievement to the database and agent ###
    # Input: Proof of Achievement
    # Output: None

    ### End of Main Loop ###
    # Input: None
    # Output: None

    ### End of Main Function ###
    # Input: None
    # Output: None


### Main Loop of Agent ###
if __name__ == "__main__":
    main()
