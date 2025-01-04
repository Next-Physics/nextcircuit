### Module imports ###
import os, argparse, sys
import builtins

### Importing database update functions ###
from funcs.db_funcs import update_chains_db

### Importing Initialization functions ###
from funcs.initialization import setup_dirs
from funcs.initialization import setup_dbs
from funcs.initialization import submit_supplimentary_info
from funcs.initialization import investigate_circumstances
from funcs.initialization import generate_chain_title
from funcs.initialization import generate_new_chain_id
from funcs.initialization import create_chain_results_dir

### Importing Main Agent functions ###
from funcs.planning import categorize_content
from funcs.planning import create_elaboration_prompt
from funcs.planning import propose_step_by_step_plan
from funcs.planning import elaborate_on_steps
from funcs.planning import extract_step_titles

### Import Execution functions ###
from funcs.execution import execute_plan

### Importing Misc. functions ###
from funcs.misc import create_print_with_logging

### Argument Parser ###
parser = argparse.ArgumentParser(description='Ollama Agent')
parser.add_argument('--port', type=int, default=11411, help='Ollama Port')
parser.add_argument('--ip', type=str, default='localhost', help='Local IP')
parser.add_argument('--api_key', type=str, default=None, help='Relevant API Key')
parser.add_argument('--model', type=str, default=None, help='Model to use')
parser.add_argument('--query', type=str, default='', help='Users query')
parser.add_argument('--attached_files', type=str, default=None, help='Attached files')
parser.add_argument('--chain_id', help='Chain ID to resume')
args = parser.parse_args()


def main():

    ############################################################
    ################### SESSION SETTINGS #######################
    ############################################################


    if args.chain_id != "None":
        pass

    # Set user query
    #d["prompt"] = "Help me cure my brain cancer using oncolytic virus quickly!. From design to bioreactor production."

     # Dictionary to store data
    d = {}

    # Extract the arguments
    d["prompt"] = args.query
    d["attached_files"] = args.attached_files
    d["model"] = args.model
    d["port"] = args.port
    d["ip"] = args.ip
    d["api_key"] = args.api_key
    d["chain_id"] = args.chain_id
    

    print(d)
    ############################################################
    #################### INITIALIZATION ########################
    ############################################################

    # Move to directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # List of directory names to create
    setup_dirs(os.path.dirname(os.path.abspath(__file__)),d)

    # Setup sqlite3 databases to store progress and data
    setup_dbs()

    d["id"] = generate_new_chain_id()



    # Set up chain_id results directory results/<chain_id>
    create_chain_results_dir(d)

    # Submit supplimentary information to the database
    submit_supplimentary_info(d)

    # Overwrite print function to also log to database
    builtins.print = create_print_with_logging(d["id"])

    # Update the initial progress
    update_chains_db(d["id"], "progress_stage", "Starting...")
    update_chains_db(d["id"], "progress_pct", 0)
    

    print("PROMPT: ", d["prompt"])

    # Generate chain title
    update_chains_db(d["id"], "progress_stage", "Generating agent title...")
    generate_chain_title(d)
    

    # # Elabroate on the prompt
    # update_chains_db(d["id"], "progress_stage", "Enriching user prompt for detailed understanding...")
    # create_elaboration_prompt(d)
    # update_chains_db(d["id"], "progress_pct", 1)

    # Investigate circumstances (Physical Hardware, OS, Internet Connection)
    update_chains_db(d["id"], "progress_stage", "Gathering details on users physical hardware...")
    investigate_circumstances(d)

    ############################################################
    ######################## PLANNING ##########################
    ############################################################

    # Propose a step-by-step plan
    update_chains_db(d["id"], "progress_stage", "Laying out step-by-step plan to achieve the goal...")
    propose_step_by_step_plan(d)
    update_chains_db(d["id"], "progress_pct", 2)
    
    # Extract the step titles
    update_chains_db(d["id"], "progress_stage", "Extracting titles for each step...")
    extract_step_titles(d)

    # Elaborate on each step of the plan
    update_chains_db(d["id"], "progress_stage", "Elaborating & extending each step of the plan to gain more details...")
    elaborate_on_steps(d)
    update_chains_db(d["id"], "progress_pct", 3)
    
    #############################################################
    #################### EXECUTE PLAN ###########################
    #############################################################

    # Start execution of the plan
    update_chains_db(d["id"], "progress_stage", "Executing plan...")
    execute_plan(d)
    update_chains_db(d["id"], "progress_stage", "Finished")
    update_chains_db(d["id"], "progress_pct", 100)




### Main Loop of Agent ###
if __name__ == "__main__":
    main()



### THE DICTIONARYU STRCUTRE OF d ###
# d = {
#      "id" : "Chain ID",
#      "prompt" : "User Prompt",
#      "model" : "Model to use",
#      "port" : "Ollama Port",
#      "local_ip" : "Local IP",
#      "title" : "Chain Title",
#      "plan" : {"overview": "Plan Overview",
#                "num_steps": "Number of steps",
#                "steps": num: {"step_title": "Step Title",
#                           "content": "Step Content",
#                           "status": "Step Status"}]


 #                   }

 # Test