from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    user_input: str
    analysis: str
    response_type: Literal["common_issue", "serious_symptoms", "symptom_checker"]
    response: str
    current_symptom: str | None
    current_stage: int
    conversation_context: dict
    chat_history: list
    symptom_answers: dict
    severity: str
    emergency: bool


# Comprehensive symptom checker database
SYMPTOM_CHECKER_DB = {
    "fever": {
        "name": "Fever",
        "emergency_keywords": ["104", "105", "unbearable", "delirious", "unconscious"],
        "questions": [
            "How many days have you had the fever?",
            "What is your temperature (in °F)?",
            "Do you have chills or sweating?",
            "Do you feel body pain or weakness?",
            "Do you have headache or sore throat?",
        ],
        "severity_criteria": {
            "high": {
                "keywords": ["104", "105", "3 days", "severe", "unbearable"],
                "advice": "⚠️ Seek medical help immediately. High fever can lead to complications.",
                "medicines": "Consult doctor before taking any medicine",
            },
            "medium": {
                "keywords": ["2 days", "102", "103", "body pain", "weakness"],
                "advice": "Monitor your temperature closely. Continue hydration and rest. Take acetaminophen if temperature exceeds 101°F.",
                "medicines": "Acetaminophen (Tylenol) 500mg every 6 hours (max 2000mg/day)",
            },
            "low": {
                "keywords": ["1 day", "99", "100", "101", "feeling fine"],
                "advice": "Drink plenty of fluids (water, coconut water, warm fluids). Take rest. Use paracetamol if uncomfortable.",
                "medicines": "Paracetamol 500mg every 6 hours if needed",
            }
        },
        "diet": "Light foods like soups, broths, fruits (oranges, bananas), rice. Avoid heavy and spicy foods.",
        "disclaimer": "⚠️ This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.",
    },
    "cold/cough": {
        "name": "Cold / Cough",
        "emergency_keywords": ["breathing", "difficulty", "chest pain", "severe", "cannot breathe"],
        "questions": [
            "Do you have runny nose or blocked nose?",
            "Is your cough dry or with mucus?",
            "Do you have sore throat?",
            "Do you have fever along with cough?",
            "Do you feel breathing difficulty?",
        ],
        "severity_criteria": {
            "high": {
                "keywords": ["breathing", "difficulty", "chest pain", "severe", "cannot"],
                "advice": "⚠️ If experiencing breathing difficulty or chest pain, seek medical help immediately.",
                "medicines": "Consult doctor immediately",
            },
            "medium": {
                "keywords": ["fever", "severe cough", "persistent", "3 days"],
                "advice": "Use cough syrups, rest adequately. If cough persists >1 week, consult a doctor.",
                "medicines": "Dextromethorphan-based cough syrup. Throat lozenges for sore throat.",
            },
            "low": {
                "keywords": ["mild", "runny nose", "light cough", "few days"],
                "advice": "Try steam inhalation, drink warm fluids (tea with honey), rest.",
                "medicines": "Over-the-counter throat lozenges if needed",
            }
        },
        "diet": "Warm soups, herbal teas (ginger, turmeric), citrus fruits, honey, chicken broth.",
        "disclaimer": "⚠️ This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.",
    },
    "headache": {
        "name": "Headache",
        "emergency_keywords": ["sudden", "severe", "blurred vision", "confusion", "stiff neck", "seizure"],
        "questions": [
            "Where is the pain located (front, back, one side)?",
            "Is the pain mild, moderate, or severe?",
            "Do you feel nausea or vomiting?",
            "Are you sensitive to light or noise?",
            "How long does the headache last?",
        ],
        "severity_criteria": {
            "high": {
                "keywords": ["sudden", "severe", "worst", "confusion", "vision", "stiff neck"],
                "advice": "⚠️ Sudden severe headache with vision changes or confusion requires immediate medical attention.",
                "medicines": "Do not self-medicate. Seek doctor immediately.",
            },
            "medium": {
                "keywords": ["moderate", "lasting hours", "nausea", "vomiting"],
                "advice": "Rest in a dark, quiet room. Take ibuprofen or acetaminophen. If persists >48 hours, consult doctor.",
                "medicines": "Ibuprofen 400mg every 6-8 hours OR Acetaminophen 500mg every 6 hours",
            },
            "low": {
                "keywords": ["mild", "occasional", "stress", "fatigue"],
                "advice": "Drink plenty of water, rest, reduce screen time, massage temples, take a warm shower.",
                "medicines": "Acetaminophen 500mg if needed (no more than 3 times daily)",
            }
        },
        "diet": "Regular meals, avoid caffeine and alcohol, lots of water, magnesium-rich foods (nuts, seeds).",
        "disclaimer": "⚠️ This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.",
    },
    "stomach pain": {
        "name": "Stomach Pain",
        "emergency_keywords": ["severe", "unbearable", "vomiting", "blood", "acute", "sharp"],
        "questions": [
            "Where is the pain located (upper, lower, center)?",
            "Is it sharp pain or dull ache?",
            "Do you have vomiting or diarrhea?",
            "Does pain occur after eating?",
            "Is the pain continuous or comes and goes?",
        ],
        "severity_criteria": {
            "high": {
                "keywords": ["severe", "unbearable", "sharp", "vomiting", "blood"],
                "advice": "⚠️ Severe abdominal pain with vomiting requires immediate medical evaluation.",
                "medicines": "Do not take any medicine without doctor's advice",
            },
            "medium": {
                "keywords": ["moderate", "after meals", "diarrhea", "bloating"],
                "advice": "Eat light foods, drink ORS (Oral Rehydration Solution). Avoid oily and spicy food for 2-3 days.",
                "medicines": "Antacids like Tums or Milk of Magnesia. Avoid NSAIDs without doctor's advice.",
            },
            "low": {
                "keywords": ["mild", "occasional", "light", "feeling better"],
                "advice": "Drink water, eat bland foods (rice, toast), rest. Monitor symptoms.",
                "medicines": "Gentle antacid if needed. Stay hydrated.",
            }
        },
        "diet": "BRAT diet: Bananas, Rice, Applesauce, Toast. Avoid dairy, fatty foods, caffeine, alcohol.",
        "disclaimer": "⚠️ This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.",
    },
    "dizziness": {
        "name": "Dizziness",
        "emergency_keywords": ["fainting", "blacking out", "severe", "falling", "unable to move"],
        "questions": [
            "When do you feel dizzy (standing, after eating, anytime)?",
            "Do you feel weak or tired?",
            "Have you eaten properly today?",
            "Do you feel like fainting?",
            "Do you have headache or blurred vision?",
        ],
        "severity_criteria": {
            "high": {
                "keywords": ["fainting", "blacking", "falling", "losing consciousness"],
                "advice": "⚠️ If experiencing fainting or loss of consciousness, seek immediate medical help.",
                "medicines": "Do not self-medicate. Seek doctor immediately.",
            },
            "medium": {
                "keywords": ["severe", "weakness", "cannot stand", "blurred vision"],
                "advice": "Sit or lie down immediately. Drink water slowly. Consult doctor if it persists.",
                "medicines": "Take supplements for anemia if advised by doctor (iron tablets, B12)",
            },
            "low": {
                "keywords": ["mild", "occasional", "after standing", "feeling better"],
                "advice": "Drink plenty of water, eat regular meals, stand up slowly, get adequate sleep.",
                "medicines": "No immediate medication needed. Improve hydration and nutrition.",
            }
        },
        "diet": "Iron-rich foods: leafy greens, red meat, beans. Include vitamin C for iron absorption. Frequent small meals.",
        "disclaimer": "⚠️ This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.",
    },
    "breathing problem": {
        "name": "Breathing Problem",
        "emergency_keywords": ["cannot breathe", "shortness", "severe", "chest pain", "gasping"],
        "questions": [
            "Do you feel shortness of breath at rest or during activity?",
            "Is it sudden or gradual?",
            "Do you have chest pain?",
            "Do you have asthma history?",
            "Can you speak normally without difficulty?",
        ],
        "severity_criteria": {
            "high": {
                "keywords": ["severe", "cannot breathe", "gasping", "chest pain", "emergency"],
                "advice": "🚨 EMERGENCY: Seek medical help IMMEDIATELY! This could be life-threatening.",
                "medicines": "Do not wait. Call emergency services (911 or local emergency number)",
            },
            "medium": {
                "keywords": ["moderate", "on exertion", "anxiety", "persistent"],
                "advice": "Sit upright, breathe slowly. If you have an inhaler, use it. Consult doctor soon.",
                "medicines": "Use prescribed inhaler if available. Do not delay doctor's visit.",
            },
            "low": {
                "keywords": ["mild", "after exercise", "occasional", "feeling better"],
                "advice": "Sit down, take deep slow breaths. Rest for a while. Avoid strenuous activity.",
                "medicines": "No medication for mild cases. Focus on rest and breathing exercises.",
            }
        },
        "diet": "Light foods, avoid heavy meals. Plenty of fluids. Avoid allergens.",
        "disclaimer": "⚠️ This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.",
    },
    "stress/anxiety": {
        "name": "Stress / Anxiety",
        "emergency_keywords": ["panic attack", "chest pain", "suicidal", "harming"],
        "questions": [
            "Do you feel nervous or restless most of the time?",
            "Are you sleeping properly?",
            "Do you feel overthinking or racing thoughts?",
            "Do you experience panic attacks (sudden intense fear)?",
            "Do you feel tired, low energy, or unmotivated?",
        ],
        "severity_criteria": {
            "high": {
                "keywords": ["panic attack", "severe", "unable to function", "suicidal"],
                "advice": "⚠️ Please consult a mental health professional or therapist immediately.",
                "medicines": "Consult psychiatrist for possible medication",
            },
            "medium": {
                "keywords": ["moderate", "affecting work", "persistent", "affecting sleep"],
                "advice": "Consider professional counseling or therapy. Practice mindfulness and meditation.",
                "medicines": "Consult doctor for possible short-term anxiety management if needed",
            },
            "low": {
                "keywords": ["mild", "situational", "manageable", "occasional"],
                "advice": "Practice relaxation techniques: deep breathing, meditation, yoga, exercise, listen to music.",
                "medicines": "No medication for mild cases. Focus on lifestyle changes.",
            }
        },
        "diet": "Balanced nutrition. Reduce caffeine and sugar. Omega-3 rich foods: fish, walnuts, flaxseeds.",
        "disclaimer": "⚠️ This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.",
    },
}


