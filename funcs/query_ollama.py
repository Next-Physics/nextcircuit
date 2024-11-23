from ollama import Client

def query_ollama(d):

        if "model" not in d:
                d["model"] = 'llama3.1:8b'

        client = Client(host=f"""http://{d['local_ip']}:{d['port']}""")

        response = client.chat(model=d["model"], messages=[
        {'role': 'user',
        'content': d['prompt']}]
        )

        # options={"stop":[f"| {no_of_days+1}  |"]}
        output = response["message"]["content"]
        return output