from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import openai
from dotenv import load_dotenv
import os
import json

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


# ------- Infermedica API calls ------- 

#sending user info/sympotms for diagnosis - post request - /diagnosis
def get_diagnosis(symptoms, age, gender):
    url = "https://api.infermedica.com/v3/diagnosis" #https://api.infermedica.com/v3/diagnosis
    headers = {
        "App-Id": infermedica_app_id,
        "App-Key": infermedica_app_key,
        "Content-Type": "application/json"}
    
    symptoms = [{"id": s, "choice_id": "present"} for s in symptoms]

    payload = {
        "age": age,
        "sex": gender,
        "evidence": symptoms
    }
    print(payload)

    response = requests.post('https://api.infermedica.com/v3/diagnosis', headers=headers, json=payload) #there's an issue here
    print("Infermedica Diagnosis:", response.json())
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Infermedica API error")
    return response.json()


#getting additional information about the diagnosis - get request - /conditions/{id}


# ------- OpenAI API calls ------- 

def summarize_diagnosis(diagnosis_data):
    conditions = diagnosis_data.get("conditions", [])
    top_condition = conditions[0] if conditions else {"name": "unknown", "probability": 0}
    prompt = f"""
    A user has entered symptoms and received the following top condition: {top_condition['name']} (probability: {top_condition['probability']*100:.1f}%).
    Give a short explanation of what this condition is and general next steps for the patient. Include a disclaimer that this is not a diagnosis.
    """
    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message['content']


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

@app.get("/symptoms")
def get_valid_symptoms(age): #need to add age and maybe gender as a parameter - WORKING!!
    url = f"https://api.infermedica.com/v3/symptoms?age.value={age}" #?age.value=25" instead of hard coding a value, this will be passed as the parameter
    headers = {
        "App-Id": infermedica_app_id,
        "App-Key": infermedica_app_key,
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers)
    #print("Status:", response.status_code)
    #print("Response:", response.json())
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch symptoms list")
    return response.json()


def get_symptoms_list(): #returns a list with the common names of all valid symptoms - WORKING!!
    symptoms_dict = get_valid_symptoms(25)
    #symptoms_list = [symptom["common_name"] for symptom in symptoms_dict] 
    new_symptoms_dict = {symptom["id"]: symptom["common_name"] for symptom in symptoms_dict}

    return new_symptoms_dict

def symptoms_conversion(user_input): #takes the users input symptoms and returns a list of matching symptoms within the infermedica symptoms list WORKING!!
    symptoms_list = get_symptoms_list()

    system_prompt = f"""
    You are a medical assistant. The user will describe their symptoms in natural language.
    Your task is to identify symptoms from the user’s input and map them **exactly** to entries in the approved list of symptoms provided below.
    Only return symptoms that match exactly — do not summarize, shorten, combine, or infer symptoms. 
    """
    #Use only the terms exactly as they appear in the list. If the symptom the user describes is not in the list, do not include it.
    #Return a comma-separated list using only the terms from the list, without quotes or brackets.

    user_prompt = f"""
    The user said: "{user_input}"

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
    print(f"Symptoms List: {symptoms_list}")

    return extract_ids_from_llm(symptoms_list) #get_symptom_ids(symptoms_list, 25)

    #return (completion.choices[0].message.content).split(",")

def extract_ids_from_llm(symptom_lines):
    symptom_ids = []
    for item in symptom_lines:
        if ":" in item:
            symptom_id = item.split(":")[0].strip()
            symptom_ids.append(symptom_id)
    return symptom_ids


def get_symptom_ids(symptoms_list, age):
    all_symptoms = get_valid_symptoms(age)
    symptoms_ids = []
    for symptom in symptoms_list:
        for s in all_symptoms:
            if s["common_name"].lower() == symptom.lower():
                symptoms_ids.append(s["id"])
                break
    return symptoms_ids





if __name__ == '__main__':
    #print( get_symptoms_list() )
    #print( symptoms_conversion("My head has been pounding for 2 days and I've been feeling nauseous") )
    print( symptoms_conversion("I’ve been burning up and shivering all night.") )

    current_symptoms = symptoms_conversion("I’ve been burning up and shivering all night.")
    age = {"value": 25}
    get_diagnosis(current_symptoms, age, "female")

    #print( symptoms_conversion("It’s hard to breathe and my throat is sore.") )
    #print( symptoms_conversion("Everything hurts and I’m exhausted.") )
    #get_valid_symptoms(25)
    #get_diagnosis(["s_9"], 30, "male")