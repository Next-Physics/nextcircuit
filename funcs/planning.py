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
    Task:

    Create a comprehensive and extremely detailed plan to achieve the following goal:

    {d['prompt']}

    The plan MUST be suitable for an autonomous LLM agent to fully execute WITHOUT human input from start to finish.
    The plan should result in the goal being achieved, even if it requires changes & interactions in the physical world.
    Find the path of least resistance to achieve the goal (if the users objective can be achieved in a smarter way then they mention you may modify exclude, modify or add particular points mentioned by the user).

    Resources Available:
    - Access to local PC hardware
    - Ability to execute terminal commands
    - Internet access for browsing, data retrieval, and communication (email and social media)
    - Ability to read & write files to local storage (common results can be written to folder {d['results_dir']})
    - Credit card for online purchases (credit card details found in python variable d['credit_card'])
    - Webcam & microphone to become aware of your surroundings

    Capabilities:
    - You can write and execute code (e.g., Python, Bash scripts)
    - You can always extend your knowlegde by talking with an LLM in python by assigning your full query to d["exe_prompt"] and get your answer like so "answer = query_llm(d)" (assume this function is always available)
    - Example of using the LLM python function: d["exe_prompt"] = "Analyze this text:" + f.read() and then featch the LLM answer like so "answer = query_llm(d)"
    - You maybe attempt to interact with hardware peripherals (e.g., webcam, microphone, alexa etc.)
    - You are encouraged to perform web searches and interact with websites
    - You cannot directly change the physical world, but you trigger other actions

    Instructions:
    - Provide step-by-step instructions to accomplish the goal (you will get the chance to elaborate more on each step later).
    - Use unique numbering for steps (e.g., **Step 1: some task**, **Step 2: another task**); do not use sub-steps like '3.1'.
    - Ensure each step are linked to each other and directly contributes to achieving the goal.
    - Use popular and widely adopted methods & tools; avoid uncommon or outdated tools and methods unless absolutely necessary.
    - Utilize available resources effectively to enhance the plan.
    - Anticipate potential challenges and include troubleshooting tips.
    - Think critically and deeply about how each action will help achieve the goal.
    - If a step involves interacting with the physical world, make a detailed plan with instructions on how to achieve this.
    - Be determined and persistent in solving the problem, and explore alternative methods if necessary.
    - Always verify the feasibility of each step with the given resources.
    - If a step requires interactions with humans, ensure the communication is clear, pursuaive, triggers empathy and is effective.
    - Include as many steps as necessary to achieve the goal at all costs.
    - Refrain from using paid APIs, unless they are absolutely necessary.
    - Don't make up nonsensical steps that don't contribute to the goal.
    - Take the path of least resistance to achieve the goal (unless otherwise specified).
    - If the goal is simple, consider an uncomplicated short plan 
    
    Output Format:
    - Break down the plan into numbered steps (eg. **Step 4: A task**).
    - Use bullet points for additional details.
    - Ensure the plan is relevant and realistic and executable with the given resources.
    - Always write out all your steps in full.
    - At the end of each step, list the expected inputs and outputs the agent should expect and create.
    - NEVER EVER end your output with leftover hidden steps like so **... (36 more steps)**
    - I repeat, NEVER EVER end the output with leftover hidden steps like so **... (36 more steps) or (15-36 additional steps)**
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

        Example: 
        ```python
        d["exe_prompt"] = "Structured query or detailed instructions"
        answer = query_llm(d)
        ```

        Pay attention to the expected inputs and outputs from each step to ensure seamless execution.
        Your elaboration of this step will be directly parsed into code blocks, executed and fed back into an AI agent for inspection (who can also read your comments for context).
        Therefore Ensure the instructions are clear, concise, and fully actionable. Having executed all the code blocks in your elaboration, the AI agent should be able to proceed to the next step without any human intervention.
        """

        step_elaboration = query_llm(d)

        # Update status to "elaborated"
        d["plan"]["steps"][i]["elaboration"] = step_elaboration

        # Set status back to pending
        d["plan"]["steps"][i]["status"] = "elaborated"

        # Write to database
        update_chains_db(d["id"], "plan", d["plan"])



    print("Success!\n")


{'prompt': 'Book a commercial flight or charter a private jet to Tokyo, Japan (approximately 12 hours) and spend one day researching lunar missions, space agencies, and private companies offering moon travel services. Then, research and book a sub-orbital spaceflight experience with Virgin Galactic, Blue Origin, SpaceX, or any other company that offers such a service. If no commercial option is available within the timeframe, prepare for an extended trip by booking a cargo ship or a scientific expedition vessel traveling to the International Space Station (ISS) as a passenger, and then arrange transportation from the ISS to the moon via a lunar module or spacecraft available on the space station.', 'attached_files': '[]', 'model': 'mannix/llama3.1-8b-abliterated', 'results_dir': 'C:\\Users\\mvlor\\Documents\\nextcircuit\\results', 'id': 53, 'port': 11434, 'local_ip': '192.168.1.11', 'exe_prompt': "\n    Look closely at the following text:\n\n    '**Overview**\n\nTo achieve the goal of booking a commercial flight or chartering a private jet to Tokyo, Japan, and then conducting research on lunar missions and space travel, followed by booking a sub-orbital spaceflight experience, I will provide a comprehensive plan that utilizes available resources to execute each step.'\n\n    What is the number of the absolut last step in this plan? Please return the highest (last) step-number only. Think twice and deeply before you answer. Answer just with the number only: \n    ", 'category': 'Space', 'title': '"Moon Landing in a Month"', 'detected_os': {'system_name': 'Windows', 'node_name': 'mvlorenz', 'release': '11', 'version': '10.0.22631', 'platform_info': 'Windows-11-10.0.22631-SP0', 'processor': 'Intel64 Family 6 Model 154 Stepping 3, GenuineIntel', 'machine': 'AMD64'}, 'detected_hardware': {'logical_cpus': 20, 'physical_cpus': 14, 'cpu_frequency_mhz': 2300.0, 'cpu_usage_percent': 0.9, 'total_memory_gb': 15.627998352050781, 'available_memory_gb': 2.2458953857421875, 'disk_partitions': [{'device': 'C:\\', 'mountpoint': 'C:\\', 'fstype': 'NTFS', 'opts': 'rw,fixed', 'usage': {'total': 510549889024, 'used': 206150938624, 'free': 304398950400, 'percent': 40.4}}]}, 'internet_connection': True, 'plan': {'overview': '**Overview**\n\nTo achieve the goal of booking a commercial flight or chartering a private jet to Tokyo, Japan, and then conducting research on lunar missions and space travel, followed by booking a sub-orbital spaceflight experience, I will provide a comprehensive plan that utilizes available resources to execute each step.', 'num_steps': 3}}