import requests
import openai # Already configured in config/settings.py, but good to import if used directly
import re
import json
from fastapi import HTTPException # For consistent error handling

user_states = {}

# Import settings for API keys
from config.settings import settings


def get_valid_symptoms_from_infermedica(age: int, sex: str):
    # Note: your original get_symptoms_list had hardcoded age/sex
    # This version correctly uses the passed arguments
    url = f"https://api.infermedica.com/v3/symptoms?age.value={age}"
    headers = {
        "App-Id": settings.INFERMEDICA_APP_ID,
        "App-Key": settings.INFERMEDICA_APP_KEY,
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching symptoms: {response.status_code} - {response.text}")
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch symptoms list from Infermedica")
    return response.json()

def get_symptoms_list(user_age: int, user_sex: str):
    """
    Returns a dictionary with symptom IDs as keys and common names as values
    for use by the LLM.
    """
    symptoms_dict = get_valid_symptoms_from_infermedica(user_age, user_sex)
    # Ensure it returns a simple dictionary of id: common_name
    return {symptom["id"]: symptom["common_name"] for symptom in symptoms_dict}

def extract_ids_from_llm(symptom_lines: list[str]) -> list[str]:
    """
    Extracts symptom IDs from a list of strings returned by the LLM.
    Assumes format 'ID: Common Name'
    """
    symptom_ids = []
    for item in symptom_lines:
        if ":" in item:
            symptom_id = item.split(":")[0].strip()
            symptom_ids.append(symptom_id)
    return symptom_ids



def extract_user_info(session_info, text):
    extracted_age = None
    extracted_sex = None

    age_match = re.search(r'my age is (\d+)|i\'m (\d+) (?:years old|yo)|i am (\d+) (?:years old|yo)|i\'m a (\d+) (?:year old|yo)|(/d+) (?:years old|yo)|\b(\d{1,3})\b', text.lower())
    if age_match:
        extracted_age = int(age_match.group(1) or age_match.group(2) or age_match.group(3) or age_match.group(4) or age_match.group(5) or age_match.group(6))
        

    # Extract sex
    sex_match = re.search(r'(male|female|man|woman|boy|girl|guy)', text.lower())
    if sex_match:
        extracted_sex = sex_match.group(1) or sex_match.group(2) or sex_match.group(3) or sex_match.group(4) or sex_match.group(5) or sex_match.group(6) or sex_match.group(7)#or sex_match.group(2)
        

    if session_info["age"]["value"] is None:
        session_info["age"]["value"] = extracted_age

    if session_info["sex"] is None:
        if extracted_sex == "man" or extracted_sex == "boy" or extracted_sex == "guy" or extracted_sex == "male":
            session_info["sex"] = "male"
        elif extracted_sex == "woman" or extracted_sex == "girl" or extracted_sex == "female":
            session_info["sex"] = "female"

    if(session_info["age"]["value"] is not None and session_info["sex"] is not None):
        extracted_symptoms = extract_symptoms(session_info, text)
        session_info["symptoms"] = extracted_symptoms

def extract_symptoms(session_info: dict, user_input: str):
    symptoms_list = get_symptoms_list(session_info["age"]["value"], session_info["sex"])

    user_symptoms = user_input
    session_info["chat_history"].append({"role": "user", "content": user_symptoms})

    system_prompt = f"""
    You are a medical assistant. The user will describe their symptoms in natural language.
    Your task is to identify symptoms from the user’s input and map them **exactly** to entries in the approved list of symptoms provided below.
    Only return symptoms that match exactly — do not summarize, shorten, combine, or infer symptoms. 
    """

    user_prompt = f"""
    The user said: "{user_symptoms}"

    Only use symptoms from this list:
    {json.dumps(symptoms_list)}

    Use only the terms exactly as they appear in the list. If the symptom the user describes is not in the list, do not include it.
    Return a comma-separated dictionary with both the term AND its id using only the terms from the list, without quotes or brackets.
    """

    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    symptoms_list = [sym.strip() for sym in completion.choices[0].message.content.split(",")]

    session_info["symptoms"] = symptoms_list

    id_extraction = extract_ids_from_llm(symptoms_list)

    return id_extraction


def symptoms_conversion(user_input: str): #takes the users input symptoms and returns a list of matching symptoms within the infermedica symptoms list WORKING!!
    symptoms_list = get_symptoms_list()

    user_symptoms = user_input
    #session_info["chat_history"].append({"role": "user", "content": user_symptoms})

    system_prompt = f"""
    You are a medical assistant. The user will describe their symptoms in natural language.
    Your task is to identify symptoms from the user’s input and map them **exactly** to entries in the approved list of symptoms provided below.
    Only return symptoms that match exactly — do not summarize, shorten, combine, or infer symptoms. 
    """

    user_prompt = f"""
    The user said: "{user_symptoms}"

    Only use symptoms from this list:
    {json.dumps(symptoms_list)}

    Use only the terms exactly as they appear in the list. If the symptom the user describes is not in the list, do not include it.
    Return a comma-separated dictionary with both the term AND its id using only the terms from the list, without quotes or brackets.
    """

    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    symptoms_list = [sym.strip() for sym in completion.choices[0].message.content.split(",")]
    #session_info["symptoms"] = symptoms_list

    return extract_ids_from_llm(symptoms_list)


def get_diagnosis(age: dict, sex: str, symptoms: list[str]): #sending user info/sympotms for diagnosis - post request - /diagnosis
    url = "https://api.infermedica.com/v3/diagnosis"
    headers = {
        "App-Id": settings.INFERMEDICA_APP_ID,
        "App-Key": settings.INFERMEDICA_APP_KEY,
        "Content-Type": "application/json"}
    
    symptoms = [{"id": s, "choice_id": "present"} for s in symptoms]

    payload = {
        "age": age,
        "sex": sex,
        "evidence": symptoms
    }

    response = requests.post('https://api.infermedica.com/v3/diagnosis', headers=headers, json=payload) #there's an issue here
    print("Infermedica Diagnosis:", response.json())

    #session_info["current_diagnosis"] = response.json()

    summarized_diagnosis = summarize_diagnosis(response.json())

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Infermedica API error")
    return summarized_diagnosis

def summarize_diagnosis(diagnosis_data: dict):
    conditions = diagnosis_data.get("conditions", [])
    top_condition = conditions[0] if conditions else {"name": "unknown", "probability": 0}
    
    prompt = f"""
        You are HealthTalk, an AI medical assistant. Respond kindly and empathetically, as a caring medical assistant would. 
        Offer reassurance when appropriate.

        A user has entered symptoms and received the following top condition: {top_condition['common_name']}. 
        Frame the condition as a suggesstion, not as something sure.

        Please give them an explanation of the condition and provide some advice on how to manage it.
        After the explanation, ask the patient if they think the condition is correct.

        If the condition is urgent, emphasize the urgency and encourage them to get to a medical professional quickly.

        Please summarize the following condition and advice including headings, bullet points for key takeaways, and bold text for important concepts. 
        Remember to ask the user if they think the condition is accurate.
    """

    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": prompt}]
    )

    #session_info["chat_history"].append({"role": "assistant", "content": completion.choices[0].message.content})

    return completion.choices[0].message.content


