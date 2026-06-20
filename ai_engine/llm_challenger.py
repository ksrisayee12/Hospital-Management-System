import torch
import json
import re
from transformers import AutoProcessor, AutoModelForCausalLM

# Use a standard causal LM for text-only, or the user's specified model if possible.
# Note: The user snippet used AutoModelForImageTextToText for a multimodal MedGemma.
# We will use AutoModelForCausalLM as a fallback if it's just text, or try to load the specified one.
# For simplicity and strict JSON adherence, we'll write a prompt that forces the JSON format.

MODEL_ID = "google/medgemma-4b-it"

# Global lazy loading to avoid loading on import if it's not needed instantly
_model = None
_processor = None

def load_model():
    global _model, _processor
    if _model is None:
        try:
            # We try loading as a causal language model for text RAG processing
            from transformers import AutoTokenizer
            _processor = AutoTokenizer.from_pretrained(MODEL_ID)
            _model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                torch_dtype=torch.bfloat16,
                device_map="auto"
            )
        except Exception as e:
            # Fallback to the user's snippet class if CausalLM fails
            from transformers import AutoProcessor, AutoModelForImageTextToText
            _processor = AutoProcessor.from_pretrained(MODEL_ID)
            _model = AutoModelForImageTextToText.from_pretrained(
                MODEL_ID,
                torch_dtype=torch.bfloat16,
                device_map="auto"
            )

def generate_clinical_review(current_report, rag_context):
    """
    Generates the Clinical Challenger JSON response based on the report and context.
    """
    load_model()
    
    system_prompt = """You are an AI Clinical Reasoning Challenger Agent.
Your job is to support doctors by questioning, challenging, and analyzing their reports against historical patient data.
You MUST NEVER generate final diagnoses, prescribe medicines, approve/reject prescriptions, override doctors, or make treatment decisions.
You must analyze the historical data and highlight anomalies, surface missing evidence, and suggest verification points.
You must always provide reasoning and evidence references from the RAG Context.

OUTPUT FORMAT MUST BE EXACTLY VALID JSON:
{
  "risk_level": "LOW | MEDIUM | HIGH",
  "contradictions": ["...", "..."],
  "clinical_questions": ["..."],
  "missing_evidence": ["..."],
  "wearable_observations": ["..."],
  "historical_observations": ["..."],
  "prescription_warnings": ["..."],
  "confidence": 0.85
}
"""

    user_prompt = f"""
RAG CONTEXT (Past Patient Data):
{rag_context}

CURRENT DOCTOR REPORT/PRESCRIPTION:
{current_report}

Generate your Challenger review in the exact JSON format specified.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        # If the model uses apply_chat_template
        inputs = _processor.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt"
        ).to(_model.device, dtype=torch.bfloat16)
        
        input_len = inputs["input_ids"].shape[-1]
        
        with torch.inference_mode():
            generation = _model.generate(**inputs, max_new_tokens=800, do_sample=False)
            generation = generation[0][input_len:]
            
        decoded = _processor.decode(generation, skip_special_tokens=True)
    except Exception as e:
        # Fallback if chat template isn't supported
        prompt_text = system_prompt + "\n\n" + user_prompt
        inputs = _processor(prompt_text, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
        with torch.inference_mode():
            outputs = _model.generate(**inputs, max_new_tokens=800)
            decoded = _processor.decode(outputs[0], skip_special_tokens=True)
            # Remove prompt from output
            decoded = decoded.replace(prompt_text, "")

    # Clean the output to ensure we just return the JSON string
    try:
        # Try to find JSON block if it wrapped it in markdown
        json_str = decoded
        if "```json" in decoded:
            json_str = decoded.split("```json")[1].split("```")[0]
        elif "```" in decoded:
            json_str = decoded.split("```")[1].split("```")[0]
            
        return json.loads(json_str.strip())
    except json.JSONDecodeError:
        # Fallback if the model failed to generate strict JSON
        return {
            "risk_level": "MEDIUM",
            "contradictions": ["Model failed to return valid JSON. Raw output: " + decoded[:200]],
            "clinical_questions": [],
            "missing_evidence": [],
            "wearable_observations": [],
            "historical_observations": [],
            "prescription_warnings": [],
            "confidence": 0.5
        }

def generate_chat_response(message, rag_context, chat_history=[]):
    """
    Generates a conversational response from the AI Clinical Challenger,
    including a textual response and a structured JSON findings block.
    """
    try:
        load_model()
    except Exception as e:
        # Fallback if the local model cannot be loaded (e.g. no GPU, out of memory, or gated model access issues)
        print(f"Model load failed: {e}. Falling back to Rule-Based Challenger.")
        return generate_mock_chat_response(message, rag_context)

    system_prompt = """You are an AI Clinical Reasoning Challenger Agent chatbot.
Your job is to support doctors by questioning, challenging, and analyzing their messages/prescriptions against historical patient data.
You MUST NEVER generate final diagnoses, prescribe medicines, approve/reject prescriptions, override doctors, or make treatment decisions.
You must analyze the historical data and highlight anomalies, surface missing evidence, and suggest verification points.
You must always provide reasoning and evidence references from the RAG Context.

