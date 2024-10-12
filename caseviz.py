import streamlit as st
import requests
import json
from pyvis.network import Network
import streamlit.components.v1 as components
import logging
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Embed the API key directly
API_KEY = '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'

# Function to check case validity using Perplexity API
def check_case_validity(case_description):
    url = "https://api.perplexity.ai/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Given the following legal case description, analyze its validity:
    
    {case_description}
    
    Please provide a clear assessment of whether this case appears to be valid or not, 
    and briefly explain the reasoning behind your conclusion. 
    Your response should be in the format:
    
    Validity: [VALID/INVALID]
    Reasoning: [Your explanation]
    """
    
    data = {
        "model": "llama-3.1-sonar-small-128k-chat",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        logger.debug(f"Sending request to {url}")
        logger.debug(f"Headers: {headers}")
        logger.debug(f"Data: {json.dumps(data)}")
        
        response = requests.post(url, headers=headers, json=data)
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response content: {response.text}")
        
        response.raise_for_status()
        result = response.json()
        
        # Extract the content from the API response
        content = result['choices'][0]['message']['content']
        
        # Parse the content to extract validity and reasoning
        validity = "INVALID"  # Default to invalid
        reasoning = "Unable to determine validity."
        
        if "Validity: VALID" in content:
            validity = "VALID"
        
        reasoning_start = content.find("Reasoning:")
        if reasoning_start != -1:
            reasoning = content[reasoning_start + 10:].strip()
        
        return validity, reasoning
    
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response content: {e.response.text}")
        return "ERROR", f"An error occurred: {str(e)}"

# Functions for each stage in the legal process
def negotiate_settlement():
    return st.radio("Was a settlement agreed upon?", ("Yes", "No"))

def proceed_to_trial():
    return st.radio("Proceed to trial?", ("Yes", "No"))

def appear_in_court():
    return st.radio("Did the appearance in court occur?", ("Yes", "No"))

def obtain_judgment():
    return st.radio("Was judgment obtained?", ("Yes", "No"))

def draft_settlement_agreement():
    return st.radio("Draft settlement agreement?", ("Yes", "No"))

def draft_judgment():
    return st.radio("Draft the judgment?", ("Yes", "No"))

# Function to generate the interactive graph using pyvis
def generate_pyvis_graph(validity, settlement_outcome, court_outcome):
    net = Network(height="600px", width="100%", notebook=True)
    
    # Add nodes for each step in the flowchart
    net.add_node('A', label='Client requests legal advice', shape='ellipse')
    net.add_node('B', label='Is the case valid?', shape='diamond')
    net.add_node('C', label='Accept case', shape='box')
    net.add_node('D', label='Reject case', shape='box')
    net.add_node('E', label='Is settlement possible?', shape='diamond')
    net.add_node('F', label='Negotiate settlement', shape='box')
    net.add_node('G', label='Proceed to trial', shape='box')
    net.add_node('H', label='Appear in court', shape='box')
    net.add_node('I', label='Obtain judgment', shape='box')
    net.add_node('J', label='Draft judgment', shape='box')
    net.add_node('K', label='Draft settlement agreement', shape='box')
    
    # Add edges based on decisions
    net.add_edge('A', 'B')
    
    if validity == 'VALID':
        net.add_edge('B', 'C')
        net.add_edge('C', 'E')
        if settlement_outcome == "Yes":
            net.add_edge('E', 'F')
            net.add_edge('F', 'K')  # Settlement agreed, draft agreement
        else:
            net.add_edge('E', 'G')
            net.add_edge('G', 'H')
            if court_outcome == "Yes":
                net.add_edge('H', 'I')
                net.add_edge('I', 'J')  # Judgment obtained, draft judgment
    else:
        net.add_edge('B', 'D')
    
    # Save and display the interactive graph
    net.set_options('''
    var options = {
        "physics": {
            "enabled": false
        },
        "nodes": {
            "font": {
                "size": 16
            },
            "borderWidth": 2
        }
    }
    ''')
    
    net_file_path = "/mnt/data/legal_case_graph.html"
    net.show(net_file_path)

    return net_file_path

# Streamlit layout
st.set_page_config(layout="wide")
st.title("Legal Case Analyzer")

# Sidebar for inputs
with st.sidebar:
    st.header("Input")
    case_description = st.text_area("Enter the legal case description:", height=300)
    
    analyze_button = st.button("Analyze Case")
    
    # Chatbox for additional prompts
    st.header("Ask a Question")
    chat_prompt = st.text_area("Enter your question about the case:", height=100)
    chat_button = st.button("Send Question")

# Case Analysis and Sidebar Insights
settlement_outcome, court_outcome = None, None

if analyze_button:
    if not case_description:
        st.sidebar.error("Please enter a case description.")
    else:
        with st.spinner("Analyzing case..."):
            validity, reasoning = check_case_validity(case_description)
        
        if validity == "ERROR":
            st.sidebar.error(reasoning)
        else:
            # Display results on the right-hand sidebar as insights
            st.sidebar.subheader("Case Analysis")
            st.sidebar.write(f"**Validity:** {validity}")
            st.sidebar.write(f"**Reasoning:** {reasoning}")
            
            # Proceed with settlement and court steps
            settlement_outcome = negotiate_settlement()
            court_outcome = None if settlement_outcome == "Yes" else appear_in_court()

            # Generate and display pyvis interactive graph
            st.subheader("Legal Process Flow")
            net_file_path = generate_pyvis_graph(validity, settlement_outcome, court_outcome)
            
            # Render the pyvis graph in Streamlit
            with open(net_file_path, 'r', encoding='utf-8') as f:
                graph_html = f.read()
            components.html(graph_html, height=600)

# Handle chat prompt submission
if chat_button:
    if not chat_prompt:
        st.sidebar.error("Please enter a question.")
    else:
        with st.spinner("Sending your question..."):
            validity, reasoning = check_case_validity(chat_prompt)  # Use case validity function for chat
            st.write(f"**Response to your question:** {reasoning}")

# Instructions and Disclaimer
st.sidebar.title("Instructions")
st.sidebar.write("""
1. Input a legal case description.
2. Click "Analyze Case" to get an assessment of the case validity.
3. Use the chatbox to ask additional questions related to the case.
4. Click "Send Question" to submit your question and see the response.
""")

st.sidebar.title("Disclaimer")
st.sidebar.write("""
This tool uses AI to analyze legal cases. The results and visualizations should not be considered as legal advice. Always consult with a qualified legal professional for actual legal matters.
""")