# Old SERIOUS_KEYWORDS and COMMON_SYMPTOMS for backward compatibility
SERIOUS_KEYWORDS = {
    "chest pain",
    "shortness of breath",
    "difficulty breathing",
    "severe headache",
    "fainting",
    "unconscious",
    "blood in vomit",
    "stroke",
    "heart attack",
    "high fever",
}

COMMON_SYMPTOMS = {
    "fever",
    "cold",
    "cough",
    "headache",
    "sore throat",
    "runny nose",
    "body pain",
    "fatigue",
    "stomach pain",
    "dizziness",
    "breathing problem",
    "stress",
    "anxiety",
}

# Legacy TRAINING_DATA kept for backward compatibility
TRAINING_DATA = {
    "fever": {
        "response": "For fever, rest, drink plenty of fluids, and take acetaminophen (Tylenol) if needed for comfort.",
        "follow_up": "How long have you had the fever? Is it above 103°F? Any other symptoms like rash or difficulty breathing?",
        "medicine": "Acetaminophen (Tylenol) - follow dosage instructions. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Eat light foods like soups, fruits, and vegetables. Avoid heavy or spicy foods.",
        "emergency": "Seek immediate medical help if fever is >104°F, lasts >3 days, or with severe symptoms."
    },
    "cold": {
        "response": "For common cold: rest, drink fluids, use saline nasal spray. Symptoms usually improve in 7-10 days.",
        "follow_up": "Do you have a cough, sore throat, or congestion? How long have symptoms lasted?",
        "medicine": "Decongestants or antihistamines if needed. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Warm soups, herbal teas, fruits rich in vitamin C like oranges and berries.",
        "emergency": "See doctor if symptoms worsen or last >10 days."
    },
    "cough": {
        "response": "For cough: stay hydrated, use honey for sore throat, use a humidifier.",
        "follow_up": "Is the cough dry or productive? Any blood in sputum? How long has it lasted?",
        "medicine": "Cough syrups with dextromethorphan. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Warm fluids, avoid irritants like smoke. Honey and lemon tea.",
        "emergency": "Seek help if cough is severe, with chest pain, or shortness of breath."
    },
    "headache": {
        "response": "For headache: rest in a dark room, hydrate, use over-the-counter pain relievers.",
        "follow_up": "Is it a migraine? Any vision changes, nausea, or neck stiffness?",
        "medicine": "Ibuprofen or aspirin. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Avoid triggers like caffeine, alcohol. Eat regular meals.",
        "emergency": "Emergency if sudden severe headache with confusion or seizures."
    },
    "sore throat": {
        "response": "For sore throat: gargle salt water, use lozenges, rest your voice.",
        "follow_up": "Any difficulty swallowing, fever, or rash? How long has it been sore?",
        "medicine": "Throat lozenges or sprays. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Soft foods, warm soups, avoid acidic foods.",
        "emergency": "See doctor if severe pain, high fever, or breathing difficulty."
    },
    "runny nose": {
        "response": "For runny nose: use saline spray, antihistamines, rest.",
        "follow_up": "Is it clear or colored discharge? Any fever or sinus pain?",
        "medicine": "Antihistamines like loratadine. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Stay hydrated, spicy foods may help clear sinuses.",
        "emergency": "Consult doctor if lasts >10 days or with severe symptoms."
    },
    "body pain": {
        "response": "For body aches: rest, apply warm compress, use OTC pain relievers.",
        "follow_up": "Where is the pain? Any swelling, redness, or injury?",
        "medicine": "Ibuprofen or acetaminophen. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Anti-inflammatory foods like turmeric, ginger, berries.",
        "emergency": "See doctor if pain is severe, with fever, or after injury."
    },
    "fatigue": {
        "response": "For fatigue: ensure good sleep, balanced diet, light exercise.",
        "follow_up": "How long have you felt tired? Any weight changes or other symptoms?",
        "medicine": "None specific, but B-vitamins if deficient. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Balanced meals with proteins, carbs, healthy fats. Iron-rich foods if anemic.",
        "emergency": "See doctor if chronic fatigue with other concerning symptoms."
    },
    "stomach pain": {
        "response": "For stomach pain: avoid heavy foods, drink water, use antacids.",
        "follow_up": "Where is the pain? Any vomiting, diarrhea, or blood?",
        "medicine": "Antacids like Tums. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "BRAT diet: bananas, rice, applesauce, toast. Avoid dairy, caffeine.",
        "emergency": "Emergency if severe pain, blood in stool, or signs of appendicitis."
    },
    "nausea": {
        "response": "For nausea: small sips of water, ginger tea, rest.",
        "follow_up": "Any vomiting? Related to food, pregnancy, or medication?",
        "medicine": "Anti-nausea like meclizine. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Crackers, ginger, avoid strong smells and heavy foods.",
        "emergency": "See doctor if persistent, with dehydration, or severe symptoms."
    },
    "diarrhea": {
        "response": "For diarrhea: stay hydrated with electrolyte drinks, BRAT diet.",
        "follow_up": "How many times a day? Any blood or mucus? Recent travel or food?",
        "medicine": "Loperamide (Imodium). Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "BRAT diet, probiotics like yogurt. Avoid dairy, fatty foods.",
        "emergency": "Seek help if bloody, >3 days, or with dehydration."
    },
    "constipation": {
        "response": "For constipation: increase fiber, drink water, exercise.",
        "follow_up": "How long since last bowel movement? Any pain or blood?",
        "medicine": "Fiber supplements or laxatives like psyllium. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "High-fiber foods: fruits, vegetables, whole grains. Prunes, kiwi.",
        "emergency": "See doctor if severe pain or no relief after home remedies."
    },
    "back pain": {
        "response": "For back pain: rest, ice/heat, gentle stretches.",
        "follow_up": "Is it upper or lower back? Any numbness or weakness?",
        "medicine": "Ibuprofen for inflammation. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Anti-inflammatory diet: omega-3 rich foods, avoid processed foods.",
        "emergency": "Emergency if pain after fall, with leg weakness, or bladder issues."
    },
    "joint pain": {
        "response": "For joint pain: rest affected joint, OTC anti-inflammatories.",
        "follow_up": "Which joints? Any swelling, redness, or morning stiffness?",
        "medicine": "Ibuprofen or naproxen. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Anti-inflammatory foods: fatty fish, nuts, olive oil.",
        "emergency": "See doctor for swelling, redness, or if acute injury."
    },
    "rash": {
        "response": "For rash: avoid irritants, moisturize, use antihistamines.",
        "follow_up": "Where is the rash? Itchy? Any fever or other symptoms?",
        "medicine": "Antihistamines like cetirizine. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Avoid allergens, eat anti-inflammatory foods.",
        "emergency": "Seek help if rash spreads rapidly, with fever, or breathing issues."
    },
    "allergy": {
        "response": "For allergies: avoid triggers, use antihistamines, nasal sprays.",
        "follow_up": "What triggers? Symptoms like sneezing, itchy eyes?",
        "medicine": "Loratadine or cetirizine. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Local honey, probiotics. Avoid common allergens.",
        "emergency": "Emergency for severe allergic reaction (anaphylaxis)."
    },
    "insomnia": {
        "response": "For insomnia: consistent sleep schedule, relaxation techniques.",
        "follow_up": "How long? Any stress, caffeine, or medical conditions?",
        "medicine": "Melatonin supplements. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Avoid caffeine, heavy meals before bed. Chamomile tea.",
        "emergency": "See doctor if insomnia affects daily life significantly."
    },
    "anxiety": {
        "response": "For anxiety: deep breathing, exercise, talk to someone.",
        "follow_up": "How often? Any panic attacks or physical symptoms?",
        "medicine": "None for mild, but therapy recommended. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Magnesium-rich foods, avoid caffeine. Balanced diet.",
        "emergency": "Seek help for severe anxiety or panic attacks."
    },
    "depression": {
        "response": "For depression: talk to loved ones, exercise, healthy diet.",
        "follow_up": "How long? Any suicidal thoughts or changes in appetite?",
        "medicine": "None here, professional help needed. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Omega-3s, B-vitamins, regular meals.",
        "emergency": "Hotline or ER for suicidal thoughts."
    },
    "stress": {
        "response": "For stress: relaxation techniques, hobbies, social support.",
        "follow_up": "What's causing stress? Physical symptoms?",
        "medicine": "None specific. Disclaimer: This is not medical advice; consult a doctor.",
        "diet": "Healthy eating, avoid alcohol. Magnesium, vitamin C.",
        "emergency": "Seek professional help if overwhelming."
    },
}


