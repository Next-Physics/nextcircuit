from funcs.query_ollama import query_ollama

def propose_step_by_step_plan(d):

    d["exe_prompt"] = f"""
    Task:

    Create an elaborate and extremely detailed plan to achieve the following goal:

    {d['prompt']}

    Resources Available:

    Access to local PC hardware
    Ability to execute terminal commands
    Internet access for browsing and data retrieval

    Instructions:

    Provide step-by-step instructions to accomplish the goal.
    Include any necessary terminal commands, code snippets, or scripts.
    Utilize available resources effectively to enhance the plan.
    Ensure each step is clear, unambiguous, and detailed enough to be followed precisely.
    Anticipate potential challenges and include troubleshooting tips.

    Output Format:

    Begin with an overview of the strategy.
    Break down the plan into numbered steps.
    Use bullet points for sub-steps or additional details.
    Highlight commands or code in code blocks for clarity.
    Conclude with a summary of the expected outcome.

    """

    first_draf = query_ollama(d)
    print(first_draf)


