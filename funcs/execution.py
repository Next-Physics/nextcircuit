import re
import time
import traceback
from funcs.db_funcs import update_chains_db
from funcs.query_llm import query_llm

def extract_code_blocks(content):

    # Regular expression pattern to match code blocks with their language
    code_block_pattern = re.compile(
        r'```(?P<language>\w+)\n(?P<code>[\s\S]*?)```', re.MULTILINE
    )

    result = []
    prev_end = 0  # Keeps track of the end position of the last code block

    for match in code_block_pattern.finditer(content):
        start, end = match.span()
        language = match.group('language')
        code = match.group('code')

        # Extract preceding text, excluding previous code blocks
        preceding_text = content[prev_end:start].strip()

        # Append the extracted information to the result list
        result.append({language: code})

        prev_end = end  # Update prev_end to the end of the current code block

    return result



def apply_code_block_transformations(block):

    # Remove potential overwrite of the dictionary
    block = block.replace("d = {}", "")
    
    # If query_llm is present, ensure import
    if "query_llm" in block:
        if "from funcs.query_llm import query_llm" not in block:
            block = "from funcs.query_llm import query_llm\n" + block


def run_code_block(block, step_num):

    try:
        if python in block.keys():
            exec(block, globals())

        if language == "bash":
            output = subprocess.run(block, shell=True, capture_output=True)
            print(output.stdout.decode("utf-8"))

    except Exception as e:

        d['exe_prompt'] = f"""You are an expert at investigating tracebacks, errors, debugging code and resolving code issues that might occour when running an LLM agent.

        As part of step {step_num} in the following plan..

        '''
        {d['plan']['overview']}
        '''

        For step {step_num},
        I attempted to execute the following code block:

        '''
        {block}
        '''

     
        Error in code block:  {e}
        The traceback.format_exc() {traceback.format_exc()}
        
        Please return the fully revised / resolved code block ready for execution. Output ONLY the code as described. 
        """ 


def execute_plan(d):

    update_chains_db(d["id"], "progress_stage", "Executing plan...")

    for step_num,value in d["plan"]["steps"].items():
        
        # ### Provide information on this stage
        info = "Now executing step: " + str(step_num)
        update_chains_db(d["id"], "progress_stage", info)

        d["plan"]["steps"][step_num]["status"] = "executing"
        update_chains_db(d["id"], "plan", d["plan"])

        elaboration = value["elaboration"]

        # Extract code blocks from elaboration
        code_blocks = extract_code_blocks(elaboration)

        # Apply necessary transformations to the code blocks
        code_blocks = [apply_code_block_transformations(block) if "python" in block.keys() else block for block in code_blocks]


        for block in code_blocks:
            run_code_block(block,step_num)

        
        time.sleep(10)
        d["plan"]["steps"][step]["status"] = "completed"
        update_chains_db(d["id"], "plan", d["plan"])



    # update_chains_db(d["id"], "progress_stage", "Finished")
    # update_chains_db(d["id"], "progress_pct", 100)