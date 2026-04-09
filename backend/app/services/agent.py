from typing import Literal, TypedDict, Optional
import re
from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    user_input: str
    analysis: str
    response_type: Literal["common_issue", "serious_symptoms", "symptom_checker"]
    response: str
    current_symptom: str | None
    current_stage: int  # Which question number we're on (0-4)
    conversation_context: dict
    chat_history: list
    symptom_answers: dict
    severity: str
    emergency: bool


# Comprehensive symptom checker database
SYMPTOM_CHECKER_DB = {
    "fever": {
        "name": "Fever",
        "keywords": ["fever", "high temperature", "temp", "warm", "hot"],
        "emergency_keywords": ["104", "105", "unbearable", "delirious", "unconscious", "seizure"],
        "questions": [
            "How many days have you had the fever?",
            "What is your temperature (in °F)?",
            "Do you have chills or sweating?",
            "Do you feel body pain or weakness?",
            "Do you have headache or sore throat?",
        ],
        "severity_criteria": {
            "high": {
                "keywords": ["104", "105", "3 days", "severe", "unbearable", "seizure"],
                "threshold": lambda answers: any("104" in str(a) or "105" in str(a) for a in answers.values()) or len(answers) >= 4,
                "advice": "⚠️ Seek medical help immediately. High fever can lead to complications.",
                "medicines": "Consult doctor before taking any medicine",
            },
            "medium": {
                "keywords": ["2 days", "102", "103", "body pain", "weakness"],
                "threshold": lambda answers: any("102" in str(a) or "103" in str(a) for a in answers.values()),
                "advice": "Monitor your temperature closely. Continue hydration and rest. Take acetaminophen if temperature exceeds 101°F.",
                "medicines": "Acetaminophen (Tylenol) 500mg every 6 hours (max 2000mg/day)",
            },
            "low": {
                "keywords": ["1 day", "99", "100", "101", "feeling fine"],
                "threshold": lambda answers: True,  # Default
                "advice": "Drink plenty of fluids (water, coconut water, warm fluids). Take rest. Use paracetamol if uncomfortable.",
                "medicines": "Paracetamol 500mg every 6 hours if needed",
            }
        },
        "diet": "Light foods like soups, broths, fruits (oranges, bananas), rice. Avoid heavy and spicy foods.",
        "disclaimer": "⚠️ This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.",
    },
    "cold/cough": {
        "name": "Cold / Cough",
        "keywords": ["cold", "cough", "coughing", "coughed"],
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
                "threshold": lambda answers: any(word in str(answers).lower() for word in ["breathing", "difficulty", "chest pain"]),
                "advice": "⚠️ If experiencing breathing difficulty or chest pain, seek medical help immediately.",
                "medicines": "Consult doctor immediately",
            },
            "medium": {
                "keywords": ["fever", "severe cough", "persistent", "3 days"],
                "threshold": lambda answers: len(answers) >= 3,
                "advice": "Use cough syrups, rest adequately. If cough persists >1 week, consult a doctor.",
                "medicines": "Dextromethorphan-based cough syrup. Throat lozenges for sore throat.",
            },
            "low": {
                "keywords": ["mild", "runny nose", "light cough", "few days"],
                "threshold": lambda answers: True,
                "advice": "Try steam inhalation, drink warm fluids (tea with honey), rest.",
                "medicines": "Over-the-counter throat lozenges if needed",
            }
        },
        "diet": "Warm soups, herbal teas (ginger, turmeric), citrus fruits, honey, chicken broth.",
        "disclaimer": "⚠️ This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.",
    },
    "headache": {
        "name": "Headache",
        "keywords": ["headache", "head pain", "migraine", "head ache"],
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
                "threshold": lambda answers: any(word in str(answers).lower() for word in ["sudden", "severe", "confusion"]),
                "advice": "⚠️ Sudden severe headache with vision changes or confusion requires immediate medical attention.",
                "medicines": "Do not self-medicate. Seek doctor immediately.",
            },
            "medium": {
                "keywords": ["moderate", "lasting hours", "nausea", "vomiting"],
                "threshold": lambda answers: any(word in str(answers).lower() for word in ["moderate", "nausea", "vomiting"]),
                "advice": "Rest in a dark, quiet room. Take ibuprofen or acetaminophen. If persists >48 hours, consult doctor.",
                "medicines": "Ibuprofen 400mg every 6-8 hours OR Acetaminophen 500mg every 6 hours",
            },
            "low": {
                "keywords": ["mild", "occasional", "stress", "fatigue"],
                "threshold": lambda answers: True,
                "advice": "Drink plenty of water, rest, reduce screen time, massage temples, take a warm shower.",
                "medicines": "Acetaminophen 500mg if needed (no more than 3 times daily)",
            }
        },
        "diet": "Regular meals, avoid caffeine and alcohol, lots of water, magnesium-rich foods (nuts, seeds).",
        "disclaimer": "⚠️ This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.",
    },
    "stomach pain": {
        "name": "Stomach Pain",
        "keywords": ["stomach pain", "stomach ache", "abdominal pain", "belly pain", "stomach"],
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
                "threshold": lambda answers: any(word in str(answers).lower() for word in ["severe", "unbearable", "sharp", "vomiting", "blood"]),
                "advice": "⚠️ Severe abdominal pain with vomiting requires immediate medical evaluation.",
                "medicines": "Do not take any medicine without doctor's advice",
            },
            "medium": {
                "keywords": ["moderate", "after meals", "diarrhea", "bloating"],
                "threshold": lambda answers: len(answers) >= 2,
                "advice": "Eat light foods, drink ORS (Oral Rehydration Solution). Avoid oily and spicy food for 2-3 days.",
                "medicines": "Antacids like Tums or Milk of Magnesia. Avoid NSAIDs without doctor's advice.",
            },
            "low": {
                "keywords": ["mild", "occasional", "light", "feeling better"],
                "threshold": lambda answers: True,
                "advice": "Drink water, eat bland foods (rice, toast), rest. Monitor symptoms.",
                "medicines": "Gentle antacid if needed. Stay hydrated.",
            }
        },
        "diet": "BRAT diet: Bananas, Rice, Applesauce, Toast. Avoid dairy, fatty foods, caffeine, alcohol.",
        "disclaimer": "⚠️ This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.",
    },
    "dizziness": {
        "name": "Dizziness",
        "keywords": ["dizzy", "dizziness", "vertigo", "lightheaded", "feeling faint"],
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
                "threshold": lambda answers: any(word in str(answers).lower() for word in ["fainting", "blacking", "falling", "consciousness"]),
                "advice": "⚠️ If experiencing fainting or loss of consciousness, seek immediate medical help.",
                "medicines": "Do not self-medicate. Seek doctor immediately.",
            },
            "medium": {
                "keywords": ["severe", "weakness", "cannot stand", "blurred vision"],
                "threshold": lambda answers: len(answers) >= 2,
                "advice": "Sit or lie down immediately. Drink water slowly. Consult doctor if it persists.",
                "medicines": "Take supplements for anemia if advised by doctor (iron tablets, B12)",
            },
            "low": {
                "keywords": ["mild", "occasional", "after standing", "feeling better"],
                "threshold": lambda answers: True,
                "advice": "Drink plenty of water, eat regular meals, stand up slowly, get adequate sleep.",
                "medicines": "No immediate medication needed. Improve hydration and nutrition.",
            }
        },
        "diet": "Iron-rich foods: leafy greens, red meat, beans. Include vitamin C for iron absorption. Frequent small meals.",
        "disclaimer": "⚠️ This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.",
    },
    "breathing problem": {
        "name": "Breathing Problem",
        "keywords": ["breathing", "breathe", "breath", "shortness", "dyspnea"],
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
                "threshold": lambda answers: any(word in str(answers).lower() for word in ["severe", "cannot", "gasping", "chest pain"]),
                "advice": "🚨 EMERGENCY: Seek medical help IMMEDIATELY! This could be life-threatening.",
                "medicines": "Do not wait. Call emergency services (911 or local emergency number)",
            },
            "medium": {
                "keywords": ["moderate", "on exertion", "anxiety", "persistent"],
                "threshold": lambda answers: len(answers) >= 2,
                "advice": "Sit upright, breathe slowly. If you have an inhaler, use it. Consult doctor soon.",
                "medicines": "Use prescribed inhaler if available. Do not delay doctor's visit.",
            },
            "low": {
                "keywords": ["mild", "after exercise", "occasional", "feeling better"],
                "threshold": lambda answers: True,
                "advice": "Sit down, take deep slow breaths. Rest for a while. Avoid strenuous activity.",
                "medicines": "No medication for mild cases. Focus on rest and breathing exercises.",
            }
        },
        "diet": "Light foods, avoid heavy meals. Plenty of fluids. Avoid allergens.",
        "disclaimer": "⚠️ This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.",
    },
    "stress/anxiety": {
        "name": "Stress / Anxiety",
        "keywords": ["stress", "anxiety", "anxious", "worried", "panic"],
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
                "threshold": lambda answers: any(word in str(answers).lower() for word in ["panic", "severe", "suicidal"]),
                "advice": "⚠️ Please consult a mental health professional or therapist immediately.",
                "medicines": "Consult psychiatrist for possible medication",
            },
            "medium": {
                "keywords": ["moderate", "affecting work", "persistent", "affecting sleep"],
                "threshold": lambda answers: len(answers) >= 2,
                "advice": "Consider professional counseling or therapy. Practice mindfulness and meditation.",
                "medicines": "Consult doctor for possible short-term anxiety management if needed",
            },
            "low": {
                "keywords": ["mild", "situational", "manageable", "occasional"],
                "threshold": lambda answers: True,
                "advice": "Practice relaxation techniques: deep breathing, meditation, yoga, exercise, listen to music.",
                "medicines": "No medication for mild cases. Focus on lifestyle changes.",
            }
        },
        "diet": "Balanced nutrition. Reduce caffeine and sugar. Omega-3 rich foods: fish, walnuts, flaxseeds.",
        "disclaimer": "⚠️ This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.",
    },
}


