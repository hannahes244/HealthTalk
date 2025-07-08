from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import openai
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

app = FastAPI()

openai_api_key = os.getenv("OPENAI_API_KEY")
infermedica_app_id = os.getenv("INFERMEDICA_APP_ID")
infermedica_app_key = os.getenv("INFERMEDICA_APP_KEY")

openai.api_key = openai_api_key


#Request Model
class SymptomInput(BaseModel): #keeping it basic for now, will add other fields later
    age: list[int]
    sex: str
    evidence: list[str]

#Response Model
class AssistantResponse(BaseModel):
    diagnosis: str
    advice: str
    # severity: str
    # treatments: list[str]


user_states = {} #session_id --> session_info

session_info = {
    "age": {"value": None,
            "unit": "year"},
    "sex": None,
    "symptoms": [],
    "chat_history": [],
    "is_diagnosed": False,
    "diagnosis": None,
    "current_state": "initial_gathering"
}


# ------------------------------------ Processing User Input ------------------------------------------------------------------------

def process_user_message(session_id, user_message): #session_id, user_message
    session_info = user_states.get(session_id)
    if not session_info:
        session_info = {
            "age": {
                "value": None,
                "unit": "year"
            },
            "sex": None,
            "symptoms": [],
            "chat_history": [],
            "is_diagnosed": False,
            "diagnosis": None,
            "current_state": "initial_gathering"
        }

        user_states[session_id] = session_info
        inital_message ="Hi, I'm HealthTalk — your AI-powered health assistant. I can help you understand your symptoms and give general advice. To get started, can you tell me your age, sex, and what symptoms you're experiencing?"
        session_info["chat_history"].append({"role": "assistant", "content": inital_message})
        return inital_message
    
    #print("User States:", user_states)
    #print("\n \n Session Info:", session_info)

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

            #currently_needed.clear()
                

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


    
# ------------------------------------ Getting Initial User Information ------------------------------------------------------------------------

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
        #print(" \n \n Extracted Symptoms:", extracted_symptoms)
        session_info["symptoms"] = extracted_symptoms

def extract_symptoms(session_info, user_input):
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




# ------------------------------------ Getting Symptoms from User Input ------------------------------------------------------------------------

def symptoms_conversion(user_input): #takes the users input symptoms and returns a list of matching symptoms within the infermedica symptoms list WORKING!!
    symptoms_list = get_symptoms_list()

    user_symptoms = user_input
    session_info["chat_history"].append({"role": "user", "content": user_symptoms})

    system_prompt = f"""
    You are a medical assistant. The user will describe their symptoms in natural language.
    Your task is to identify symptoms from the user’s input and map them **exactly** to entries in the approved list of symptoms provided below.
    Only return symptoms that match exactly — do not summarize, shorten, combine, or infer symptoms. 
    """
    #Use only the terms exactly as they appear in the list. If the symptom the user describes is not in the list, do not include it.
    #Return a comma-separated list using only the terms from the list, without quotes or brackets.

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

    return extract_ids_from_llm(symptoms_list)

# ------------------------------------ Get Missing Info from User ------------------------------------------------------------------------


# ------------------------------------ Helper Functions ------------------------------------------------------------------------

def get_symptoms_list(user_age, user_sex): #returns a list with the common names of all valid symptoms - WORKING!!
    user_age = 25
    user_sex = "female"
    symptoms_dict = get_valid_symptoms(user_age)
    new_symptoms_dict = {symptom["id"]: symptom["common_name"] for symptom in symptoms_dict}

    return new_symptoms_dict



