from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/')
db = client['github_webhook']
collection = db['events']

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event_type = data['event']
    payload = data['payload']

    # Extracting relevant data from payload
    author = payload['head_commit']['author']['name']
    timestamp = datetime.utcfromtimestamp(payload['head_commit']['timestamp']).strftime('%Y-%m-%d %H:%M:%S')

    if event_type == 'push':
        from_branch = payload['ref'].split('/')[-1]
        to_branch = from_branch
        action = 'PUSH'
    elif event_type == 'pull_request':
        from_branch = payload['pull_request']['head']['ref']
        to_branch = payload['pull_request']['base']['ref']
        action = 'PULL_REQUEST'
    elif event_type == 'merge':
        from_branch = payload['merge']['source']['ref']
        to_branch = payload['merge']['target']['ref']
        action = 'MERGE'

    # Storing data in MongoDB
    collection.insert_one({
        'request_id': payload['head_commit']['id'],
        'author': author,
        'action': action,
        'from_branch': from_branch,
        'to_branch': to_branch,
        'timestamp': timestamp
    })

    return 'Webhook received and data stored successfully!', 200

@app.route('/latest', methods=['GET'])
def latest_events():
    # Fetching latest events from MongoDB
    latest_events = collection.find().sort('timestamp', -1).limit(10)
    events_list = []
    for event in latest_events:
        events_list.append({
            'author': event['author'],
            'action': event['action'],
            'from_branch': event['from_branch'],
            'to_branch': event['to_branch'],
            'timestamp': event['timestamp']
        })
    return jsonify(events_list)

if __name__ == '__main__':
    app.run(debug=True)