# Keywords for quick detection
SERIOUS_KEYWORDS = {
    "chest pain", "shortness of breath", "difficulty breathing", "severe headache",
    "fainting", "unconscious", "blood in vomit", "stroke", "heart attack", "high fever",
    "cannot breathe", "gasping", "severe", "emergency", "critical"
}

COMMON_SYMPTOMS = {
    "fever", "cold", "cough", "headache", "sore throat", "runny nose",
    "body pain", "fatigue", "stomach pain", "dizziness", "breathing",
    "stress", "anxiety",
}


def detect_symptom(text: str) -> Optional[str]:
    """Detect which symptom is being discussed"""
    text_lower = text.lower()
    
    for symptom_key, symptom_data in SYMPTOM_CHECKER_DB.items():
        for keyword in symptom_data["keywords"]:
            if keyword in text_lower:
                return symptom_key
    
    return None


def detect_emergency(text: str, symptom_key: Optional[str]) -> bool:
    """Check if any emergency keywords are mentioned"""
    text_lower = text.lower()
    
    # Check global serious keywords
    if any(keyword in text_lower for keyword in SERIOUS_KEYWORDS):
        return True
    
    # Check symptom-specific emergency keywords
    if symptom_key and symptom_key in SYMPTOM_CHECKER_DB:
        symptom_data = SYMPTOM_CHECKER_DB[symptom_key]
        if any(keyword in text_lower for keyword in symptom_data["emergency_keywords"]):
            return True
    
    return False


