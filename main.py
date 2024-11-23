import os


def main():

    # Set placeholder values for the user query and error message
    query = "Why is the sky blue?"
    err_msg = ""


    # Import
    from funcs.initialization import setup_dirs
    from funcs.initialization import setup_dbs
    from funcs.initialization import get_ollama_port
    from funcs.initialization import make_chain_entry
    from funcs.initialization import investigate_circumstances


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
    ollama_port = get_ollama_port()
    if ollama_port:
        print(ollama_port)
        print("Success!\n")
    else:
        print("Error: Ollama not found on the local machine.\n")
        exit()

    
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
