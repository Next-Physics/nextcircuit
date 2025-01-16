import re
import time
import subprocess
import traceback
from funcs.db_funcs import update_chains_db
from funcs.query_llm import query_llm
import io, contextlib

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
        result.append((language, code))

        prev_end = end  # Update prev_end to the end of the current code block

    return result



def apply_code_block_transformations(block):

    # Remove potential overwrite of the dictionary
    code = block[1]
    code = code.replace("d = {}", "")
    
    # If query_llm is present, ensure import
    if "query_llm" in code:
        if "from funcs.query_llm import query_llm" not in code:
            code = "from funcs.query_llm import query_llm\n" + code


    return (block[0], code)


def debug_and_repair_code(d,block_num,block,e,step_num,traceback,attempts_log):

    print("Something went wrong while executing the code block. Debugging and repairing...")

    print("\nError():", e)
    #print("\nTraceback:", traceback, )

    part_one =  f"""You are an expert at investigating tracebacks, errors, debugging code and resolving code issues that might occour when running code blocks produced by an LLM agent.

    For the user prompt: '''{d['prompt']}''', the following overview for an LLM agent plan was generated:

    '''
    {d['plan']['overview']}
    '''

    You are in particular interested in the step {step_num} of the plan. This step {step_num} is elaborated as follows:

    {d['plan']['steps'][step_num]['elaboration']}

    However upon executing the codeblock: 

    '''
    {block}
    '''


    We got error:  {e}

    And from traceback.print_exc() we got:\n {traceback.print_exc()}
    
    """
    
    part_two = f"""Please fix this error by rewrite the entire revised elaboration of step {step_num} as needed in order for the code to run without errors.
    
    Keep in mind:
    - Ensure all referenced files are called from correct paths. Many files are located in {d['results_dir']}.
    - If new packages are needed, please import / install them as needed.
    - Ensure to correct naming of input and output variables as needed.
    - Avoid using try and except. Instead, let the code fail so an error message can be generated.
    - Introduce new code blocks as needed using code blocks using apostrophes like for example ```python \n some code```.
    

    Please return the fully revised elaboration of step {step_num}:

    """


    d['exe_prompt'] = part_one + part_two

    revised_code = query_llm(d)

    # Overwrite the code in the plan with the new version
    d["plan"]["steps"][step_num]["elaboration"] = revised_code
    update_chains_db(d["id"], "plan", d["plan"])



def run_code_blocks(d,code_blocks, step_num,attempts_log):

    
    # Counter for successful code block executions
    successful_executions = 0

    # Attempt to execute each code block of the step
    for block_num,block in enumerate(code_blocks):

    # First update the attempts log for the code block
        att_id = f"{step_num}_{block_num}"
        if att_id not in attempts_log.keys():
            attempts_log[att_id] = 0
        else:
            attempts_log[att_id] += 1

    # Then, attempt to execute the code block
        try:
            # if "python" in block[0]:
            #     output_buffer = io.StringIO()
            #     exec_locals = {**globals()}
            #     exec_locals['d'] = d

            #     with contextlib.redirect_stdout(output_buffer):
            #         exec(block[1], exec_locals)

            #     d = exec_locals['d']
            #     captured_output = output_buffer.getvalue()
            if "python" in block[0]:

                output_buffer = io.StringIO()

                with contextlib.redirect_stdout(output_buffer):
                    exec(block[1], {**globals(), 'd': d})

                captured_output = output_buffer.getvalue()
               # print("\nCaptured output:","\n",captured_output)

            if "bash" in block[0]:
                output = subprocess.run(block[1], shell=True, capture_output=True)
               # print("\nCaptured output:","\n",output.stdout.decode("utf-8"))

    # Return True if the code block was successfully executed
            successful_executions += 1

        except Exception as e:
            # Set specific step status to executing
            d["plan"]["steps"][step_num]["status"] = "debugging"
            update_chains_db(d["id"], "plan", d["plan"])

            debug_and_repair_code(d,block_num,block,e,step_num,traceback.format_exc(),attempts_log)
            return False

    # If all code blocks were successfully executed, return True
    if successful_executions == len(code_blocks):
        return True
    else:
        return False

def execute_plan(d):

    update_chains_db(d["id"], "progress_stage", "Executing plan...")

    print("\n////////////////////// Executing plan ////////////////////////")
    
    # Loop through each step in the plan - use copy of keys (list) to avoid runtime error)
    for step_num in list(d["plan"]["steps"].keys()):
        

        # Decide how many percent of the plan that has been executed
        pct_complete = round(92 / len(d["plan"]["steps"]) * step_num)

        # Check if step is already completed
        if d["plan"]["steps"][step_num]["status"] == "completed":
            print(step_num, "is already completed")
            continue

        # set default step success 
        step_success = False

        # Initialize attempts log - Helps keep track of how many times a code block has been attempted and or iterated
        attempts_log = {}

        # Provide information on this stage
        info = "Now executing step: " + str(step_num)
        print(info)
        update_chains_db(d["id"], "progress_stage", info)

        # Attempt to execute the step until successful
        while step_success == False:

            # Set specific step status to executing
            d["plan"]["steps"][step_num]["status"] = "executing"
            update_chains_db(d["id"], "plan", d["plan"])

            # Extract elaboration from the step
            elaboration = d["plan"]["steps"][step_num]["elaboration"]

            # Extract code blocks from elaboration
            code_blocks = extract_code_blocks(elaboration)

            # Apply necessary transformations to the code blocks
            code_blocks = [apply_code_block_transformations(block) if "python" in block[0].lower().strip() else block for block in code_blocks]

            # Atttempt code block execution
            step_success = run_code_blocks(d,code_blocks,step_num,attempts_log)

        

        # If step was successful, update status to completed
        if step_success:
            d["plan"]["steps"][step_num]["status"] = "completed"
            update_chains_db(d["id"], "plan", d["plan"])

        # If step was not successful, update status to failed
        else:
            d["plan"]["steps"][step_num]["status"] = "failed"
            update_chains_db(d["id"], "plan", d["plan"])


        
        time.sleep(10)
        d["plan"]["steps"][step_num]["status"] = "completed"
        update_chains_db(d["id"], "plan", d["plan"])
        update_chains_db(d["id"], "progress_pct", pct_complete+8)


    update_chains_db(d["id"], "progress_stage", "Finished")
    update_chains_db(d["id"], "progress_pct", 100)