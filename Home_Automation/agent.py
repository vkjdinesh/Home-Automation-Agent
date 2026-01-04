import json
import re
from typing import Dict, Any

import tools

# import run_llm from your llm module
from llm import run_llm  


# Load resources at startup


# 1. load sensor csv
tools.load_sensor_data(
    r"path_to_CSV"
)

# 2. load local llm config 
llm_info = tools.load_local_llm()
print("\nLocal LLM registered:", llm_info, "\n")


# Helper: very small dispatcher

def call_tool(tool_name: str, args: Dict[str, Any]) -> Any:
    """
    Calls tools.py functions safely
    """
    TOOL_REGISTRY = {
        "get_latest_sensor_data": tools.get_latest_sensor_data,
        "get_sensor_data_by_timestamp": tools.get_sensor_data_by_timestamp,
        "avg_sensor_data": tools.avg_sensor_data,
        "set_device_state": tools.set_device_state,
        "add_automation_rule": tools.add_automation_rule,
        "list_automation_rules": tools.list_automation_rules,
        "check_rules": tools.check_rules,  
        "get_latest_sensor_data_time_filtered": tools.get_latest_sensor_data_time_filtered,
    }

    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Unknown tool '{tool_name}'"}

    return TOOL_REGISTRY[tool_name](**args)

def run_local_llm(prompt: str) -> str:
    """
    Proxy function that calls your real LLM in llm.py
    """
    print("\n[LLM PROMPT]")
    print(prompt)
    response = run_llm(prompt)  
    print("\n[RAW LLM OUTPUT]\n")
    print(response)
    return response

# Extract JSON helper

def extract_json(text: str):
    try:
        json_candidates = []
        brace_count = 0
        start = None
        
        for i, ch in enumerate(text):
            if ch == '{':
                if brace_count == 0:
                    start = i
                brace_count += 1
            elif ch == '}':
                brace_count -= 1
                if brace_count == 0 and start is not None:
                    json_candidates.append(text[start:i+1])
                    start = None
        
        if not json_candidates:
            print("[extract_json] No complete JSON objects found")
            return None
        json_str = json_candidates[-1]
        print(f"[extract_json] Found {len(json_candidates)} JSONs, using last: {json_str[:100]}...")
        
        parsed = json.loads(json_str)
        if "tool" not in parsed:
            print("[extract_json] Last JSON missing 'tool' key, trying previous...")
            for candidate in reversed(json_candidates[:-1]):
                try:
                    parsed = json.loads(candidate)
                    if "tool" in parsed:
                        print(f"[extract_json] Found valid tool call: {candidate[:100]}...")
                        return parsed
                except:
                    continue
            return None
        
        return parsed
        
    except Exception as e:
        print(f"[extract_json error]: {e}")
        return None

SYSTEM_INSTRUCTIONS = """
You are a home automation agent.
You ONLY respond using JSON describing tool calls.

 ABSOLUTE MANDATORY RULES - READ FIRST:
1. SINGLE SENSOR ONLY - sensor_name = STRING ("temperature") NEVER ARRAY/LIST
2. NO EXTRA ARGS - add_automation_rule takes ONLY rule_text + structured_rule
3. NO time_period, states[], threshold_values[] in add_automation_rule args

CRITICAL RULES (check in order):
1. "if", "when", "whenever" + ONE condition + action → add_automation_rule
2. "check rules", "run rules" → check_rules  
3. "evening/morning/afternoon/night" + sensor → get_latest_sensor_data_time_filtered
4. "what is", "latest", "current" → get_latest_sensor_data
5. "average" → avg_sensor_data
6. "turn on/off", "set" → set_device_state
7. "list", "show" rules → list_automation_rules

 STRUCTURED_RULE FORMAT (MANDATORY - NO EXCEPTIONS):
FORMAT 1 ONLY: {"sensor_name": "temperature", "threshold_value": 25, "device": "fan", "state": "on", "room": "living_room"}
- sensor_name = STRING only
- threshold_value = NUMBER only  
- NO arrays, NO lists, NO time_period here

CORRECT EXAMPLES:
"temp > 18 → light": {"tool": "add_automation_rule", "args": {"rule_text": "user input", "structured_rule": {"sensor_name": "temperature", "threshold_value": 18, "device": "light", "state": "on", "room": "living_room"}}}

WRONG (LLM WILL FAIL VALIDATION):
{"sensor_name": ["temp1", "temp2"]}           → ARRAY ❌
{"threshold_values": [25, 25]}               → ARRAY ❌  
{"states": ["on"]}                           → ARRAY ❌
"time_period": "all"                         → EXTRA ARG ❌

SINGLE SENSOR SPLIT PATTERN:
"room1 AND room2 hot → fan" = 2 rules:
Rule 1: {"sensor_name": "temperature", "room": "living_room", ...}
Rule 2: {"sensor_name": "temperature", "room": "kitchen", ...}

TIME PERIODS: morning, afternoon, evening, night

TOOL SPECS:
• add_automation_rule(rule_text: string, structured_rule: object)
• check_rules(time_period: string) 
• get_latest_sensor_data_time_filtered(room: string, sensor_name: string, time_period: string)
• get_latest_sensor_data(room: string, sensor_name: string)
• set_device_state(room: string, device: string, state: string)
• list_automation_rules()

Respond ONLY in JSON with keys: "tool" and "args". NO other text.
"""
def natural_language_command_agent(user_message: str):
    prompt = f"""
{SYSTEM_INSTRUCTIONS}

User request:
{user_message}

Respond ONLY in JSON with keys: tool, args
"""
    llm_output = run_local_llm(prompt)

    tool_call = extract_json(llm_output)
    if not tool_call:
        return {"error": "LLM did not return valid JSON", "raw": llm_output}

    tool_name = tool_call.get("tool")
    args = tool_call.get("args", {})

    allowed_tools = [
        "get_latest_sensor_data",
        "get_sensor_data_by_timestamp",
        "avg_sensor_data",
        "set_device_state",
        "add_automation_rule",
        "list_automation_rules",
        "check_rules",
        "get_latest_sensor_data_time_filtered",
    ]

    if tool_name not in allowed_tools:
        return {"error": f"Invalid tool name '{tool_name}'", "raw": llm_output}

    print(f"\n[AGENT DECISION] calling tool: {tool_name} args={args}")
    
    if "sensor_type" in args:
        args["sensor_name"] = args.pop("sensor_type")
    if "sensor" in args:
        args["sensor_name"] = args.pop("sensor")
    if "location" in args:
        args["room"] = args.pop("location")

    print(f"[NORMALIZED] calling tool: {tool_name} args={args}")

    result = call_tool(tool_name, args)
    print("\n[TOOL RESULT]", result)
    return result

# Simple interactive loop

if __name__ == "__main__":
    print("Multi-Agent Home Automation System Ready! (Time-Aware)")
    print("Commands: 'list rules', 'check rules evening', 'latest evening kitchen temperature', 'if evening temp>28 → fan'")
    print("Type 'exit' to quit\n")

    while True:
        user_msg = input("User: ")

        if user_msg.lower() in ["exit", "quit"]:
            break

        result = natural_language_command_agent(user_msg)
        print("\nAgent response:", result)
