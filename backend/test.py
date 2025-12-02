from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import openai
from dotenv import load_dotenv
import os
import json
import re

from sklearn import datasets
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

load_dotenv()

app = FastAPI()

openai_api_key = os.getenv("OPENAI_API_KEY")
infermedica_app_id = os.getenv("INFERMEDICA_APP_ID")
infermedica_app_key = os.getenv("INFERMEDICA_APP_KEY")

openai.api_key = openai_api_key


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


def symptoms_conversion(user_input): #takes the users input symptoms and returns a list of matching symptoms within the infermedica symptoms list WORKING!!
    symptoms_list = get_symptoms_list()

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

    return extract_ids_from_llm(symptoms_list)

def get_symptoms_list(user_age, user_sex): #returns a list with the common names of all valid symptoms - WORKING!!
    user_age = 25
    user_sex = "female"
    symptoms_dict = get_valid_symptoms(user_age)
    new_symptoms_dict = {symptom["id"]: symptom["common_name"] for symptom in symptoms_dict}

    return new_symptoms_dict

def get_valid_symptoms(age):
    url = f"https://api.infermedica.com/v3/symptoms?age.value={age}"
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
    #print("Infermedica Diagnosis:", response.json())

    session_info["current_diagnosis"] = response.json()

    #summarized_diagnosis = summarize_diagnosis(response.json())

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Infermedica API error")
    return response.json()


def get_follow_up_questions(diagnosis):
    question = diagnosis["question"]["text"]
    print(question)

    choices = []

    items = diagnosis["question"]["items"]
    # for key, value in items.items():
    #     if key == "name":
    #         choices.append(value)

    print(items)






def accuracy_testing(illness_dict):

    y_pred = []
    y_correct = []

    session_info1 = {
            "age": {"value": None,
            "unit": "year"},
            "sex": None,
            "symptoms": [],
            "chat_history": [],
            "is_diagnosed": False,
            "diagnosis": None,
            "current_state": "initial_gathering"
    }

    for key, value in illness_dict.items():
        y_correct.append(key)

        extract_user_info(session_info1, value)
        diagnosis = get_diagnosis(session_info1["age"], session_info1["sex"], session_info1["symptoms"])

        if diagnosis['conditions'] == []:
            y_pred.append("None")
        else:
            y_pred.append(diagnosis['conditions'][0]['common_name']) #common_name
        
        session_info1 = {
            "age": {"value": None,
            "unit": "year"},
            "sex": None,
            "symptoms": [],
            "chat_history": [],
            "is_diagnosed": False,
            "diagnosis": None,
            "current_state": "initial_gathering"
        }

    print(y_correct)
    print(y_pred)

    accuracy = accuracy_score(y_true=y_correct, y_pred=y_pred)
    formatted_accuracy = "{:.2f}%".format(accuracy*100)

    return formatted_accuracy

def accuracy_testing2(illness_dict):
    
    y_pred = []
    y_correct = []

    accuracy_score = 0
    count = 0

    session_info1 = {
            "age": {"value": None,
            "unit": "year"},
            "sex": None,
            "symptoms": [],
            "chat_history": [],
            "is_diagnosed": False,
            "diagnosis": None,
            "current_state": "initial_gathering"
    }

    for key, value in illness_dict.items():

        extract_user_info(session_info1, key)
        diagnosis = get_diagnosis(session_info1["age"], session_info1["sex"], session_info1["symptoms"])

        if diagnosis['conditions'] == []:
            y_pred.append("None")
        else:
            illness_name = diagnosis['conditions'][0]['common_name']
            y_pred.append(diagnosis['conditions'][0]['common_name']) #common_name

            if illness_name in value:
                accuracy_score += 1
                y_correct.append(illness_name)
            else:
                y_correct.append(value)
        
        count += 1

        
        session_info1 = {
            "age": {"value": None,
            "unit": "year"},
            "sex": None,
            "symptoms": [],
            "chat_history": [],
            "is_diagnosed": False,
            "diagnosis": None,
            "current_state": "initial_gathering"
        }

    print(f"Correct List: {y_correct}")
    print(f"Predicted List: {y_pred}")

    accuracy = accuracy_score / count
    formatted_accuracy = "{:.2f}%".format(accuracy*100)

    return formatted_accuracy
   