def classify_severity(symptom_key: str, answers: dict) -> str:
    """Classify severity based on collected answers"""
    if symptom_key not in SYMPTOM_CHECKER_DB:
        return "medium"
    
    symptom_data = SYMPTOM_CHECKER_DB[symptom_key]
    severity_criteria = symptom_data["severity_criteria"]
    
    # Check from high to low
    for severity_level in ["high", "medium", "low"]:
        criteria = severity_criteria[severity_level]
        threshold_fn = criteria.get("threshold")
        
        if threshold_fn:
            try:
                if threshold_fn(answers):
                    return severity_level
            except:
                pass
    
    return "low"


def get_next_question(symptom_key: str, stage: int) -> Optional[str]:
    """Get the next question for a given symptom"""
    if symptom_key not in SYMPTOM_CHECKER_DB:
        return None
    
    symptom_data = SYMPTOM_CHECKER_DB[symptom_key]
    questions = symptom_data["questions"]
    
    if stage < len(questions):
        return questions[stage]
    
    return None


def get_symptom_advice(symptom_key: str, severity: str) -> dict:
    """Get advice based on symptom and severity"""
    if symptom_key not in SYMPTOM_CHECKER_DB:
        return {}
    
    symptom_data = SYMPTOM_CHECKER_DB[symptom_key]
    severity_data = symptom_data["severity_criteria"].get(severity, symptom_data["severity_criteria"]["low"])
    
    return {
        "severity": severity,
        "advice": severity_data["advice"],
        "medicines": severity_data["medicines"],
        "diet": symptom_data["diet"],
        "disclaimer": symptom_data["disclaimer"]
    }


