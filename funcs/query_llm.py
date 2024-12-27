import re


def query_llm(d):

        if "model" not in d:
                d["model"] = 'llama3.1:8b'
        
        if "chatgpt" in d["model"]:
                import openai
                client = openai.OpenAI(api_key=d["api_key"])

                completion = client.chat.completions.create(
                model=d["model"],
                messages=[{
                        "role": "user",
                        "content": d["exe_prompt"]}]
                )

                output = completion.choices[0].message


        else:   
                from ollama import Client

                host=f"""http://{d['ip']}:{d['port']}"""

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
        