def analyze_input(state: AgentState) -> AgentState:
    text = state["user_input"].lower().strip()
    state["analysis"] = text
    return state


def decide_response_type(state: AgentState) -> AgentState:
    text = state["analysis"]

    if any(keyword in text for keyword in SERIOUS_KEYWORDS):
        state["response_type"] = "serious_symptoms"
        return state

    if any(symptom in text for symptom in COMMON_SYMPTOMS):
        state["response_type"] = "common_issue"
        return state

    # Fallback for general health questions.
    state["response_type"] = "common_issue"
    return state


def generate_response(state: AgentState) -> AgentState:
    message = state["user_input"].lower()
    chat_history = state.get("chat_history", [])

    # Determine if this is a follow-up based on recent history
    is_follow_up = False
    last_ai_message = None
    current_symptom = None
    
    for msg in reversed(chat_history):
        if msg.get("ai_response"):
            last_ai_message = msg["ai_response"]
            break
    
    # Check if the last AI message asked a question (contains "?") or provided medical advice
    if last_ai_message and ("?" in last_ai_message or "medicine" in last_ai_message.lower() or "diet" in last_ai_message.lower()):
        is_follow_up = True
        # Try to determine the current symptom from the conversation history
        for msg in reversed(chat_history):
            ai_msg = msg.get("ai_response", "")
            for symptom in TRAINING_DATA.keys():
                if symptom in ai_msg.lower():
                    current_symptom = symptom
                    break
            if current_symptom:
                break

    if state["response_type"] == "serious_symptoms":
        state["response"] = (
            "Your message may indicate serious symptoms. "
            "Please consult a doctor or visit the nearest emergency center as soon as possible. "
            "If symptoms are severe or sudden, seek urgent medical help immediately."
        )
        return state

    # Check for specific training data matches or follow-up answers
    symptom_found = None
    for problem, data in TRAINING_DATA.items():
        if problem in message:
            symptom_found = problem
            break
    
    # If no direct symptom match but this is a follow-up, use the current symptom
    if not symptom_found and is_follow_up and current_symptom:
        symptom_found = current_symptom

    if symptom_found:
        data = TRAINING_DATA[symptom_found]
        if is_follow_up:
            # This is a follow-up answer - provide next level of information
            # Check what type of answer this seems to be
            if any(word in message for word in ["day", "days", "week", "weeks", "hour", "hours"]):
                # Duration answer - provide medicine info
                medicine = data.get("medicine", "")
                diet = data.get("diet", "")
                response_parts = [medicine]
                if diet:
                    response_parts.append(f"Diet recommendations: {diet}")
                state["response"] = "\n\n".join(response_parts)
            elif any(word in message for word in ["yes", "no", "above", "below", "high", "low"]):
                # Yes/no or severity answer - provide emergency info
                emergency = data.get("emergency", "")
                state["response"] = emergency
            else:
                # General follow-up - provide diet info
                diet = data.get("diet", "")
                emergency = data.get("emergency", "")
                response_parts = []
                if diet:
                    response_parts.append(f"Diet recommendations: {diet}")
                if emergency:
                    response_parts.append(f"When to seek help: {emergency}")
                state["response"] = "\n\n".join(response_parts) if response_parts else "Please consult a healthcare professional for personalized advice."
        else:
            # First time mentioning symptom - provide basic response and first follow-up
            response_parts = [data["response"]]
            follow_up = data.get("follow_up", "")
            if follow_up:
                # Split follow-up questions and take only the first one
                first_question = follow_up.split("? ")[0] + "?"
                response_parts.append(f"\n\n{first_question}")
            state["response"] = "\n\n".join(response_parts)
        return state

    # Fallback
    state["response"] = (
        f"Thanks for sharing: '{state['user_input']}'. "
        "This seems like a common health concern. "
        "Basic suggestions: drink enough water, take rest, eat light meals, "
        "and monitor your symptoms for 24-48 hours. "
        "If symptoms get worse or do not improve, consult a healthcare professional."
    )
    return state


def detailed_analysis(state: AgentState) -> AgentState:
    # For now, just pass through, but could add logic to ask follow-ups
    return state


def build_agent():
    graph = StateGraph(AgentState)
    graph.add_node("analyze_input", analyze_input)
    graph.add_node("decide_response_type", decide_response_type)
    graph.add_node("detailed_analysis", detailed_analysis)
    graph.add_node("generate_response", generate_response)

    graph.set_entry_point("analyze_input")
    graph.add_edge("analyze_input", "decide_response_type")
    graph.add_edge("decide_response_type", "detailed_analysis")
    graph.add_edge("detailed_analysis", "generate_response")
    graph.add_edge("generate_response", END)

    return graph.compile()


health_agent = build_agent()


def run_health_agent(user_input: str, chat_history: list = None) -> dict:
    if chat_history is None:
        chat_history = []
    
    initial_state: AgentState = {
        "user_input": user_input,
        "analysis": "",
        "response_type": "common_issue",
        "response": "",
        "current_symptom": None,
        "current_stage": 1,
        "conversation_context": {},
        "chat_history": chat_history,
    }
    result = health_agent.invoke(initial_state)
    return {
        "ai_response": result["response"],
        "response_type": result["response_type"],
    }
