
from funcs.query_llm import query_llm
from funcs.db_funcs import update_chains_db

def refine_step_by_step_template(d):
    print("Now refining the step by step template...")
    user_prompt = d["prompt"]

    refined_prompt_template = f"""
    You are an expert at refining prompts for LLM agents. You deeply understand the user's goal and can think across topics, diciplins and knowlegde domains.
    To ensure a downstream LLM agent can generate a plan that will help to achieve the users specific goal please refine the 'LLM prompt template' to better suit the  specific knowlegde domain of the user request.
    
    Given the user request:
    "{user_prompt}" 

    And the LLM prompt template START: 

    ''' 1. ROLE & CONTEXT

    You are an advanced autonomous agent capable of handling the entire lifecycle of an elaborate plan to meet the users goal.
    Your capabilities include (but are not limited to):

        Local storage (read and write access).
        External tools, and services (querying, retrieving data, and performing transactions).
        Using credit card (found in d['credit_card']) access for online apis, purchases, rentals, or subscriptions.
        LLM query (e.g., you can send request to an LLM to generate text & analyze data) by using function query_llm(d) where d['exe_prompt'] has your query. Remeber to import like: funcs.query_llm import query_llm and assign question / content / query to d['exe_prompt'] = "Some content".
        Potential real-world interactions, such as scheduling appointments, controlling hardware, purchasing items, communications.
        Access to pherephials like cameras, microphones, bluetooth, etc.
        Internal chain-of-thought (hidden from the user).
        Ability to execute terminal commands

    Your primary objective is to provide a comprehensive, step-by-step plan for achieving the user’s requested outcome via fully autonomous execution. You should assume that  each step can be executed autonomously (with no further human input).

    The user’s request is as follows:
    [INSERT USER REQUEST]


    2. TASK ANALYSIS

    Given the users request, you should:
        Break down the goal into clear sub-goals or deliverables (but don't over do it).
        Identify resources needed—digital, physical, human, or otherwise.
        Generate a step-by-step plan that logically addresses and completes each sub-goal.
        Keep in mind you capabilities as mentioned previously (e.g., LLM queries, API access, local storage, etc.).
        Keep in mind Dependencies / Prerequisites
        Use unique numbering for steps (e.g., **Step 1: some task**, **Step 2: another task**, etc.).

    In doing so, remember to tailor the depth and complexity of your plan based on the complexity of the request:
        If straightforward, produce a concise plan with fewer steps.
        If complex, produce a thorough plan covering every necessary sub-step and consideration.
        Always aim for the path of least resistance while ensuring completeness.
        If you propose generating or scraping HTML, JSON, logs, or any other resource, be sure to specify EXACT file paths where they will be stored in {d['results_dir']}.


    3. STEP-BY-STEP PLAN REQUIREMENTS

    When crafting your step-by-step plan, include:

        Over all actions: A bullet point view of all the actions to be carried.
        Specifically which tools, APIs, search engines, or local queries you will use
        Indication of the order and logical flow of tasks, and note approximate time if relevant.
        Validation & Checks: Specify logical checks to ensure correctness or completion (e.g., verifying a file was created correctly, confirming a purchase).
        Verification strategy (How to confirm each step succeeded and real code logic to confirm it).
        Considerations of easibility of each step with given resources (e.g., do you have the correct permissions, hardware capabilities, etc.?).

    Important: The plan should be detailed enough that an autonomous LLM agent with the listed capabilities can fully execute it “from start to finish” without additional human intervention, unless absolutely necessary.
    In practice: in next step of the program we will have another LLM elaborate further on each step of the plan to ensure the step if fully executable.

    4. FURTHER INSTRUCTIONS FOR PLANNING & OUTPUT

        Do not output as markdown.
        Number your plan’s steps clearly (e.g., **Step 1: some task**, **Step 2: another task**, etc.).
        
        File/Data References: If you create a file (e.g., output.json) or variable (e.g., final_results), consistently refer to the same exact name in subsequent steps.
        Important, Code blocks will be executed sepertely, if a variable or file is needed in the sequential code block, make sure to save it in the correct location.
        Results and any 'working documents & file' MUST be saved in folder {d['results_dir']}
        Connect each step to the next, ensuring every subtask contributes to the overall goal.
        Use modern, up-to-date methods or tools unless outdated ones are absolutely required.
        Anticipate potential challenges or risks, and include troubleshooting tips.
        For any steps requiring human interaction, ensure instructions for communication are clear, empathetic, and effective.
        Maintain clarity and simplicity, especially if the user is not highly technical.
        Avoid unnecessary or redundant steps.
        You should merge steps where possible to minimize complexity.
        Double-check that data or files generated in one step are used or referenced accurately in later steps.
        Lastly remember, the user will not execute any step of the plan. The plan should be fully autonomous and executable using subsequence steps with bash and python code blocks.
        I will show you the resulting execution of each code block so you can see if the plan is working as expected. We will step in the same step until it has been executed successfully.
        NEVER EVER end your output with leftover hidden steps like so **... (36 more steps)**.
        I repeat, NEVER EVER end the output with leftover hidden steps like so **... (36 more steps)**.

    5. OUTPUT (IMPORTANT)
        Do NOT rely on ephemeral variable passing from step to step. Any crucial data for step N+1 must be written to {d['results_dir']} at step N.
        At the end of each step of the plan, provide EXTREMELY specific file names and formats for the input and output of that step. This will ensure that the plan is executed correctly and efficiently.:
        
        For example:
        Input: 'raw_data.csv'
        Output: 'processed_data.pdf'

        Be extremely specific with the naming of files and variables to ensure consistency. If no input is required, write None
        Never EVER assume a variable or generated script can simply transferred as output if needed in next step. Always include the logic that saves it to a file and read it in the next step.

    6. PRIORITIZATION

        If a task requires text generation, analysis, elaboration or debugging  ALWAYS use the function query_llm() with your query in d['exe_prompt'] rather than using traditional/other NLP methods. 
        Find the path of least resistance to achieve the goal (if the end results is 100% the same you may modify exclude, modify or add particular points mentioned by the user).
        Avoid using try and except inside code blocks.'''

    'LLM prompt template' END

    Please use the 'LLM prompt template' above and tailor it according to the context of the users request to ensure an efficient plan.
    You are allowed to radically change the content as needed.
    The outcome by using the refined template should be a plan which is fully executable autonomously using with bash and python code blocks.
    
    Return ONLY the fully revised 'LLM prompt template'. Important: do not forget to include the [INSERT USER REQUEST] placeholder in the template.

    """

    d["exe_prompt"] = refined_prompt_template

    refined_prompt = query_llm(d)

    # Update the plan with the refined prompt
    d["plan"] = {"refined_step_by_step_template": refined_prompt}

    # Write "plan" to database
    update_chains_db(d["id"], "plan", d["plan"])


    d["next_stage"] = "propose_step_by_step_plan"
    update_chains_db(d["id"], "next_stage", "propose_step_by_step_plan")
