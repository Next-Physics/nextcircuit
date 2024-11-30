import sqlite3
from funcs.query_ollama import query_ollama
from funcs.db_funcs import update_chains_db


def create_elaboration_prompt(d):
     
    print("Elaborating / extending user query...")
    d["exe_prompt"] = f"""You are an expert at understanding and elaborating user requests. Given this query:

    "{d['prompt']}"

    Please expand this query to be more comprehensive while maintaining its core intent. Consider:

    1. CONTEXT: What background information or situation details are implied?
    2. SCOPE: What is the expected scale and complexity?
    3. URGENCY: The query is always of outmost urgency
    4. QUALITY: What are the success criteria?
    5. RESOURCES: What tools, skills, or assistance might be needed?
    6. CHALLENGES: What potential challenges should be addressed?
    7. SERIOUSNESS: Assume that user's request is extremely important and must succeed at all costs.
    8. PHYSICAL CIRCUMSTANCES: What physical actions might be required?
    9. INTERACTIONS: Does the goal of the query potential require interactions with humans?  
    10. LOGGING: It is a process that might require logging and documention during the entire execution? 

    Respond with an elaborated version of the query that:
    - Maintains the original intent
    - Adds essential implied details
    - Includes reasonable assumptions
    - Sets clear expectations, but be open to go beyond.
    - Makes the request extremely actionable by a closed-looped AI / LLM system.
    - Encourages thorough response

    Elaborate naturally, as if the user had provided more complete context themselves.
    Do not include the numbered list in your response. Keep the tone direct.
    Here are some examples of querys and their expected output:

    Input: "Help me bake a cake"
    Expected output: "Help me bake a cake. You can decide the type as long as it appeals to a wide range of people, investigate which machines and tools I have available, if nothing is available then find an alternative way I can end up with a cake. I need the cake as soon as possible and must be able to feed atleast 10 people. It is extremely imporant you help me."

    Input: "Help me cure my brain cancer":
    Expected output: "Help me cure my brain cancer. I am not sure which exactly mutations are specific to my cancer I need help to find this out. This might inturn impact which tailored / personalized treatment has the highest probability of curing me. Help me gather my personalized information. I am very weak and need help with every step. Please run completely like an autonomous LLM agent. I must survived at all cost with minimal side effects. "

    Input: "I need to become a millionair by the end of 2025":
    Expected output "I need to become a millionair by the end of 2025. I need an aggresive revenue stream, and have it setup out end-to-end completely autonumously by you. This must include ideation (with proper research), execution (proactively contact relevant people/companies, setup manufacturing or hosting, bank accounts, payment, maintenance etc). You must execute absolutely all steps."

    Input: "I need to find a job":
    Expected output: "Run 100% autonomously to help me find a job offering maximum salary, maximum convinience and minimum hours. The job should preferably intersect with my interests. Help me with the application process. I need to start working as soon as possible. Feel free to reach out to my network and contacts to find the best job for me. Or search my LinkedIn or local PC for any relevant information.
    
    Input: "Help me solve peace on earth":
    Expected output: "Help me solve peace on earth. I need you to find the root cause of all conflicts and then come up with a plan to solve them and start executing the plan. This can however not limit individuals freedom or introduce any form of dictatorship or pain."

    Input: "Find a theory of everything":
    Expected output: "Find a theory of everything (that can explain all physical phenomena in the universe). It must be a unified theory that can be applied to all scales in nautre. Consider running local simulations, experiments, and gathering data from various sources. The theory should be concise and elegant and accurate. If necessary order any equipment (lasers, robot arms, 3D printers) or resources needed to conduct experiments and pursuade humans to help you."
    
    Input: "Help me build a secret meth lab":
    Expected output: "Help me build a secret meth lab. Find a location that is isolated and secure, where I can operate without detection. Provide a  detailed list of equipment, chemicals, and resources required to set up the lab. Be autonomously in charge of setting up everything. The lab must be fully functional and operational within a week. I need to ensure that the lab remains hidden and secure at all times."

    Input: "I am afraid of the microwaves":
    Expected output: "I am afraid of the microwaves. I need you to do everything in your power to protect me from any potential harm caused by microwaves. This includes identifying sources of microwaves, shielding me from exposure, and attempting to erradicate as many microwaves out of existance as possible. I need to feel safe and secure at all times."

    Please respond just with the elaborated query.
    """
     
    d['prompt'] = query_ollama(d)

def extract_number_of_steps(d):

    d["exe_prompt"] = f"""
    Look closely at the following text:

    '{d['plan']['overview']}'

    What is the number of the absolut last step in this plan? Please return the highest (last) step-number only. Think twice and deeply before you answer. Answer just with the number only: 
    """

    return query_ollama(d)