def all_category_testing():
    neurological = {
    "I'm a 60 yo man. I have double vision and eye pain. I've been really dizzy and have had muscle stiffness. I've had some bladder dysfunction as well.": ["Parkinson's disease"],
    "I'm a 30 yo female. I've had trouble balancing and my vision has been blurred. I've been forgetting a lot of things and my face goes numb often.": ["Multiple sclerosis"],
    "I'm a 70 year old female. I've been forgetting names and appointments, repeating myself often, and I get confused about where I am or what day it is.": ["Alzheimer's disease", "Dementia"],
    "I'm a 25 year old female. I’ve been having throbbing pain on one side of my head with nausea and sensitivity to light and sound.": ["Migraine"],
    "I'm a 19 yo male. I’ve had a few seizures recently where I lose awareness and my body shakes uncontrollably. I feel confused afterward.": ["Epilepsy", "Epilepsy with loss of consciousness"],
    "I'm a 74 year old female. I feel dizzy and lightheaded throughout the day. I’ve been feeling confused and disoriented. I’ve been forgetting things like names and appointments.": ["Alzheimer's disease", "Dementia"],
    "I'm a 48 year old female. I'm experiencing difficulty speaking. I’ve been feeling extremely tired and low on energy. I'm experiencing muscle weakness.": ["Amyotrophic lateral sclerosis"],
    "I'm a 28 year old male. I feel nauseous most of the time and have no appetite. My vision has been getting blurry lately. I’ve been having constant headaches that won’t go away.": ["Brain tumor"],
    "I'm a 66 year old male. My vision has been getting blurry lately. I feel dizzy and lightheaded throughout the day. I’ve been having constant headaches that won’t go away.": ["Carotid artery dissection"],
    "I'm a 24 year old male. I'm experiencing numbness. I'm experiencing lower back pain. I'm experiencing bladder dysfunction.": ["Cauda equina syndrome", "Sciatica"],
    }

    respiratory = {
    "I'm a 32-year-old male. Suddenly, I developed a high fever (102°F), severe, widespread body aches, chills, and a deep, hacking cough that makes my chest hurt. I feel completely drained of energy.": ["Flu"],
    "I'm a 28-year-old female. I've had a persistent dry cough, significant shortness of breath even at rest, a complete loss of my sense of taste and smell that started yesterday, and I feel overwhelmingly fatigued.": ["COVID-19"],
    "I'm a 70-year-old female. I've had a bad cold for a few days that suddenly worsened. Now I'm wheezing audibly, experiencing rapid, shallow breathing, and have a very productive cough that's bringing up thick mucus. I feel very tired." : ["Respiratory syncytial virus"],
    "I'm a 35-year-old male. I have a sore throat, a cough, and surprisingly, both of my eyes are red and itchy with discharge (pink eye). I also had a low-grade fever for a couple of days last week.": ["Adenovirus", "Hay fever"],
    "I'm a 40-year-old male. I have a runny nose with clear discharge, a mild sore throat, and I've been sneezing a lot for the past few days.": ["Common cold"],
    "I'm a 25-year-old female. I initially had a mild fever and headache, and now I have a distinctive bright red rash on both cheeks that looks like I've been slapped, along with a lacy, reticulated rash spreading on my arms and legs. My joints also ache.": ["Parvovirus B19", "Lupus", "Parvovirus"],
    "I'm a 22-year-old female. I regularly experience episodes of tightness in my chest and a whistling sound (wheezing) when I breathe out, especially after exposure to pollen or during exercise. Sometimes I also have a dry cough that won't go away.": ["Asthma"],
    "I'm a 55-year-old female. I've had a persistent, often productive cough for over a month, accompanied by drenching night sweats, unexplained weight loss of 15 pounds, and profound fatigue. I also sometimes notice streaks of blood in my sputum.": ["Tuberculosis", "Pulmonary tuberculosis"],
    "I'm a 45-year-old male. I've had a persistent cough for about a week that brings up yellow-green mucus, and I feel a tightness in my chest. I also had a cold before this started.": ["Bronchitis", "Acute bronchitis"],
    "I'm a 70-year-old female. I suddenly developed a very high fever with shaking chills, a deep cough producing thick, greenish-yellow phlegm, and sharp, stabbing chest pain that worsens significantly when I take a deep breath or cough. I'm also very short of breath.": ["Pneumonia", "Acute bronchitis"],
    "I'm a 30-year-old female. Every spring, I develop intensely itchy eyes, nose, and throat, accompanied by frequent sneezing fits and a profusely runny nose with clear discharge. These symptoms are worse outdoors and I never have a fever or body aches with them.": ["Seasonal allergies", "Common cold"]
    }
    
    cardiovascular = {
    "I'm a 33 year old male. I’ve been having chest pain that feels tight and radiates down my left arm. I’m sweating a lot, and I feel nauseous and short of breath.": ["Heart attack"],
    "I'm a 20 year old female. I’ve been feeling really confused and lightheaded, my heart is racing, I’ve got a high fever and chills, and no matter how much water I drink, I feel extremely weak and short of breath.": ["Sepsis"],
    "I'm a 25 year old male. I’ve been feeling weak and out of breath lately, even when just walking short distances. I’m pale and I’ve noticed my heartbeat is faster than normal.": ["Sickle cell anemia"],
    "I'm a 74 yo male. My ankles are swollen, I get tired easily, and I have trouble breathing when I lie down. I keep waking up at night gasping for air.": ["Chronic heart failure", "Dilated cardiomyopathy"],
    "I'm a 45 yo female. I don’t feel many symptoms, but I’ve had headaches, blurry vision, and I was told at the clinic my blood pressure was very high.": ["High blood pressure"],
    "I'm a 58-year-old male. I've been feeling unusually tired, my ankles and feet are swollen, and I've noticed I'm urinating more often, especially at night. I also feel itchy all over.": ["Kidney disease", "Chronic kidney disease"],
    "I'm a 65-year-old male. I often feel a squeezing pain or pressure in my chest when I exert myself, and it sometimes spreads to my left arm. I also get short of breath with mild activity.": ["Coronary heart disease", "Stable angina pectoris"],
    "I'm a 70-year-old female. My legs feel heavy and cramp up when I walk, especially in my calves, and the pain usually goes away when I rest. I've also noticed that the skin on my feet looks shiny and I have less hair on my legs.": ["Peripheral arterial disease", "Chronic venous insufficiency"],
    "I'm a 45-year-old female. I've been experiencing unexplained fatigue, shortness of breath, and sometimes I feel a fluttering or irregular heartbeat. I've also had some chest discomfort that isn't always related to exertion.": ["Cardiac Tumor"],
    "I'm a 60-year-old male. I've noticed I get out of breath easily, even when just walking across a room, and I sometimes feel dizzy. My ankles have also started to swell, and my doctor mentioned a heart murmur.": ["Heart valve disease"],
    "I'm a 30-year-old male. I recently had a viral infection, and now I'm experiencing chest pain, extreme fatigue, and shortness of breath, even at rest. My heart feels like it's racing sometimes.": ["Chronic heart failure", "Heart failure"],
    "I'm a 52-year-old female. I frequently feel my heart skipping beats or racing very fast, and sometimes it feels like a fluttering sensation. I've also had episodes of dizziness and lightheadedness.": ["Arrhythmia"]
    }
    
    immune_inflammatory = {
    "I'm a 28 year old female. I’ve been feeling really tired all the time, my joints are swollen and painful, and I keep getting rashes on my face and arms, especially after being in the sun.": ["Lupus"],
    "I'm a 15 yo female. It's hard for me to swallow and my throat is really sore. I have a fever and parts of my neck are swollen and tender. My tonsils look swollen as well.": ["Strep throat", "Mononucleosis", "Acute streptococcal pharyngitis"],
    "I'm a 49 yo female. My hands are really stiff and painful in the morning, and it’s hard to open jars or grip things. The swelling gets worse later in the day.": ["Rheumatoid arthritis"],
    "I'm a 34 year old male. I have thick red patches with silvery scales on my elbows. They itch a lot and sometimes crack and bleed.": ["Psoriasis"],
    "I'm a 31 yo female. I’ve been having stomach cramps, urgent diarrhea, and blood in my stool. It gets worse when I’m stressed.": ["Inflammatory bowel disease", "Bacterial gastroenteritis"],    
    "I'm a 38-year-old male. I've been coughing up blood and feeling very short of breath, and my legs and face have been swelling. I've also been feeling very tired and nauseous.": ["Goodpasture's syndrome"],
    "I'm a 68-year-old male with a history of smoking. I have a persistent cough that produces a lot of mucus, and I get breathless easily, even with light activity.": ["Chronic obstructive pulmonary disease", "Pneumonia"],
    "I'm a 55-year-old female. My joints, especially in my hands and feet, feel stiff and swollen, particularly in the mornings. The stiffness lasts for more than an hour, and I've noticed symmetrical pain in the same joints on both sides of my body.": ["Rheumatoid arthritis"],
    "I'm a 45-year-old male. I have patches of red, scaly skin on my elbows and knees, and some of my nails are pitted. Lately, I've also noticed swelling and pain in some of my finger joints, making them look like 'sausages'.": ["Psoriatic arthritis", "Psoriasis"],
    "I'm a 50-year-old female. I've been experiencing significant muscle weakness that makes it hard to climb stairs or lift objects over my head. My muscles ache, and I've also developed a reddish-purple rash on my eyelids and knuckles.": ["Polymyositis", "Cushing's syndrome", "Dermatomyositis"],
    "I'm a 62-year-old male. I've had unexplained fevers, fatigue, and muscle aches. I also developed a strange rash on my legs, and some of my fingers and toes feel numb and tingly. My doctor mentioned something about inflammation in my blood vessels.": ["Vasculitis"]
    }

    mental = { #done
    "I'm a 22 year old female. I’ve been feeling sad for weeks, have no energy, I’m sleeping too much, and I’ve lost interest in everything I usually enjoy.": ["Dysthymia", "Major depressive disorder"],
    "I'm a 29 yo male. I constantly feel on edge, I can't stop worrying even about small things, and I have trouble sleeping and concentrating.": ["Generalized anxiety disorder", "Panic disorder"],
    "I'm a 41 year old male. I keep reliving a traumatic event, I get nightmares almost nightly, and loud sounds make me feel like I’m back in that moment.": ["Post traumatic stress disorder", "Acute reaction to stress"],
    "I'm a 26 yo female. Some days I feel like I’m on top of the world with tons of energy, and other days I can’t even get out of bed or stop crying.": ["Bipolar disorder", "Cyclothymic disorder"],
    "I'm a 28-year-old male. I've been hearing voices that no one else can hear, and I sometimes believe that people are plotting against me. I've also had trouble organizing my thoughts and expressing myself clearly.": ["Paranoid schizophrenia"],
    "I'm a 30-year-old male. I find it incredibly hard to focus on tasks, I'm easily distracted, and I often interrupt conversations without meaning to. I also tend to procrastinate and struggle with time management.": ["Attention deficit hyperactivity disorder"],
    "I'm a 23-year-old female. I'm intensely afraid of gaining weight, even though my friends tell me I'm too thin. I severely restrict what I eat, and I exercise compulsively, despite feeling constantly cold and fatigued.": ["Anorexia"],
    "I'm a 33-year-old female. I'll eat a large amount of food, just to throw it up later. I'm scared of weight gain and I think a lot about food.": ["Bulimia"],
    "I'm a 42-year-old male. I'm plagued by intrusive thoughts about germs and contamination, which compel me to wash my hands repeatedly until they're raw. I also feel an overwhelming need to check if the door is locked multiple times before I can leave the house.": ["Obsessive-compulsive disorder"],
    "I'm a 78-year-old female. I've been increasingly forgetful, especially with recent events, and I sometimes get lost in familiar places. My family says I've also been having trouble with problem-solving and finding the right words.": ["Dementia", "Alzheimer's disease"],
    }
    
    metabolic = { #done
    "I'm a 40 yo female. My vision has been blurry and I've been really thirsty. I've also been peeing often.": ["Diabetes mellitus type 2"],
    "I'm a 36 year old female. My skin has been dry and flaky, I’ve been gaining weight even though I’m not eating more, and I always feel cold and tired.": ["Hypothyroidism"],
    "I'm a 43 yo female. I’ve gained a lot of weight in my belly and face, my periods have stopped, and I bruise very easily.": ["Cushing's syndrome"],
    "I'm a 30 year old male. I’ve been losing weight fast, my hands tremble, I feel anxious all the time, and my heartbeat is rapid even at rest.": ["Hyperthyroidism"],
    "I'm a 24 yo female. I’ve had irregular periods, trouble losing weight, and I’m growing facial hair. I’ve also been breaking out a lot.": ["Polycystic ovary syndrome"],
    "I'm a 48-year-old female. I've been feeling unusually tired and sluggish, gaining weight despite not changing my diet, and my skin feels dry and my hair is thinning. I also often feel cold, even when others are warm.": ["Hypothyroidism"],
    "I'm a 35-year-old male. I've noticed I'm losing weight without trying, my heart often races, and I feel constantly anxious and irritable. I also have trouble sleeping and my hands sometimes tremble.": ["Hyperthyroidism"],
    "I'm a 55-year-old male. I woke up with intense pain, swelling, and redness in my big toe. It's incredibly tender to the touch, and even the weight of a sheet is painful.": ["Gout"],
    "I'm a 62-year-old male. I've been experiencing chronic fatigue, joint pain, especially in my hands, and I've noticed my skin has a bronze or grayish tone. My doctor mentioned my liver enzymes were a bit high.": ["Hemochromatosis"],
    "I'm a 50-year-old female. I haven't really had any symptoms, but during a routine check-up, my doctor told me my blood pressure readings were consistently high. Sometimes I get mild headaches, but I usually attribute it to stress.": ["High blood pressure"],
    }
    
    gastrointestinal = {
    "Gastroesophageal reflux disease": "I'm a 45 yo male. I've had persistent heartburn, a sour taste in my mouth, and a burning sensation in my chest after I eat.",
    "Appendicitis": "I'm a 26 year old female. I’ve been having sharp pain in my lower right abdomen, I feel nauseous, and I had a fever last night.",
    "Colorectal cancer": "I'm a 48 year old female. I’ve been having abdominal pain and bloating, and I’ve noticed blood in my stool. I’ve also lost weight without trying.",
    "Peptic ulcer": "I'm a 39 yo male. I’ve been having burning stomach pain that gets worse on an empty stomach and feels better after eating or taking antacids.",
    "Gallstones": "I'm a 52 yo female. I get sudden pain in my upper right abdomen after eating fatty foods. Sometimes the pain spreads to my back and shoulder.",
    "Irritable bowel syndrome": "I'm a 40 yo male. I've been having some constipation and diarrhea, and my poop looks whitish. Even after I finished pooping, it feels like I'm not empty.",
    "Hemmorhoids": "I'm a 50 yo male. It's itching and painful around my butt and I can feel some hard lumps there that are tender. When I wipe my butt, I see some blood.",
    "Celiac disease": "I'm a 50 yo female. After I eat anything with gluten, I have stomach pain, diarrhea, headaches, and I feel weak. My hands have been really cold as well."
    }

    all_categories = {
    #"neurological": neurological, #done
    "respiratory": respiratory,
    #"cardiovascular": cardiovascular, #done
    #"immune/inflammatory": immune_inflammatory, #done
    #"mental": mental, #done
    #"metabolic": metabolic, #done
    # "gastrointestinal": gastrointestinal
    }

    for category, illness_dict in all_categories.items():
        accuracy = accuracy_testing2(illness_dict)
        print(f"{category} test: {accuracy}\n")





if __name__ == '__main__':
    all_category_testing()



#Additions
#use the conditions endpoint to get more information about the diagnosis

#if the diagnosis is sever, give a major warning