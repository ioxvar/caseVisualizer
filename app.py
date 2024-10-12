import os
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import requests
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app)

PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
LEGAL_DICTIONARY_API_KEY = os.getenv('LEGAL_DICTIONARY_API_KEY')  # You'll need to sign up for a legal dictionary API

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_case():
    case_data = request.json
    analysis = call_perplexity_api(case_data)
    session['analysis'] = analysis
    return jsonify(analysis)

@app.route('/export_pdf', methods=['GET'])
def export_pdf():
    analysis = session.get('analysis', {})
    # Here you would generate a PDF using a library like ReportLab
    # For the hackathon, you could just return the JSON as a file
    return jsonify(analysis), 200, {
        'Content-Disposition': 'attachment; filename=case_analysis.json',
        'Content-Type': 'application/json'
    }

@app.route('/define/<term>', methods=['GET'])
def define_term(term):
    definition = get_legal_definition(term)
    return jsonify(definition)

def call_perplexity_api(case_data):
    api_url = 'https://api.perplexity.ai/chat/completions'
    
    prompt = f"""
    Analyze the following legal case:
    {json.dumps(case_data)}

    Provide the following information:
    1. A timeline of key events (at least 5 events)
    2. Applicable laws for each event
    3. Relevant case citations for each event (at least one per event)
    4. Entities involved and their relationships
    5. A preliminary judgment based on the information provided
    6. Potential future outcomes
    7. Confidence level in the analysis (considering completeness of information)
    8. Suggestions for additional information needed for a more accurate analysis
    9. Comparison to similar historical cases (if any)
    10. Potential challenges or counterarguments to the preliminary judgment

    Format your response as JSON with the following structure:
    {{
        "timeline": [
            {{
                "event": "Event description",
                "date": "YYYY-MM-DD",
                "applicable_law": "Law description",
                "case_citations": ["Case citation 1", "Case citation 2"]
            }},
            ...
        ],
        "entities": [
            {{"name": "Entity name", "type": "Entity type (e.g., Person, Organization)"}},
            ...
        ],
        "entity_relationships": [
            {{"source": "Entity1", "target": "Entity2", "relationship": "Description of relationship"}},
            ...
        ],
        "preliminary_judgment": "Your preliminary judgment",
        "potential_outcomes": ["Outcome 1", "Outcome 2", "Outcome 3"],
        "confidence_level": "High/Medium/Low",
        "additional_info_needed": ["Information 1", "Information 2", ...],
        "similar_cases": [
            {{
                "case_name": "Name of similar case",
                "key_similarities": ["Similarity 1", "Similarity 2", ...],
                "outcome": "Outcome of similar case"
            }},
            ...
        ],
        "potential_challenges": ["Challenge 1", "Challenge 2", ...]
    }}
    """

    response = requests.post(
        api_url,
        headers={
            'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
            'Content-Type': 'application/json'
        },
        json={
            'model': 'pplx-7b-chat',
            'messages': [{'role': 'user', 'content': prompt}]
        }
    )

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return {'error': 'Failed to get response from Perplexity API'}

def get_legal_definition(term):
    # This is a placeholder. You would need to implement this using a real legal dictionary API
    api_url = f'https://api.legaldictionary.com/define/{term}'
    response = requests.get(api_url, headers={'Authorization': f'Bearer {LEGAL_DICTIONARY_API_KEY}'})
    if response.status_code == 200:
        return response.json()
    else:
        return {'error': 'Failed to get definition'}

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f"User has joined the room."}, room=room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f"User has left the room."}, room=room)

@socketio.on('update_case')
def on_update_case(data):
    room = data['room']
    case_data = data['case_data']
    emit('case_updated', case_data, room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)