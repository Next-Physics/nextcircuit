import os

### Importing Initialization functions ###
from funcs.initialization import setup_dirs
from funcs.initialization import setup_dbs
from funcs.initialization import get_ollama_port
from funcs.initialization import get_local_ip
from funcs.initialization import make_chain_entry
from funcs.initialization import investigate_circumstances
from funcs.initialization import generate_chain_id_and_title


def main():

    # Set placeholder values for the user query and error message
    prompt = "Help me make a busniess plan to start a new ice cream company, including how to get suppliers of raw materials"
    model = 'llama3.1:8b'

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
    port = get_ollama_port()
    if port:
        print(port)
        print("Success!\n")
    else:
        print("Oops: Ollama not found on the local machine.\n")
        exit()

    # Get Ip address of the local machine
    print("Getting local IP address...")
    local_ip = get_local_ip()
    print("Local IP: ", local_ip)
    print("Success!\n")
    
    print("Generating chain ID and title...")
    id,title = generate_chain_id_and_title(prompt, model, local_ip, port)
    print("The ID is:", id)
    print("The Title is:",title)
    print("Success!\n")

   # print("Making project entry in the database...")
   # from funcs.initialization import make_chain_entry
   # make_chain_entry("Project Title", query)

    ### Investigate physical circumstances: local hardware, OS and internet connection ###
  #  print("Investigating physical circumstances and updating DB...")
 #   investigate_circumstances()
  #  print("Success!\n")


    ### Submit user query to the database and agent ###



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
