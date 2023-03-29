import os
import sys
import json
import subprocess
import openai

SYSTEM_PROMPT = """
You are a code assistant. You will be given a codebase and an issue. 
You should reply with a patch that will fix the issue.
Do not describe your output. Only output the git patch that fixes the issue. 
The output will be piped to a file and applied to the repository, so make sure the syntax is valid.
"""


def issue_to_pr(codebase, issue_content):
    issue_data = json.loads(issue_content)

    codebase_content = ""
    for file_to_load in os.listdir(codebase):
        if os.path.isfile(file_to_load) and not file_to_load == "convert_issue_to_pr.py":
            codebase_content += codebase + "/" + file_to_load + ":\n\n"
            with open(codebase + "/" + file_to_load, 'r') as code_file:
                codebase_content += f"```\n{code_file.read()}\n```\n\n"

    prompt = f"CODEBASE:\n\n{codebase_content}\n\nISSUE:\n\n{issue_data}\n\nPATCH:"

    for i in range(10):
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
                {"role": "system",  "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        reply = response["choices"][0]["message"]["content"]
        
        with open("changes.patch", "w") as patch_file:
            patch_file.write(reply)

        apply_patch="git apply --ignore-space-change --ignore-whitespace changes.patch"
        try:
            apply_command = subprocess.run(apply_patch, shell=True, check=True)
            break
        except:
            pass
        print("FAILED!")

    reply = reply.replace('"', "\"")  # Bash
    return reply


if __name__ == "__main__":
    openai.api_key = sys.argv[1]
    print(issue_to_pr(issue_content=sys.argv[2], codebase=sys.argv[3]))
