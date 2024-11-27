### Module imports ###
import os
import builtins

### Importing Initialization functions ###
from funcs.initialization import setup_dirs
from funcs.initialization import setup_dbs
from funcs.initialization import get_ollama_port
from funcs.initialization import get_local_ip
from funcs.initialization import investigate_circumstances
from funcs.initialization import generate_chain_title
from funcs.initialization import generate_new_chain_id

### Importing Main Agent functions ###
from funcs.planning import propose_step_by_step_plan
from funcs.planning import elaborate_on_steps

### Importing Misc. functions ###
from funcs.misc import create_print_with_logging




def main():

    ############################################################
    ################### SESSION SETTINGS #######################
    ############################################################

    # Dictionary to store data
    d = {}

    # Set user query
    d["prompt"] = "Help me make an oncolytic virus to cure my brain cancer. From design to bioreactor production."

    # Set model to use
    d["model"] = 'mannix/llama3.1-8b-abliterated'
   # d["model"] = 'marco-o1'
   # d["model"] = 'llama3.1:8b'


    ############################################################
    #################### INITIALIZATION ########################
    ############################################################

    # Move to directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # List of directory names to create
    setup_dirs(os.path.dirname(os.path.abspath(__file__)))

    # Setup sqlite3 databases to store progress and data
    setup_dbs()

    d["id"] = generate_new_chain_id()

    # Overwrite print function to also log to database
    builtins.print = create_print_with_logging(d["id"])

    # Get Ollama port
    d["port"] = get_ollama_port()

    # Get local IP
    d["local_ip"] = get_local_ip()

    # Make chain entry
    d = generate_chain_title(d)

    # Investigate circumstances (Physical Hardware, OS, Internet Connection)
    investigate_circumstances(d["id"])


    ############################################################
    ################## MAIN AGENT CODE #########################
    ############################################################

    print("Layouting step by step plan to achieve the goal...")
    propose_step_by_step_plan(d)
    print("Success!\n")

    print("Elaborating on each step of the plan...")
    elaborate_on_steps(d)
    print("Success!\n")


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