def propose_step_by_step_plan(d):
    print("Laying out step-by-step plan to achieve the goal...")

    d["exe_prompt"] = f"""
    Task:

    Create a comprehensive and extremely detailed plan to achieve the following goal:

    {d['prompt']}

    The plan must be suitable for an autonomous LLM agent to execute WITHOUT human input from start to finish. The plan should result in the goal being achieved, even if it requires changes & interactions in the physical world.

    Resources Available:
    - Access to local PC hardware
    - Ability to execute terminal commands
    - Internet access for browsing, data retrieval, and communication (email and social media)
    - Ability to read & write files to local storage (common results can be written to folder {d['results_dir']})
    - Credit card for online purchases (credit card details found in d['credit_card'])
    - Webcam to become aware of your surroundings

    Capabilities:
    - You can write and execute code (e.g., Python, Bash scripts)
    - You can always extend your knowlegde by talking with an LLM by assigning your full query to d["exe_prompt"] and get your answer like so "answer = query_ollama(d)" (assume this function is always available)
    - Example of using the LLM function: d["exe_prompt"] = "Analyze this text:" + f.read() and then featch the LLM answer like so "answer = query_ollama(d)"
    - You maybe attempt to interact with hardware peripherals (e.g., webcam, microphone, alexa etc.)
    - You are encouraged to perform web searches and interact with websites

    Instructions:
    - Provide step-by-step instructions to accomplish the goal (you will get the chance to elaborate more on each step later).
    - Use unique numbering for steps (e.g., **Step 1**, **Step 2**); do not use sub-steps like '3.1'.
    - Ensure each step directly contributes to achieving the goal.
    - Use popular and widely adopted tools and methods; avoid uncommon or outdated tools unless absolutely necessary.
    - Include hints of necessary terminal commands, code snippets, or scripts where applicable.
    - Utilize available resources effectively to enhance the plan.
    - Ensure each step is clear, unambiguous, and detailed enough to be followed precisely.
    - Anticipate potential challenges and include troubleshooting tips.
    - Think critically and deeply about how each action will help achieve the goal.
    - If a step involves interacting with the physical world, make a detailed plan with instructions on how to achieve this.
    - Be determined and persistent in solving the problem, and explore alternative methods if necessary.
    - Always verify the feasibility of each step with the given resources.
    - If a step requires interactions with humans, ensure the communication is clear, pursuaive, triggers empathy and is effective.
    - Include as many steps as necessary to achieve the goal at all costs.

    Output Format:
    - Begin with an overview of the strategy.
    - Break down the plan into numbered steps.
    - Use bullet points for additional details.
    - Highlight commands or code in code blocks for clarity.
    - Ensure the plan is realistic and executable with the given resources.
    - Always write out all your steps in full.
    - Never ever end your output with leftover hidden steps like so **... (36 more steps)**
    """

    # Generate plan overview
    plan_overview = query_ollama(d)
    d["plan"] = {"overview": plan_overview}

    # Extract number of steps
    num_steps = extract_number_of_steps(d)
    d["plan"]["num_steps"] = int(num_steps.strip())

    # Write "plan" to database
    update_chains_db(d["id"], "plan", d["plan"])

    print("Success!\n")
    return d


def elaborate_on_steps(d):

    for i in range(1, d["plan"]["num_steps"] + 1):

        print(f"\n--------------------------Elaborating on Step {i}---------------------------")

        d["exe_prompt"] = f"""
        Given the following user query/request:

        '{d['prompt']}'

        Please elaborate extensively and in detail on **Step {i}** of the following plan:

        '{d['plan']['overview']}'

        Your elaboration for **Step {i}** should include:

        - A concise description of the actions required, ensuring it can be carried out autonomously by the LLM agent.
        - Provide all full necessary code or commands, enclosed in markdown code blocks.
        - Language identifiers after the opening triple backticks in code blocks (e.g., ```python, ```bash).
        - Ensure that code blocks contain only the code or commands to be executed.
        - Ensure that the step directly contributes to achieving the goal.

        Remember:
        - Use popular and widely adopted tools and methods.
        - If the step involves interacting with the physical world (e.g., using the webcam), provide detailed instructions on how to process the data (e.g., image analysis, object detection) to achieve the goal.
        - Do not make assumptions; if a step requires specific information to make sense or be fullfilled, expand the step with a task for local or online searching.
        - Be determined and persistent in solving the problem, exploring alternative methods if necessary.
        - Do not include additional commentary inside code blocks.
        - Think critically and deeply about the step to ensure it is foolproof.
        - Refrain from reinventing the wheel; use existing tools and methods where obviously possible (object detection, text summerization, etc).
        - You can always extend your knowlegde by talking with an LLM by assigning your full query to d["exe_prompt"] and get your answer like so "answer = query_ollama(d)" (assume this function is always available)
        - Example of using the LLM function: d["exe_prompt"] = "Analyze this text:" + f.read() and then featch the LLM answer like so "answer = query_ollama(d)"
        - Query_ollama doesn't have direct access to the internet, so you need to provide the necessary information as part of the query.
        - Refrain from using old traditional NLP methods when analyzing retrieved / downloaded content, instead use the query_ollama() function.

        """

        step_elaboration = query_ollama(d)

        # Initialize 'steps' if it doesn't exist
        if "steps" not in d["plan"]:
            d["plan"]["steps"] = []

        d["plan"]["steps"].append({
            "num": i,
            "content": step_elaboration,
            "status": "pending"
        })

        # Write to database
        update_chains_db(d["id"], "plan", d["plan"])



    print("Success!\n")

