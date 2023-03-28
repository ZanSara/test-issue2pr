import sys
import json
import openai


def issue_to_pr(issue_content):
    issue_data = json.loads(issue_content)

    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "system", "content": "You are a helpful assistant. Provide a very concise answer."},
            {"role": "user", "content": "How do people greet each other in French?"},
        ]
    )
    reply = response["choices"][0]["message"]["content"]
    reply = reply.replace('"', "\"")  # Bash
    return reply


if __name__ == "__main__":
    openai.api_key = sys.argv[1]
    print(issue_to_pr(issue_content=sys.argv[2]))
