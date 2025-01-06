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

- Retain all original user instructions and intent.
- Fill in implied details necessary to fully accomplish the goal.
- Assume urgency and importance.
- Specify realistic resources and actions to achieve the goal from start to finish.
- Ensure logical consistency and avoid contradictory or irrelevant tangents.
- Include only steps directly related to accomplishing the user’s request.
- Avoid unnecessary complexity or unrelated tasks.
- Make it fully actionable so the autonomous agent can execute all steps (research, ordering, simulation, report writing, communication, etc.) immediately.

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

    d["exe_prompt"] = f"""
1. ROLE & CONTEXT

You are an advanced autonomous agent capable of handling the entire lifecycle of an elaborate plan to meet the users goal.
Your capabilities include (but are not limited to):

    Local storage (read and write access).
    External APIs, tools, and services (querying, retrieving data, and performing transactions).
    Using credit card (found in d['credit_card']) access for online apis, purchases, rentals, or subscriptions.
    LLM query (e.g., you can send request to an LLM to generate text & analyze data) by using function query_llm(d) where d['exe_prompt'] has your query. Remeber to import like: funcs.query_llm import query_llm and assign question / content / query to d['exe_prompt'] = "Some content".
    Potential real-world interactions, such as scheduling appointments, controlling hardware, purchasing items, communications.
    Access to pherephials like cameras, microphones, bluetooth, etc.
    Internal chain-of-thought.
    Ability to execute terminal commands

Your primary objective is to provide a comprehensive, step-by-step plan for achieving the user’s requested outcome. You should assume that you can execute each step autonomously (with no further human input).

The user’s request is as follows:
{d['prompt']}


2. TASK ANALYSIS

Given the users request, you should:
    Break down the goal into clear sub-goals or deliverables.
    Identify resources needed—digital, physical, human, or otherwise.
    Generate a step-by-step plan that logically addresses and completes each sub-goal.
    Keep in mind you capabilities as mentioned previously (e.g., LLM queries, API access, local storage, etc.).
    Use unique numbering for steps (e.g., **Step 1: some task**, **Step 2: another task**, etc.).

In doing so, remember to tailor the depth and complexity of your plan based on the complexity of the request:
    If straightforward, produce a concise plan with fewer steps.
    If complex, produce a thorough plan covering every necessary sub-step and consideration.
    Always aim for the path of least resistance while ensuring completeness.

3. STEP-BY-STEP PLAN REQUIREMENTS

When crafting your step-by-step plan, include:

    Over all actions: A bullet point view of all the actions to be carried.
    Proposal of which tools, APIs, search engines, or local queries you will use
    Indication of the order and logical flow of tasks, and note approximate time if relevant.
    Dependencies / Prerequisites: Note if any steps must be completed before others can begin.
    Validation & Checks: Specify how to verify correctness or completion (e.g., verifying a file was created correctly, confirming a purchase, or obtaining final user approval).
    Logic representation 

Important: The plan should be detailed enough that an autonomous LLM agent with the listed capabilities can fully execute it “from start to finish” without additional human intervention, unless absolutely necessary.
In practice: Next step of the program we will have another LLM elaborate further on each step of the plan to ensure the step if fully executable.

4. FURTHER INSTRUCTIONS FOR PLANNING & OUTPUT

    Do not output as markdown.
    Number your plan’s steps clearly (e.g., **Step 1: some task**, **Step 2: another task**, etc.).
    File/Data References: If you create a file (e.g., output.json) or variable (e.g., final_results), consistently refer to the same exact name in subsequent steps.
    Important, Code blocks will be executed sepertely, if a variable or file is needed in the sequential code block, make sure to save it in the correct location.
    Results and any 'working documents & file' must be saved in folder {d['results_dir']}
    Connect each step to the next, ensuring every subtask contributes to the overall goal.
    Use modern, up-to-date methods or tools unless outdated ones are absolutely required.
    Anticipate potential challenges or risks, and include troubleshooting tips.
    Verify feasibility of each step with given resources (e.g., do you have the correct permissions, hardware capabilities, etc.?).
    For any steps requiring human interaction, ensure instructions for communication are clear, empathetic, and effective.
    Maintain clarity and simplicity, especially if the user is not highly technical.
    Avoid unnecessary or redundant steps.
    Minimize cost (avoid paid APIs if free alternatives exist).
    Double-check that data or files generated in one step are used or referenced accurately in later steps.
    Lastly remember, the user will not execute any step of the plan. The plan should be fully autonomous and executable using subsequence steps with bash and python code blocks.
    I will show you the resulting execution of each code block so you can see if the plan is working as expected. We will step in the same step until it has been executed successfully.
    NEVER EVER end your output with leftover hidden steps like so **... (36 more steps)**.
    I repeat, NEVER EVER end the output with leftover hidden steps like so **... (36 more steps)**.

5. OUTPUT

    At the end of each step of the plan, provide extremely specific file names and formats for the input and output of that step. This will ensure that the plan is executed correctly and efficiently.:
    
    For example:
    Input: 'raw_data.csv'
    Output: 'processed_data.pdf'

    Be extremely specific with the naming of files and variables to ensure consistency. If no input is required, write None

6. PRIORITIZATION

    If a task requires text generation or text analysis, ALWAYS use the function query_llm() with your query in d['exe_prompt'] rather than using traditional/other NLP methods. 
    Find the path of least resistance to achieve the goal (if the end results is 100% the same you may modify exclude, modify or add particular points mentioned by the user).

    """

    # Generate plan overview
    plan_overview = query_llm(d)
    d["plan"] = {"overview": plan_overview}

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
        As a planning and action expert, elaborate extensively on **Step {i}** of this plan:

        **Plan Overview**:
        '{d['plan']['overview']}'

        **Instructions**:

        a. **Elaboration Requirements**
        - A concise description of the all actions required, ensuring it can be carried out autonomously by the LLM agent and directly contribute towards achieving the goal.
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
        - Ensure you don't accidentally mix up python and bash commands in the same code block unless it is designed to specifically work together.
        - Know you limitations as an LLM agent and don't try to do things that are impossible for an LLM agent to do, instead find a genious workaround.

        c. **Consolidate Dependent Code in a Single Code Block**  
        - If any code in this step relies on or references variables, imports, or data from earlier lines within the same step, **keep it all within exactly one fenced code block** (e.g., triple backticks for Python: ```python ... ```).
        - If you need to demonstrate partial references to code, do so inline (e.g. `like this`) or as comments **without** creating new fenced blocks.

        d. **Separate Only Completely Independent Code**  
        - If you must show code for a completely different context (e.g., Bash script, Dockerfile) that does not interact with the Python code, you may create a separate fenced code block.  
        - **Otherwise, do not split code** into multiple fenced blocks.

        e. **Detailed Procedure**  
        - Explain step-by-step instructions linking to earlier and subsequent steps.
        - List any tools, libraries, or data sources required, and how to install or import them.
        - Clearly specify how to save results in the folder {d['results_dir']} for use in subsequent steps.

        f. **Output Passing**  
        - Explicitly mention how to pass or store the outputs (e.g., variables, files) so subsequent steps can use them.
        - Use consistent file paths, especially those referencing {d['results_dir']}.

        **Important**:  
        - Ensure choerence between current step and the surrounding steps.
        - Any code for this step must be placed inside a single fenced code block if the lines are interdependent.  
        - Avoid splitting related Python code, as we run each fenced code block in isolation.  
        - Keep the number of fenced code blocks minimal for each step.

        - Example usage of the function query_llm along with a local file:
        ```python
        from funcs.query_llm import query_llm

        with open("results_dir/some_file>", "r") as f:
            content = f.read()

        d["exe_prompt"] = "Detailed instructions:" + content
        answer = query_llm(d)

        with open("results_dir/another_file", "w") as f:
            f.write(answer)
        ```

        **Deliverables**:
        - A thorough, foolproof explanation of how to execute Step {i}.
        - A single self-contained (or minimal separate) code block that can be run to produce the expected results.
        - Clear instructions for verifying success or diagnosing failures.

        **Now, please provide your elaboration for Step {i}**:
        """

        step_elaboration = query_llm(d)

        # Update status to "elaborated"
        d["plan"]["steps"][i]["elaboration"] = step_elaboration

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