@app.get("/symptoms")
def get_valid_symptoms(age): #need to add age and maybe gender as a parameter - WORKING!!
    url = f"https://api.infermedica.com/v3/symptoms?age.value={age}" #?age.value=25" instead of hard coding a value, this will be passed as the parameter
    headers = {
        "App-Id": infermedica_app_id,
        "App-Key": infermedica_app_key,
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch symptoms list")
    return response.json()



def extract_ids_from_llm(symptom_lines):
    symptom_ids = []
    for item in symptom_lines:
        if ":" in item:
            symptom_id = item.split(":")[0].strip()
            symptom_ids.append(symptom_id)
    return symptom_ids


# ------------------------------------ Sending symptom ids to Infermedica ------------------------------------------------------------------------

def get_diagnosis(age, sex, symptoms): #sending user info/sympotms for diagnosis - post request - /diagnosis
    url = "https://api.infermedica.com/v3/diagnosis"
    headers = {
        "App-Id": infermedica_app_id,
        "App-Key": infermedica_app_key,
        "Content-Type": "application/json"}
    
    symptoms = [{"id": s, "choice_id": "present"} for s in symptoms]

    payload = {
        "age": age,
        "sex": sex,
        "evidence": symptoms
    }

    response = requests.post('https://api.infermedica.com/v3/diagnosis', headers=headers, json=payload) #there's an issue here
    print("Infermedica Diagnosis:", response.json())

    session_info["current_diagnosis"] = response.json()

    summarized_diagnosis = summarize_diagnosis(response.json())

    #print("Diagnosis Summary:", summarized_diagnosis)
    #print("Chat History:", session_info["chat_history"])

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Infermedica API error")
    return summarized_diagnosis

#getting additional information about the diagnosis - get request - /conditions/{id}

# ------------------------------------ Sending Infermedica response to GPT - Summarizing Diagnosis ------------------------------------------------------------------------

def summarize_diagnosis(diagnosis_data):
    conditions = diagnosis_data.get("conditions", [])
    top_condition = conditions[0] if conditions else {"name": "unknown", "probability": 0}
    
    prompt = f"""
        You are HealthTalk, an AI medical assistant. Respond kindly and empathetically, as a caring medical assistant would. 
        Offer reassurance when appropriate.

        A user has entered symptoms and received the following top condition: {top_condition['name']}.
        Please give them an explanation of the condition and provide some advice on how to manage it.

        Please summarize the following condition and advice in Markdown, including headings, bullet points for key takeaways, and bold text for important concepts.
    """

    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": prompt}]
    )

    session_info["chat_history"].append({"role": "assistant", "content": completion.choices[0].message.content})

    return completion.choices[0].message.content

# ------------------------------------ Follow-Ups with GPT - Ask Follow-Up Questions Based on Infermedica Response ------------------------------------------------------------------------

def followup_questions(session_info, user_message):

    prompt = f"""
        You are HealthTalk, an AI medical assistant. Respond kindly and empathetically, as a caring medical assistant would. 
        Offer reassurance when appropriate.

        The user has had a prior conversation with you. Your chat history and user information is given: {session_info}.

        Feel free to ask follow-up questions to the user or give them proper advice.

        Please provide your answer in Markdown, including headings, bullet points for key takeaways, and bold text for important concepts.
    """

    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": prompt}]
    )

    session_info["chat_history"].append({"role": "assistant", "content": completion.choices[0].message.content})

    return completion.choices[0].message.content


# ------- API endpoint -------
@app.post("/assistant", response_model=AssistantResponse) #post endpoint - will return a response with the AssistantReponse model structure
def medical_assistant(input: SymptomInput): #function that takes in the input, matching the SymptomInput model
    diagnosis_data = get_diagnosis(input.age, input.sex, input.symptoms) #calling the above get diagnosis function, passing in the user's age, sex, and symptoms
    gpt_summary = summarize_diagnosis(diagnosis_data) #calling the above summarize diagnosis function, passing in the diagnosis data
    top_condition_name = diagnosis_data.get("conditions", [{}])[0].get("name", "unknown")
    return AssistantResponse(
        diagnosis=top_condition_name,
        advice=gpt_summary
    )


def main():
    input1 = "I'm a 20 year old female. I've been feeling dizzy and my heart is beating really fast. I've had extreme pain. My skin has been loking blotchy as well."
    input2 = "I'm a 30 yo man. It’s hard to breathe and my throat is sore."
    input3 = "Everything hurts and I’m exhausted."


if __name__ == '__main__':
    
    current_session_id = "test_user_123"

    first_response = process_user_message(current_session_id, "") # Empty message to trigger new session init
    print("HealthTalk:", first_response)

    while True:
        if current_session_id not in user_states: # Session ended
            print("Conversation ended.")
            break

        user_input_text = input("You: ")
        if user_input_text.lower() == "exit":
            print("Ending chat.")
            break

        assistant_response = process_user_message(current_session_id, user_input_text)
        print("HealthTalk:", assistant_response)


# ------------------------------------ NO LONGER NEEDED ------------------------------------------------------------------------

def test_infermedica_connection(): #just testing that the connection/reference to infermedica is working - WORKING!!
    url = "https://api.infermedica.com/v3/info"
    headers = {
        "App-Id": infermedica_app_id,
        "App-Key": infermedica_app_key,
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    print("Status:", response.status_code)
    print("Response:", response.json())