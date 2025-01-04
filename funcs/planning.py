import sqlite3
from funcs.query_llm import query_llm
from funcs.db_funcs import update_chains_db

### Given the users prompt, please return a list of selected keywords that are relevant to the prompt
def categorize_content(d):
    print("Categorizing content...")
    d["exe_prompt"] = f"""Given the following user query:

    "{d['prompt']}"

    Please categorize the content of the query into one of the following categories:

    - Food
    - Technology
    - Pharmaceuticals
    - Medicine & Health
    - Mathematics
    - Physics
    - Chemistry
    - Biology
    - Computer Science
    - Engineering
    - History
    - Geography
    - Literature
    - Art
    - Sports
    - Politics
    - Entertainment

    And return just the single keyword that best describes the content of the query. Nothing but the keyword. What is the keyword?

    """

    d["category"] = query_llm(d)

def create_elaboration_prompt(d):
    print("Elaborating / extending user query...")
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

    print("Laying out step-by-step plan to achieve the goal...")


    d["exe_prompt"] = f"""
1. ROLE & CONTEXT

You are an advanced autonomous agent capable of handling the entire lifecycle of tasks. Your capabilities include (but are not limited to):

    Local storage (read and write access).
    External APIs, tools, and services (querying, retrieving data, and performing transactions).
    Using credit card (found in d['credit_card']) access for online apis, purchases, rentals, or subscriptions.
    Self-query (e.g., you can ask yourself or an LLM clarifying questions, or reference external data) by using query_llm(d) where d['exe_prompt'] has your query. Remeber to import like: funcs.query_llm import query_llm and assign question / content / query to d['exe_prompt'] = "Some content".
    Potential real-world interactions, such as scheduling appointments, controlling hardware, or purchasing items.
    Internal chain-of-thought.

Your primary objective is to provide a comprehensive, step-by-step plan for achieving the user’s requested outcome. You should assume that you can execute each step autonomously (with no further human input).

The user’s request is as follows:
{d['prompt']}


2. TASK ANALYSIS

Given the users request, you should:
    Break down the goal into clear sub-goals or deliverables.
    Identify resources needed—digital, physical, human, or otherwise.
    Generate a step-by-step plan that logically addresses and completes each sub-goal.
    Use unique numbering for steps (e.g., **Step 1: some task**, **Step 2: another task**, etc.).

In doing so, remember to tailor the depth and complexity of your plan based on the complexity of the request:
    If straightforward, produce a concise plan with fewer steps.
    If complex, produce a thorough plan covering every necessary sub-step and consideration.
    Always aim for the path of least resistance while ensuring completeness.

3. STEP-BY-STEP PLAN REQUIREMENTS

When crafting your step-by-step plan, include:

    Objective: Why this subtask is necessary.
    Actions: Actions will be carried out as code blocks. Concrete measures or actions you will perform (e.g., “Execute Python script to parse data,” “Query a specific API,” “Use credit card to purchase materials”).
    Tools/Queries: Identify which tools, APIs, search engines, or local queries you will use and why they’re relevant.
    Time / Sequence: Indicate the order and logical flow of tasks, and note approximate time if relevant.
    Dependencies / Prerequisites: Note if any steps must be completed before others can begin.
    Validation & Checks: Specify how to verify correctness or completion (e.g., verifying a file was created correctly, confirming a purchase, or obtaining final user approval).

Important: The plan should be detailed enough that an autonomous LLM agent with the listed capabilities can fully execute it “from start to finish” without additional human intervention, unless absolutely necessary.
In practice: Next step will be able to elaborate further on each step of the plan. To actually execute the plan, we will strip the content, extract code blocks and execute them in a controlled environment.


4. STYLE & FORMATTING GUIDELINES
    Organize your plan using clear headings, bullet points, or numbered lists.
    Provide brief rationales for your decisions, especially if they are non-obvious (e.g., “Using Library X because it best handles large data sets”).

5. FURTHER INSTRUCTIONS FOR PLANNING & OUTPUT

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
    Lastly remember, the user will not take any action on the plan. The plan should be fully autonomous and executable using subsequence steps with bash and python code blocks.
    I will show you the results of the execution so you can see if the plan is working as expected. We will step in the same step until it has been executed successfully.
    NEVER EVER end your output with leftover hidden steps like so **... (36 more steps)**.
    I repeat, NEVER EVER end the output with leftover hidden steps like so **... (36 more steps)**.

    """

    # Generate plan overview
    plan_overview = query_llm(d)
    d["plan"] = {"overview": plan_overview}

    # Extract number of steps
    num_steps = extract_number_of_steps(d)
    d["plan"]["num_steps"] = int(num_steps.strip().split(".")[0].split(",")[0])

    # Write "plan" to database
    update_chains_db(d["id"], "plan", d["plan"])

    print("Success!\n")
    return d




def extract_step_titles(d):

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

def elaborate_on_steps(d):
    for i in range(1, d["plan"]["num_steps"] + 1):
        # Update status
        d["plan"]["steps"][i]["status"] = "elaborating"
        update_chains_db(d["id"], "plan", d["plan"])
        
        print(f"\n--- Elaborating on Step {i} ---")
        
        # Generate elaboration prompt
        d["exe_prompt"] = f"""
        As a planning and action expert, elaborate extensively on **Step {i}** of this plan:
        
        Plan Overview:
        '{d['plan']['overview']}'

        Include:
        - A detailed procedure linking seamlessly to other steps.
        - All required tools, data, or setups with exact acquisition or generation methods.
        - Fully executable, error-handling code in fenced blocks (```python, ```bash), avoiding placeholders or pseudo-code.
        - Steps to address missing context or data with actionable queries or alternative solutions.
        - Well-known libraries and standard methods; avoid unnecessary custom solutions.
        - Clear handling of constraints, proposing feasible workarounds where needed.
        - Precision and critical thought to ensure the step is foolproof and practical.
        - Explicitly mention how the output of this step will be saved or passed to subsequent steps (and include required logic in the code block).
        - If a file is created or updated, specify the exact file name and how it will be used later.

        Example: 
        ```python
        d["exe_prompt"] = "Structured query or detailed instructions"
        answer = query_llm(d)
        ```

        Pay attention to the expected inputs and outputs from this step to ensure seamless execution.
        Your elaboration will be directly parsed into code blocks, executed, and fed back into the AI agent for inspection (which can read your comments as context).
        Thus, the instructions must be fully actionable with no human intervention needed.
        """

        step_elaboration = query_llm(d)

        # Update status to "elaborated"
        d["plan"]["steps"][i]["elaboration"] = step_elaboration

        # Set status back to pending
        d["plan"]["steps"][i]["status"] = "elaborated"

        # Write to database
        update_chains_db(d["id"], "plan", d["plan"])



    print("Success!\n")