def followup_questions(session_info: dict, user_message: str) -> str:
    # Use session_info["chat_history"] for full context
    chat_history_for_llm = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in session_info["chat_history"]
    ]

    prompt = f"""
        You are HealthTalk, an AI medical assistant. Respond kindly and empathetically, as a caring medical assistant would. 
        Offer reassurance when appropriate.

        The user has just responded with: "{user_message}".
        Based on the previous conversation history and the current state of information about the user's age, sex, and symptoms:

        User Info: Age: {session_info['age']['value']}, Sex: {session_info['sex']}, Symptoms: {session_info['symptoms']}
        Current Diagnosis (if any): {session_info.get('diagnosis_data', 'N/A')}

        Decide on the best follow-up action:
        1. If the user provided new symptoms, acknowledge them and ask if there's anything else.
        2. If the user is asking general questions about their diagnosis, provide helpful, summarized information.
        3. If the user is ending the conversation (e.g., "bye", "thanks"), respond appropriately.
        4. If you need more information for a better diagnosis, ask relevant questions based on what's missing or what Infermedica might suggest (though Infermedica follow-ups are not implemented here yet).
        5. If the user asks something you don't understand, politely ask for clarification.
    """

    messages = chat_history_for_llm + [{"role": "system", "content": prompt}]

    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    return completion.choices[0].message.content



def process_user_message(session_id: str, user_message: str) -> str:
    if session_id not in user_states:
        user_states[session_id] = {
            "age": {"value": None, "unit": "year"},
            "sex": None,
            "symptoms": [], # List of symptom IDs
            "chat_history": [],
            "is_diagnosed": False,
            "diagnosis_data": None, # Store raw Infermedica diagnosis
            "current_state": "initial_gathering"
        }
        
    session_info = user_states[session_id]

    if not user_message and not session_info["chat_history"]:
        initial_greeting = "Hi, I'm HealthTalk — your AI-powered health assistant. I can help you understand symptoms, provide general health guidance, and determine when you should seek professional medical care.\n\nPlease remember that I provide general information only and cannot replace professional medical advice. For emergencies, always call 911 immediately.\n\n To get started, can you tell me your age, sex, and what symptoms you're experiencing?"
        session_info["chat_history"].append({"role": "assistant", "content": initial_greeting})
        return initial_greeting
    
    session_info["chat_history"].append({"role": "patient", "content": user_message})
    extract_user_info(session_info, user_message)

    assistant_response = ""

    if session_info["current_state"] == "initial_gathering":
        currently_needed = []

        if session_info["age"]["value"] is None:
            currently_needed.append("your age")

        if session_info["sex"] is None:
            currently_needed.append("your sex (male/female)")

        if len(session_info["symptoms"]) == 0:
            currently_needed.append("your symptoms")

        if not currently_needed:
            assistant_response = "Thank you for providing all the necessary information. Let me analyze this for a diagnosis."
            session_info["current_state"] = "diagnosis_ready"
            assistant_response += get_diagnosis(session_info["age"], session_info["sex"], session_info["symptoms"])

            session_info["is_diagnosed"] = True
            session_info["current_state"] = "follow_up"

        else:

            if len(currently_needed) == 1:
                assistant_response = f"Thank you! Could you also tell me {currently_needed[0]}?"
            elif len(currently_needed) == 2:
                assistant_response = f"Got it. I also need {currently_needed[0]} and {currently_needed[1]}."
            else:
                assistant_response = f"Please provide {', '.join(currently_needed)}."
                

    elif session_info["current_state"] == "follow_up":
        #I need to add something here for when the user provides new symptoms

        if "bye" in user_message.lower() or "thanks" in user_message.lower():
            assistant_response = "You're welcome! Feel free to reach out if you have more questions. Goodbye!"
            # End session for this example
            user_states.pop(session_id)
        else:
            assistant_response = followup_questions(session_info, user_message)

    session_info["chat_history"].append({"role": "assistant", "content": assistant_response})

    return assistant_response
    

 