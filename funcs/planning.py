import sqlite3
from funcs.query_llm import query_llm
from funcs.db_funcs import update_chains_db


def create_elaboration_prompt(d):

    print("Original user prompt: ", d["prompt"],"\n")

    ### Provide information on this stage
    info = "Elaborating on user prompt..."
    print(info)
    update_chains_db(d["id"], "progress_stage", info)

    d["exe_prompt"] = f"""You are an expert at reformulating and expanding user queries into a more comprehensive and actionable request, ensuring no contradictions or unnecessary complexities. Your goal is to produce a single, coherent elaboration of the user’s initial query that can be directly executed by an autonomous AI agent with broad capabilities (internet access, ability to purchase items, communicate online, and utilize local computing resources) without needing additional clarification.

The elaborated query must:

- Fill in implied details necessary to fully accomplish the goal.
- Retain all original user instructions and intent.
- Assume urgency and importance.
- Specify realistic resources and actions to achieve the goal from.
- Ensure logical consistency and avoid contradictory or irrelevant tangents.
- Avoid unnecessary complexity or unrelated tasks.
- Assume that it is aware the plan will be executed by an autonomous agent (primarily using bash and python) with broad capabilities.
- Assume the user is aware the machine can interface with both local pc, the internet and the physical world (e.g., webcam, microphone, bluetooth etc.).
- Make the request phrased such that it is fully actionable by an autonomous agent that can execute all steps  immediately.
- Assume that the agent can perfor anything from required research, ordering, simulation, report writing, communication, reasoning
- Ensure that NO unnecessary tasks are included in the elaboration.
- Assume the user don't wants to use APIs or paid services unless absolutely necessary.

Please respond only with the fully elaborated query. Do not include these instructions in your response.

User’s original query:
"{d['prompt']}"
"""
    d['prompt'] = query_llm(d)

    # Update the next stage
    d["next_stage"] = "investigate_circumstances"
    update_chains_db(d["id"], "next_stage", "investigate_circumstances")
    
    return d




def extract_number_of_steps(d):

    print("\nTotal number of steps in the plan:")
    d["exe_prompt"] = f"""
    Look closely at the following text:

    '{d['plan']['overview']}'

    What is the number of the absolut last step in this plan? Please return the highest (last) step-number only. Think twice and deeply before you answer. Answer just with the number only: 
    """

    return query_llm(d)


def propose_step_by_step_plan(d):

    ### Provide information on this stage
    info = "Laying out step-by-step plan to achieve the goal..."
    print(info)
    update_chains_db(d["id"], "progress_stage", info)

    step_by_step_combined_prompt = d['plan']['refined_step_by_step_template'].replace("[INSERT USER REQUEST]", d['prompt'])

    d["exe_prompt"] = step_by_step_combined_prompt 

    # Generate plan overview
    plan_overview = query_llm(d)
    d["plan"]["overview"] = plan_overview

    # Extract number of steps
    num_steps = extract_number_of_steps(d)
    d["plan"]["num_steps"] = int(num_steps.strip().split(".")[0].split(",")[0])

    # Write "plan" to database
    update_chains_db(d["id"], "plan", d["plan"])

    # Update progress percentage
    update_chains_db(d["id"], "progress_pct", 2)

    # Update the next stage
    d["next_stage"] = "extract_step_titles"
    update_chains_db(d["id"], "next_stage", "extract_step_titles")

    return d


def extract_step_titles(d):

    ### Provide information on this stage
    info = "Extracting titles for each step..."
    print(info)
    update_chains_db(d["id"], "progress_stage", info)

    print("Extracting steps titles...")
    # Initialize 'steps' if it doesn't exist
    if "steps" not in d["plan"]:
        d["plan"]["steps"] = {}

   
    # Attempt to split the overview into steps using python logic
    try:
        pre_split = d["plan"]["overview"].split("**Step",1000)
    except:
        pass

    # Extract step titles
    for i in range(1, d["plan"]["num_steps"] + 1):

        # Extract step title using python logic
        try:
            step_title = pre_split[i].split("**")[0].split(":")[1].strip()

        # If python logic fails, prompt the LLM to extract the step title
        except:

            d["exe_prompt"] = f""" You are an expert at text extract. Please extract the title of step {i} of the following plan:

            '{d['plan']['overview']}'

            You should remove the ** Chareters along with the step number and return the TITLE of the step.

            What is the extracted step title of step {i}? Return only the extracted step title text only.

            """

            step_title = query_llm(d)


        d["plan"]["steps"][i] = {
            "step_title": step_title,
            "status": "pending"
            }

        # Write to database
        update_chains_db(d["id"], "plan", d["plan"])

        # Update the next stage
        d["next_stage"] = "elaborate_on_steps"
        update_chains_db(d["id"], "next_stage", "elaborate_on_steps")



