import os
import sys
import json
import glob
import subprocess

import openai

SYSTEM_PROMPT = """
You are given a codebase_path and the content of a GitHub issue. 
Respond with the content of a patch file that will fix the issue. Do not describe your output.

Your output should look like this:

```
--- a/testfile.txt
+++ b/testfile.txt
@@ -1 +1 @@
-this is the original content
+this is the new content

```

and NOT like this:

```
diff --git a/testfile.txt b/testfile.txt
index 4157dda..7f0642a 100644
--- a/testfile.txt
+++ b/testfile.txt
@@ -1 +1 @@
-this is the original content
+this is the new content

```

Only respond with the content of the git patch that fixes the issue.
If the patch is wrong, you will receive the error that was generated.
You should generate an output that does the same thing as before, but 
does not cause the error.
"""


def issue_to_pr(codebase_path, issue_content):
    issue_data = json.loads(issue_content)

    codebase_content = ""
    files_to_load = os.listdir(codebase_path)

    while files_to_load:
        file_to_load = files_to_load.pop()
        print(f"Processing {file_to_load}...")
        
        if os.path.isdir(file_to_load) and ".git" != file_to_load:
            print(f"   is a dir")
            files_to_load += [f"{file_to_load}{os.path.sep}{filename}" for filename in os.listdir(f"{codebase_path}{os.path.sep}{file_to_load}")]
        
        elif os.path.isfile(file_to_load) and not "convert_issue_to_pr.py" in file_to_load and not "explain_pr.py" in file_to_load:
            print(f"   is a file")
            codebase_content += f"`{codebase_path}/{file_to_load}`:\n\n"
            with open(codebase_path + "/" + file_to_load, 'r') as code_file:
                codebase_content += f"```\n{code_file.read()}\n```\n\n"


    prompt = f"""
# Codebase

{codebase_content}

--------
# Issue: {issue_data["title"]}

{issue_data["body"]}

-------
# Patch to apply:

"""
    print("#---------#")
    print(prompt)
    print("#---------#")
    
    messages = [
        {"role": "system",  "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    for _ in range(3):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        reply = response["choices"][0]["message"]["content"]

        print("---------")
        print(reply)
        print("---------")

        with open("changes.patch", "w") as patch_file:
            patch_file.write(reply + "\n")

        apply_patch="patch -p1 < changes.patch"
        try:
            apply_command = subprocess.run(apply_patch, capture_output=True, shell=True, check=True)
            break
        except subprocess.CalledProcessError as exc:

            for rej in glob.iglob(os.path.join(codebase_path, '*.rej')):
                os.remove(rej)

            print("######################")
            print(os.listdir(codebase_path))
            print("######################")
            print(exc)
            print("######################")
            print(exc.stdout)
            print("######################")
            print(exc.stderr)
            print("######################")
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": f"# Error:\n{exc.stderr.decode('utf-8')}\n\n# Patch to apply:\n\n"})

    reply = reply.replace('"', "\"")  # Bash
    return reply


if __name__ == "__main__":
    openai.api_key = sys.argv[1]
    print(issue_to_pr(issue_content=sys.argv[2], codebase_path=sys.argv[3]))
