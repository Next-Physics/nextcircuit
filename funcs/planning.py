import sqlite3
from funcs.query_ollama import query_ollama
from funcs.db_funcs import update_chains_db

def extract_number_of_steps(d):

    d["exe_prompt"] = f"""
    Look closely at the following text:

    '{d['plan']['overview']}'

    What is the number of the absolut last step in this plan? Please return the highest (last) step-number only. Think twice and deeply before you answer. Answer just with the number only: 
    """

    return query_ollama(d)


def propose_step_by_step_plan(d):
    print("Layouting step by step plan to achieve the goal...")

    d["exe_prompt"] = f"""
    Task:

    Create an elaborate and extremely detailed plan to achieve the following goal:

    {d['prompt']}

    The plan must be suitable for an autonomous LLM agent with sudo rights on the system (headless ubuntu) to follow and execute without human input.

    Resources Available:
    Access to local PC hardware
    Ability to execute terminal commands
    Internet access for browsing and data retrieval
    Ability to read & write files to local storage

    Instructions:
    Provide step-by-step instructions to accomplish the goal (you will get the chance to elaborate more on each step later).
    Don't use sub steps ex. '3.1', instead make them unique numbers (**step 1**, **step 2**).
    Include hints of necessary terminal commands, code snippets, or scripts.
    Utilize available resources effectively to enhance the plan.
    Ensure each step is clear, unambiguous, and detailed enough to be followed precisely.
    Anticipate potential challenges and include troubleshooting tips.
    Always think twice and deeply and make sure the plan is foolproof.
    Include as many steps as possible

    Output Format:
    Begin with an overview of the strategy.
    Break down the plan into numbered steps.
    Use bullet points for additional details.
    Highlight commands or code in code blocks for clarity.

    """


    ### GENERATE PLAN OVERVIEW
    plan_overview = query_ollama(d)
    d["plan"] = {"overview":plan_overview}

    ### EXTRACT NUMBER OF STEPS ###
    num_steps = extract_number_of_steps(d)

    d["plan"]["num_steps"] = int(num_steps.strip())

    ### WRITE "PLAN" TO DATABASE ###
    update_chains_db(d["id"], "plan", d["plan"])

    print("Success!\n")

def elaborate_on_steps(d):

    for i in range(1, d["plan"]["num_steps"]+1):
        
        print(f"Elaborating on step {i}...")

        d["exe_prompt"] = f"""

        Given the following user query / request:

        '{d['prompt']}'

        Please elaborate carefully and detailed on step {i} of the following plan:

        '{d['plan']['overview']}'
        
        Your elboration for step {i} should include:

        - A clear and concise description of the actions required (should be able to be carried out autonomously by the LLM Agent).
        - Any necessary code or commands, enclosed in markdown code blocks.
        - Use language identifiers after the opening triple backticks in code blocks (e.g., ```python, ```bash).
        - Do not include additional commentary inside code blocks.
        - Do not make assumptions (make random guesses), if a step requires specific information, layout a proactive search step you can carry out
        - Ensure that code blocks contain only the code or commands to be executed."""

        step_elaboration = query_ollama(d)

        d["plan"]["steps"] = {f"num":i,
                                "content":step_elaboration,
                                "status":"pending"
                                }

        ### WRITE TO DATABASE ###
        update_chains_db(d["id"], "plan", d["plan"])

        print(step_elaboration)
        print("")

    print("Success!\n")