### A function that based on the elaborated steps creates python logic that checks for success
def create_step_success_check_logic(i,d):

    print("Writing logic to check whether the step was successfully executed")

    d["exe_prompt"] = f"""You are an expert at creating python logic that checks if an LLM agent has successfully completed / executed a step in a plan. 
    
    Your goal is to create a single python code block that checks if a step successfully run or produce the expected output.

    Here are some examples of things to check for:
    - If a step is expected to have create a particular file, you should check if the file exists.
    - If a step is expected to have downloaded a file, you should check if the file is present.
    - If a step is expected to have generated a particular output, you should check if the output is correct.
    - In general, for any output of a step, you should also ensure that files are not empty

    Given the following step details:

    {d["plan"]["steps"][i]["elaboration"]}

    Please write the appropriate python code block we can run to check whether the expected output was created.
    
    Example of a expected python code block:
    ```python
    import os

    msg = ""
    if os.file.exists("path/to/file.csv") and os.getsize_of("path/to/file.csv") > 0: # some logic that see if file has a size larger than 0:
        return True,msg

    elif os.file.exists:("path/to/file.csv") and os.getsize_of("path/to/file.csv") == 0:
        msg = "File is empty"
        return False,msg
    
    else:
        msg = "File not found or created"
        return False,msg
    ```

    **Keep in mind**
    If the step is not expected to create any output simply return True and an empty msg = ""

    Now please return ONLY the expected step-success python logic: 

    """

    return query_llm(d)




