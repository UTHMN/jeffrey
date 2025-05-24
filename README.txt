Simple server, uses flask, sse and waitress

/ = run ai, stop when ai stops
/forever = run ai forever
/stream = sse stream
/stream-forever = sse stream forever

API_KEY is required from open-webui (self hosted), may port to ollama or anthropic later.

run with `python3 app.py`

inspired by https://www.youtube.com/watch?v=7fNYj0EXxMs - rootkid