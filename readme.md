# Grammar checking

#### How to use
- Make sure a python environment is set up with the right requirements (from `requirements.txt`)
- Execute `run.bat` or simply `uvicorn app.server:app --reload`
- Navigate to `http://127.0.0.1:8000/docs` in a browser
- Here you can use the built-in FastAPI tools to try grammar checking a sentence:
- Click the `/check` endpoint
- Click the `Try it out` button
- Input a sentence (e.g. "de beer eet een appel")
- Press `execute` to try out the command
- View the information on the response to see whether your sentence was flagged as correct or incorrect