import re
from ollama import Client

def query_ollama(d):

        if "model" not in d:
                d["model"] = 'llama3.1:8b'
        
        host=f"""http://{d['local_ip']}:{d['port']}"""

        client = Client(host=host)

        response = client.chat(model=d["model"],
                                messages=[
                                {'role': 'user',
                                'content': d['exe_prompt']}]
                                )


        if d["model"] == 'marco-o1':
                output = response["message"]["content"].split("<Output>")[-1].split("</Output>")[0]
        else:
                output = response["message"]["content"]


        print(output)
 
        return output
        