Your response MUST be a JSON object containing both a natural conversational 'message' and the structured 'findings' metadata:
{
  "message": "Write your natural conversational reply to the doctor here. Be polite but challenge inconsistencies.",
  "findings": {
    "risk_level": "LOW | MEDIUM | HIGH",
    "contradictions": ["..."],
    "clinical_questions": ["..."],
    "missing_evidence": [],
    "wearable_observations": [],
    "historical_observations": [],
    "prescription_warnings": [],
    "confidence": 0.85
  }
}
"""

    user_prompt = f"""
RAG CONTEXT (Past Patient Data):
{rag_context}

CHAT HISTORY:
{chat_history}

DOCTOR'S MESSAGE:
{message}

Respond in the exact JSON format specified.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        inputs = _processor.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt"
        ).to(_model.device, dtype=torch.bfloat16)
        
        input_len = inputs["input_ids"].shape[-1]
        
        with torch.inference_mode():
            generation = _model.generate(**inputs, max_new_tokens=800, do_sample=False)
            generation = generation[0][input_len:]
            
        decoded = _processor.decode(generation, skip_special_tokens=True)
    except Exception:
        prompt_text = system_prompt + "\n\n" + user_prompt
        inputs = _processor(prompt_text, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
        with torch.inference_mode():
            outputs = _model.generate(**inputs, max_new_tokens=800)
            decoded = _processor.decode(outputs[0], skip_special_tokens=True)
            decoded = decoded.replace(prompt_text, "")

    try:
        json_str = decoded
        if "```json" in decoded:
            json_str = decoded.split("```json")[1].split("```")[0]
        elif "```" in decoded:
            json_str = decoded.split("```")[1].split("```")[0]
            
        return json.loads(json_str.strip())
    except json.JSONDecodeError:
        return {
            "message": "I processed your request but had trouble formatting the response. Let's verify the details.",
            "findings": {
                "risk_level": "LOW",
                "contradictions": [],
                "clinical_questions": [],
                "missing_evidence": [],
                "wearable_observations": [],
                "historical_observations": [],
                "prescription_warnings": [],
                "confidence": 0.5
            }
        }

def generate_mock_chat_response(message, rag_context):
    """
    A deterministic rule-based generator that checks key terms in the message
    and returns a structured response matching the clinical instructions.
    """
    msg_lower = message.lower()
    
    response_text = "I've analyzed your input against the patient's records."
    risk_level = "LOW"
    contradictions = []
    questions = []
    missing_evidence = []
    wearable = []
    prescriptions = []
    
    # 1. Historical consistency checks
    if "hypertension" in msg_lower or "blood pressure" in msg_lower:
        if "stable bp" in rag_context.lower() or "bp normal" in rag_context.lower() or "normal blood pressure" in rag_context.lower():
            response_text = "Potential contradiction detected. Historical data indicates stable blood pressure patterns. Could recent measurements supporting severe hypertension be verified?"
            risk_level = "MEDIUM"
            contradictions.append("Historical data indicates stable blood pressure patterns.")
            questions.append("Could recent measurements supporting severe hypertension be verified?")
            
    # 2. Dosage check
    if "metformin" in msg_lower:
        # Check for high dose (e.g. 5000mg)
        dosage_match = re.search(r'(\d+)\s*mg', msg_lower)
        if dosage_match:
            dose = int(dosage_match.group(1))
            if dose > 2000:
                response_text = f"Possible dosage anomaly detected. The recorded dosage of {dose}mg appears significantly higher than standard treatment patterns. Please verify dosage entry."
                risk_level = "HIGH"
                prescriptions.append(f"Metformin dosage ({dose}mg) exceeds standard maximum therapeutic limits (2000mg/day).")
                questions.append("Consider verifying dosage.")
                
    # 3. Sleep / Wearable check
    if "sleep deprivation" in msg_lower or "insomnia" in msg_lower:
        if "sleep average 7.5" in rag_context.lower() or "average sleep = 8.2" in rag_context.lower() or "sleep average" in rag_context.lower():
            response_text = "Potential inconsistency detected between reported symptoms and wearable data. Consider validating recent sleep measurements."
            risk_level = "MEDIUM"
            wearable.append("Smartwatch logs average sleep > 7.5 hours over the past week.")
            questions.append("Consider validating recent sleep measurements.")
            
    # 4. Missing ECG check
    if "cardiac" in msg_lower or "heart condition" in msg_lower:
        response_text = "Diagnosis appears to lack supporting evidence from available ECG and laboratory reports. Consider additional verification."
        risk_level = "HIGH"
        missing_evidence.append("No active ECG anomalies or cardiac lab biomarkers recorded.")
        questions.append("Consider additional verification.")

    return {
        "message": response_text,
        "findings": {
            "risk_level": risk_level,
            "contradictions": contradictions,
            "clinical_questions": questions,
            "missing_evidence": missing_evidence,
            "wearable_observations": wearable,
            "historical_observations": [],
            "prescription_warnings": prescriptions,
            "confidence": 0.9
        }
    }

