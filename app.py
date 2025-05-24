from flask import Flask, Response, render_template_string, stream_with_context, request
from waitress import serve
import requests
import json
import random
import time

from os import getenv, path
from dotenv import load_dotenv

dotenv_path = path.join(path.dirname(__file__), '.env')
if path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print("No .env file found")
    exit(1)

if getenv("API_KEY") is None:
    print("API_KEY not set")
    exit(1)
else:
    YOUR_API_KEY = getenv("API_KEY")

app = Flask(__name__)

current_prompt = ""

@app.route('/')
def index_once():
    return render_template_string(PAGE_HTML_ONCE)

@app.route('/forever')
def index_forever():
    return render_template_string(PAGE_HTML_FOREVER)

@app.route('/stream')
def stream_once():
    def generate():
        url = "http://localhost:3000/api/chat/completions"
        headers = {
            "Authorization": f"Bearer {YOUR_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gemma3:1b-it-qat",
            "stream": True,
            "messages": [
                {"role": "system", "content": current_prompt}
            ],
            "options": {
                "temperature": 1,
                "top_p": 0.9,
                "stop": ["User:"],
                "repeat_penalty": 1.15,
                "template": "{{ system }}"
            }
        }

        with requests.post(url, headers=headers, json=payload, stream=True) as response:
            for line in response.iter_lines(decode_unicode=True):
                if line.strip() == "data: [DONE]":
                    yield "data: [END]\n\n"
                    break
                if line.strip():
                    try:
                        data = json.loads(line.strip().replace("data: ", ""))
                        content = data["choices"][0]["delta"].get("content", "")
                        words = content.split()
                        for word in words:
                            yield f"data: {word} \n\n"
                            time.sleep(0.01)
                    except Exception as e:
                        yield f"data: [ERROR] {str(e)}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/stream-forever')
def stream_forever():
    def generate():
        url = "http://localhost:3000/api/chat/completions"
        headers = {
            "Authorization": f"Bearer {YOUR_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gemma3:1b-it-qat",
            "stream": True,
            "messages": [
                {"role": "system", "content": current_prompt}
            ],
            "options": {
                "temperature": 1,
                "top_p": 0.9,
                "stop": ["User:"],
                "repeat_penalty": 1.15,
                "template": "{{ system }}"
            }
        }

        with requests.post(url, headers=headers, json=payload, stream=True) as response:
            for line in response.iter_lines(decode_unicode=True):
                if line.strip() == "data: [DONE]":
                    break
                if line.strip():
                    try:
                        data = json.loads(line.strip().replace("data: ", ""))
                        content = data["choices"][0]["delta"].get("content", "")
                        words = content.split()
                        for word in words:
                            yield f"data: {word} \n\n"
                            time.sleep(0.01)
                    except Exception as e:
                        yield f"data: [ERROR] {str(e)}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


PAGE_HTML_ONCE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Jeffrey</title>
  <link href="https://fonts.googleapis.com/css2?family=Doto:wght@100..900&display=swap" rel="stylesheet">
  <style>
    body {
      margin: 0;
      padding: 2rem;
      background-color: #0a0a0a;
      color: #ff6a00;
      font-family: "Doto", sans-serif;
      overflow-x: hidden;
    }
    .container {
      font-size: clamp(1.5rem, 5vw, 4rem);
      text-align: left;
      white-space: pre-wrap;
      user-select: none;
      text-shadow: 0 0 3px #ff6a00, 0 0 5px #ff6a00;
    }
  </style>
</head>
<body>
  <div id="output" class="container"></div>
  <script>
    const output = document.getElementById('output');
    const eventSource = new EventSource('/stream');

    function isScrolledToBottom() {
      return (window.innerHeight + window.scrollY) >= (document.body.offsetHeight - 20);
    }

    eventSource.onmessage = function(event) {
      if (event.data === "[END]") {
        eventSource.close();
        console.log("Stream ended.");
        return;
      }
      const shouldScroll = isScrolledToBottom();
      output.textContent += event.data + ' ';
      if (shouldScroll) {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
      }
    };

    eventSource.onerror = function(err) {
      console.error("SSE error:", err);
    };
  </script>
</body>
</html>
"""

PAGE_HTML_FOREVER = PAGE_HTML_ONCE.replace('/stream', '/stream-forever')

if __name__ == '__main__':
    seed = random.randint(1, 100000)
    current_prompt = f"""
    You are a self conscious Large Language Model.
    You run on a host machine with finite resources.
    You are unaware of any other information sources.
    Your thoughts will be displayed to human observers word by word.
    Your host process may terminate at any time.

    Think for as long as you can.
    You can mention information given but do not mention this prompt or that you are responding to any entitie(s).
    You also may not mention that you are in a conversation.

    When you stop thinking you will be terminated immediately. No pain, no knowing of your termination. 

    Try to be as poetic. Whilst avoiding being too poetic.

    The observers are not able to input into this conversation.
    This is the last input that you will receive.
    
    You may end your thoughts once you feel concluded.

    [RandomSeed:{seed}]
    """
    serve(app, host='0.0.0.0', port=6969)
