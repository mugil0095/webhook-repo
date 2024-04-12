import os
import json
from datetime import datetime
from flask import Flask, request, render_template
from pymongo import MongoClient

app = Flask(__name__)
mongo_uri = os.environ["MONGO_URI"]
client = MongoClient(mongo_uri)
db = client["github_events"]

@app.route("/", methods=["GET"])
def index():
    events = db.events.find().sort("_id", -1).limit(10)
    return render_template("index.html", events=events)

@app.route("/", methods=["POST"])
def handle_github_webhook():
    data = request.get_json()
    action = data["action"]
    author = data["sender"]["login"]
    repo = data["repository"]["name"]
    branch = data["ref"].replace("refs/heads/", "")
    if action == "pull_request":
        pr_number = data["number"]
        pr_base = data["pull_request"]["base"]["ref"]
        pr_head = data["pull_request"]["head"]["ref"]
        event_data = {
            "action": action,
            "author": author,
            "repo": repo,
            "from_branch": pr_base,
            "to_branch": pr_head,
            "timestamp": datetime.fromisoformat(data["created_at"][:-1]),
            "request_id": pr_number,
        }
    else:
        event_data = {
            "action": action,
            "author": author,
            "repo": repo,
            "from_branch": branch,
            "to_branch": branch,
            "timestamp": datetime.fromisoformat(data["created_at"][:-1]),
            "request_id": data["after"],
        }
    db.events.insert_one(event_data)
    return "OK"

if __name__ == "__main__":
    app.run()