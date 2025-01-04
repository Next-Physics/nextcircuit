import re
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
        result.append({preceding_text: {language: code}})

        prev_end = end  # Update prev_end to the end of the current code block

    return result



def execute_plan(d):

    update_chains_db(d["id"], "progress_stage", "Executing plan...")

    for step in d["plan"]["steps"]:

        # Extract content from step
        content = step["content"]

        print("CONTENT IS: ", content)
        # Extract code blocks from content
        code_blocks = extract_code_blocks(content)
        print("--------------------------------------------------------------------")
        for block in code_blocks:
            print("BLOCK IS: ", block)

        print("____________________________________________________________________")

        # step["status"] = query_llm(d)
        # print("Step Status: ", step["status"])
        # print("")



#                "num_steps": "Number of steps",
#                "steps": [{"num": "Step Number",
#                           "content": "Step Content",
#                           "status": "Step Status"}]
    update_chains_db(d["id"], "progress_stage", "Finished")
    update_chains_db(d["id"], "progress_pct", 100)