def analyze_input(state: AgentState) -> AgentState:
    text = state["user_input"].lower().strip()
    state["analysis"] = text
    return state


def decide_response_type(state: AgentState) -> AgentState:
    text = state["analysis"]
    
    # Check for emergency
    if any(keyword in text for keyword in SERIOUS_KEYWORDS):
        state["response_type"] = "serious_symptoms"
        return state
    
    # Check if we're in the middle of a symptom checker conversation
    # Look at both the current_symptom field and the chat history
    if state.get("current_symptom"):
        # We already have a symptom being discussed
        state["response_type"] = "symptom_checker"
        return state
    
    # Check if starting new symptom checker
    symptom = detect_symptom(state["user_input"])
    if symptom:
        state["response_type"] = "symptom_checker"
        state["current_symptom"] = symptom
        state["current_stage"] = 0
        return state
    
    # Default
    state["response_type"] = "common_issue"
    return state


def generate_response(state: AgentState) -> AgentState:
    if state["response_type"] == "serious_symptoms":
        state["response"] = (
            "⚠️ Based on your message, you may have serious symptoms. "
            "Please consult a doctor or visit the nearest emergency center immediately. "
            "If symptoms are severe, call emergency services (911 or local number) without delay."
        )
        state["severity"] = "high"
        state["emergency"] = True
        return state
    
    if state["response_type"] == "symptom_checker":
        symptom_key = state["current_symptom"]
        
        if not symptom_key:
            symptom_key = detect_symptom(state["user_input"])
            state["current_symptom"] = symptom_key
        
        if not symptom_key:
            state["response"] = (
                "I'm not sure which symptom you're referring to. "
                "Please describe your symptoms more clearly. "
                "Common symptoms I can help with: fever, cold/cough, headache, stomach pain, dizziness, breathing problems, stress/anxiety."
            )
            return state
        
        symptom_data = SYMPTOM_CHECKER_DB[symptom_key]
        
        # Check for emergency keywords
        if detect_emergency(state["user_input"], symptom_key):
            state["emergency"] = True
            severity_data = symptom_data["severity_criteria"]["high"]
            state["severity"] = "high"
            state["response"] = severity_data["advice"]
            return state
        
        # Track answers
        if "symptom_answers" not in state:
            state["symptom_answers"] = {}
        
        # If this is not the first message about this symptom, store the answer
        if state["current_stage"] > 0:
            state["symptom_answers"][f"q{state['current_stage']}"] = state["user_input"]
        
        # Get current question stage
        current_stage = state.get("current_stage", 0)
        next_question = None
        
        # Determine if we should ask another question or provide advice
        if current_stage < len(symptom_data["questions"]):
            # Ask next question
            next_question = symptom_data["questions"][current_stage]
            state["current_stage"] = current_stage + 1
            state["response"] = f"**{symptom_data['name']} Assessment**\n\n{next_question}"
        else:
            # We've asked all questions, provide assessment
            severity = classify_severity(symptom_key, state["symptom_answers"])
            state["severity"] = severity
            
            advice_data = get_symptom_advice(symptom_key, severity)
            
            response_parts = [
                f"**{symptom_data['name']} - {severity.upper()} Severity**",
                "",
                f"📋 **Advice:** {advice_data['advice']}",
                f"💊 **Medicines:** {advice_data['medicines']}",
                f"🥗 **Diet:** {advice_data['diet']}",
                "",
                f"_{advice_data['disclaimer']}_"
            ]
            
            state["response"] = "\n".join(response_parts)
        
        return state
    
    # Fallback for common_issue
    symptom = detect_symptom(state["user_input"])
    if symptom:
        symptom_data = SYMPTOM_CHECKER_DB[symptom]
        state["response"] = (
            f"I see you have **{symptom_data['name']}**. "
            f"Let me ask you a few questions to better understand your condition.\n\n"
            f"{symptom_data['questions'][0]}"
        )
        state["current_symptom"] = symptom
        state["current_stage"] = 1
        state["response_type"] = "symptom_checker"
        return state
    
    # Generic fallback
    state["response"] = (
        "Thanks for sharing that. This seems like a health concern. "
        "To help you better, could you describe your main symptom? "
        "I can help with: fever, cold/cough, headache, stomach pain, dizziness, breathing problems, or stress/anxiety."
    )
    return state


