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
from funcs.planning import create_elaboration_prompt
from funcs.planning import propose_step_by_step_plan
from funcs.planning import elaborate_on_steps

### Import Execution functions ###
from funcs.execution import execute_plan

### Importing Misc. functions ###
from funcs.misc import create_print_with_logging


def main():

    ############################################################
    ################### SESSION SETTINGS #######################
    ############################################################

    # Dictionary to store data
    d = {}

    # Set user query
    d["prompt"] = "Write me a quick poem about roses and put in the file roses_poem.txt. Make it a quick 2 step plan. Don't overthink it"

    # Set model to use
   # d["model"] = 'mannix/llama3.1-8b-abliterated'
   # d["model"] = 'marco-o1'
    d["model"] = 'llama3.1:8b'


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

    # Overwrite print function to also log to database
    builtins.print = create_print_with_logging(d["id"])

    print("PROMPT: ", d["prompt"])
    print("")
    # Get Ollama port
    d["port"] = get_ollama_port()

    # Get local IP
    d["local_ip"] = get_local_ip()

    # Generate chain title
    generate_chain_title(d)

    # Elabroate on the prompt
    create_elaboration_prompt(d)

    # Investigate circumstances (Physical Hardware, OS, Internet Connection)
    investigate_circumstances(d["id"])

    ############################################################
    ######################## PLANNING ##########################
    ############################################################

    # Propose a step-by-step plan
    propose_step_by_step_plan(d)

    # Elaborate on each step of the plan
    elaborate_on_steps(d)
    
    #############################################################
    #################### EXECUTE PLAN ###########################
    #############################################################

    # Start execution of the plan
    execute_plan(d)




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
#                "steps": [{"num": "Step Number",
#                           "content": "Step Content",
#                           "status": "Step Status"}]


 #                   }