def elaborate_on_steps(d):

    info = "Elaborating & extending each step of the plan to gain more details..."
    print(info)
    update_chains_db(d["id"], "progress_stage", info)

    for i in range(1, d["plan"]["num_steps"] + 1):
        
        if d["plan"]["steps"][i]["status"] == "elaborated":
            continue
        # Update status
        d["plan"]["steps"][i]["status"] = "elaborating"
        update_chains_db(d["id"], "plan", d["plan"])
        
        print(f"\n--- Elaborating on Step {i} ---")
        
        # Generate elaboration prompt
        d["exe_prompt"] = f"""
        As a planning and action expert, you goal is to elaborate extensively on **Step {i}** of this plan:

        **Plan Overview**:
        '{d['plan']['overview']}'


        **Instructions**:

        a. **Elaboration Requirements**
        - A description of the all actions required, ensuring it can be carried out autonomously by an LLM agent that directly contributes towards achieving the goal.
        - Provide all full necessary code or commands, enclosed in markdown code blocks.
        - Provide real executable code - don't provide hypothetical examples
        - Language identifiers after the opening triple backticks in code blocks (e.g., ```python, ```bash).
        - Ensure that code blocks contain only the code or commands to be executed.
        - An answer that makes sense and is relevant to the step (no nonsensical outputs).

        b. ** Remember **
        - Think critically and deeply about the step to ensure it is foolproof.
        - If the step involves interacting with the physical world (e.g., using the webcam), provide detailed instructions on how to process the data (e.g., image analysis, object detection) to achieve the goal.
        - Do not make assumptions; if a step requires specific information to make sense or be fullfilled, expand the step with a task for local or online searching.
        - Be determined and persistent in solving the problem, exploring alternative methods if necessary.
        - Do not include additional commentary inside code blocks.
        - Refrain from reinventing the wheel; use popular existing & widely adaopted tools and methods where obviously possible (object detection, text summerization, etc).
        - You can always extend your knowlegde by talking with an LLM in python by assigning your full query to d["exe_prompt"] and get your answer like so "answer = query_llm(d)" (assume this function is always available)
        - Example of using the LLM python function: d["exe_prompt"] = "Analyze this text:" + f.read() and then featch the LLM answer like so "answer = query_llm(d)"
        - Query_llm DOES NOT have direct access to the internet, so you need to provide the necessary information as part of the query.
        - Refrain from using old traditional NLP methods when analyzing retrieved / downloaded content, instead use the query_llm() function.
        - Refrain from using paid APIs, unless they are absolutely necessary.
        - If a step requires interactions with humans, ensure the communication is clear, pursuaive, triggers empathy and is effective.
        - Do not accidentially mix up python and bash commands in the same code block unless it is designed to specifically work together.
        - Know you limitations as an LLM agent and don't try to do things that are impossible for an LLM agent to do, instead find a genious workaround.

        c. **Consolidate Dependent Code in a Single Code Block**  
        - If any code in this step relies on or references variables, imports, or data from earlier lines within the same step, **keep it all within exactly one fenced code block** (e.g., triple backticks for Python: ```python ... ```).
        - If you need to demonstrate partial references to code, do so inline (e.g. `like this`) or as comments **without** creating new fenced blocks.

        d. **Separate Only Completely Independent Code**  
        - If you must show code for a completely different context (e.g., Bash script, Dockerfile) that does not interact with the Python code, you may create a separate fenced code block.  
        - **Otherwise, do not split code** into multiple fenced blocks.

        e. **Detailed Procedure**  
        - Explain step-by-step instructions linking to earlier and subsequent steps.
        - Include all tools, libraries, or data sources required, and the logic to install or access them.
        - Clearly specify how to save results in the folder {d['results_dir']} for use in subsequent steps.

        f. **Outputs and transfering of information **  
        - Use consistent file paths, and remember to save results to {d['results_dir']} so that the next step can access the results.
        - NEVER end on a variable, always save the variable to a file if a following step needs it.
        - Explicitly mention how to pass or store the outputs (e.g., variables, files) so subsequent steps can use them.

        **Important**:  
        - Ensure choerence between current step and the surrounding steps.
        - Any code for this step must be placed inside a single fenced code block if the lines are interdependent.  
        - Avoid splitting related Python code, as we run each fenced code block in isolation.  
        - Keep the number of fenced code blocks minimal for each step.
        - Code must contain logical checks to ensure the desire output is achieved (empty files are not acceptable).
        - Do not assume ANY user inputs such as key presses or mouse clicks to run the step.
        - REMEMBER generated files,code,scripts and documents MUST be saved to {d['results_dir']} for use in subsequent steps.


        - Example usage of the function query_llm along with a local file:
        ```python
        from funcs.query_llm import query_llm

        with open("results_dir/some_file>", "r") as f:
            content = f.read()

        # d is already defined in the environment
        d["exe_prompt"] = "Detailed instructions:" + content
        answer = query_llm(d)

        with open("results_dir/another_file", "w") as f:
            f.write(answer)
        ```

        **Deliverables**:
        - A thorough, foolproof explanation of how to execute Step {i}.
        - A single self-contained (or minimal separate) code block that can be run to produce the expected results.
        - Clear logic for verifying success or diagnosing failures.
        - Code to save generated code/scripts/documents to {d['results_dir']} for use in subsequent steps.

        """

        if i > 1:
            d["exe_prompt"] += f"""\n
            **Keep in mind**:
            - To ensure coherences between steps here is the elaboration of the previous step {i-1}:
            {d["plan"]["steps"][i-1]["elaboration"]}
            """
        
        d["exe_prompt"] += f"""\n
        **Now, please provide your elaboration for Step {i} of the Plan Overview**:
        """

        step_elaboration = query_llm(d)

        # Update status to "elaborated"
        d["plan"]["steps"][i]["elaboration"] = step_elaboration

        # Write check logic step = create_step_success_check_logic(i,d):
        d["plan"]["steps"][i]["success_check"] = create_step_success_check_logic(i,d)

        # Set status back to pending
        d["plan"]["steps"][i]["status"] = "elaborated"

        # Write to database
        update_chains_db(d["id"], "plan", d["plan"])
        update_chains_db(d["id"], "progress_pct", 2 + round( 6 / d["plan"]["num_steps"] * i)) 
    
    d["next_stage"] = "execute_plan"
    update_chains_db(d["id"], "next_stage", "execute_plan")




##################################################
############ UNUSED FUNCTIONS #####################
##################################################
# ### Given the users prompt, please return a list of selected keywords that are relevant to the prompt
# def categorize_content(d):
#     print("Categorizing content...")
#     d["exe_prompt"] = f"""Given the following user query:

#     "{d['prompt']}"

#     Please categorize the content of the query into one of the following categories:

#     - Food
#     - Technology
#     - Pharmaceuticals
#     - Medicine & Health
#     - Mathematics
#     - Physics
#     - Chemistry
#     - Biology
#     - Computer Science
#     - Engineering
#     - History
#     - Geography
#     - Literature
#     - Art
#     - Sports
#     - Politics
#     - Entertainment

#     And return just the single keyword that best describes the content of the query. Nothing but the keyword. What is the keyword?

#     """

#     d["category"] = query_llm(d)