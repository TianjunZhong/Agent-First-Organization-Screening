import os
import json
import argparse
import time
import logging
import subprocess
import signal
import atexit

from langchain_openai import ChatOpenAI

from agentorg.utils.utils import init_logger
from agentorg.orchestrator.orchestrator import AgentOrg
from create import API_PORT
from agentorg.utils.model_config import MODEL

process = None  # Global reference for the FastAPI subprocess

def terminate_subprocess():
    """Terminate the FastAPI subprocess."""
    global process
    if process and process.poll() is None:  # Check if process is running
        logger.info(f"Terminating FastAPI process with PID: {process.pid}")
        process.terminate()  # Send SIGTERM
        process.wait()  # Ensure it stops
        logger.info("FastAPI process terminated.")

# Register cleanup function to run on program exit
atexit.register(terminate_subprocess)

# Handle signals (e.g., Ctrl+C)
signal.signal(signal.SIGINT, lambda signum, frame: exit(0))
signal.signal(signal.SIGTERM, lambda signum, frame: exit(0))


def get_api_bot_response(args, history, user_text, parameters):
    data = {"text": user_text, 'chat_history': history, 'parameters': parameters}
    orchestrator = AgentOrg(config=os.path.join(args.input_dir, "taskgraph.json"))
    result = orchestrator.get_response(data)

    return result['answer'], result['parameters']


def start_apis():
    """Start the FastAPI subprocess and update task graph API URLs."""
    global process
    command = [
        "uvicorn",
        "agentorg.orchestrator.NLU.api:app",  # Replace with proper import path
        "--port", API_PORT,
        "--host", "0.0.0.0",
        "--log-level", "info"
    ]

    # Redirect FastAPI logs to a file
    with open("./logs/api.log", "w") as log_file:
        process = subprocess.Popen(
            command,
            stdout=log_file,  # Redirect stdout to a log file
            stderr=subprocess.STDOUT,  # Redirect stderr to the same file
            start_new_session=True  # Run in a separate process group
        )
    logger.info(f"Started FastAPI process with PID: {process.pid}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', type=str, default="./examples/test")
    parser.add_argument('--model', type=str, default=MODEL["model_type_or_path"])
    parser.add_argument('--log-level', type=str, default="WARNING", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    args = parser.parse_args()
    os.environ["DATA_DIR"] = args.input_dir
    MODEL["model_type_or_path"] = args.model
    log_level = getattr(logging, args.log_level.upper(), logging.WARNING)
    logger = init_logger(log_level=log_level, filename=os.path.join(os.path.dirname(__file__), "logs", "agentorg.log"))

    # Initialize NLU and Slotfill APIs
    start_apis()
        
    history = []
    params = {}
    config = json.load(open(os.path.join(args.input_dir, "taskgraph.json")))
    user_prefix = "USER"
    worker_prefix = "ASSISTANT"
    for node in config['nodes']:
        if node[1].get("type", "") == 'start':
            start_message = node[1]['attribute']["value"]
            break
    history.append({"role": worker_prefix, "content": start_message})
    print(f"Bot: {start_message}")
    try:
        while True:
            user_text = input("You: ")
            if user_text.lower() == "quit":
                break
            start_time = time.time()
            output, params = get_api_bot_response(args, history, user_text, params)
            history.append({"role": user_prefix, "content": user_text})
            history.append({"role": worker_prefix, "content": output})
            print(f"getAPIBotResponse Time: {time.time() - start_time}")
            print(f"Bot: {output}")
    finally:
        terminate_subprocess()  # Ensure the subprocess is terminated