def build_agent():
    graph = StateGraph(AgentState)
    graph.add_node("analyze_input", analyze_input)
    graph.add_node("decide_response_type", decide_response_type)
    graph.add_node("generate_response", generate_response)
    
    graph.set_entry_point("analyze_input")
    graph.add_edge("analyze_input", "decide_response_type")
    graph.add_edge("decide_response_type", "generate_response")
    graph.add_edge("generate_response", END)
    
    return graph.compile()


health_agent = build_agent()


def run_health_agent(user_input: str, chat_history: list = None) -> dict:
    if chat_history is None:
        chat_history = []
    
    # Try to determine the current symptom and stage from chat history
    current_symptom = None
    current_stage = 0
    symptom_answers = {}
    
    # Look through all messages to find ongoing symptom checking
    for msg_idx, msg in enumerate(chat_history):
        ai_response = msg.get("ai_response", "").lower()
        
        # Try to detect symptom from AI response by checking each symptom's name
        detected_symptom = None
        for symptom_key, symptom_data in SYMPTOM_CHECKER_DB.items():
            symptom_name_lower = symptom_data["name"].lower()
            # Look for "Fever Assessment" type patterns
            if f"{symptom_name_lower} assessment" in ai_response:
                detected_symptom = symptom_key
                break
            # Also check for symptom in keywords
            elif any(kw in ai_response for kw in symptom_data["keywords"]):
                detected_symptom = symptom_key
                break
        
        # If we found a symptom being discussed, track it
        if detected_symptom:
            current_symptom = detected_symptom
            # Count user messages that are answers to this symptom's questions
            answer_count = 0
            for prev_msg in chat_history[:msg_idx + 1]:
                prev_ai = prev_msg.get("ai_response", "").lower()
                # Check if this AI message is about the current symptom
                if current_symptom.lower() in prev_ai or SYMPTOM_CHECKER_DB[current_symptom]["name"].lower() in prev_ai:
                    answer_count += 1
            current_stage = answer_count
    
    initial_state: AgentState = {
        "user_input": user_input,
        "analysis": "",
        "response_type": "common_issue",
        "response": "",
        "current_symptom": current_symptom,
        "current_stage": current_stage,
        "conversation_context": {},
        "chat_history": chat_history,
        "symptom_answers": symptom_answers,
        "severity": "low",
        "emergency": False,
    }
    
    result = health_agent.invoke(initial_state)
    
    return {
        "ai_response": result["response"],
        "response_type": result["response_type"],
        "severity": result.get("severity", "low"),
        "emergency": result.get("emergency", False),
        "current_symptom": result.get("current_symptom"),
    }
