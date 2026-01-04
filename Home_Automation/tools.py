import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any

# Global States

SENSOR_DATA: Optional[pd.DataFrame] = None
AUTOMATION_RULES: List[Dict[str, Any]] = []
DEVICE_STATES: Dict[str, Dict[str, str]] = {}

# 1. LOAD SENSOR DATA

def load_sensor_data(csv_path: str):
    """
    Load sensor data CSV into global dataframe
    """
    global SENSOR_DATA

    SENSOR_DATA = pd.read_csv(csv_path, parse_dates=["timestamp"])
    SENSOR_DATA.sort_values(by="timestamp", inplace=True)

    return {
        "status": "success",
        "rows_loaded": len(SENSOR_DATA)
    }

# 2. LOAD LOCAL LLM (Qwen 2.5 local)

import os

def load_local_llm():
    """
    Registers your local Qwen 2.5 LLM.
    This does NOT run inference; it only stores configuration info.
    The agent will later use this path to actually run the model.
    """

    model_path = r"E:\Home_Automation\qwen2.5_local" #update this

    if not os.path.exists(model_path):
        return {
            "status": "error",
            "message": f"Model path not found: {model_path}"
        }

    llm_info = {
        "type": "local",
        "engine": "qwen",
        "model_name": "qwen2.5_local",
        "path": model_path
    }

    return {
        "status": "success",
        "llm": llm_info
    }


# 3. GET LATEST SENSOR DATA

def get_latest_sensor_data(room: str, sensor_name: str):
    global SENSOR_DATA
    if SENSOR_DATA is None:
        return {"error": "Sensor data not loaded"}

    df = SENSOR_DATA[
        (SENSOR_DATA["room"] == room) &
        (SENSOR_DATA["sensor_name"] == sensor_name)
    ]

    if df.empty:
        return {"error": "No data found"}

    latest = df.iloc[-1]

    return {
        "timestamp": latest["timestamp"],
        "room": room,
        "sensor_name": sensor_name,
        "value": float(latest["value"])
    }

# 4. GET SENSOR DATA BY TIMESTAMP

def get_sensor_data_by_timestamp(room: str, sensor_name: str, timestamp: str):
    global SENSOR_DATA
    if SENSOR_DATA is None:
        return {"error": "Sensor data not loaded"}

    ts = pd.to_datetime(timestamp)

    df = SENSOR_DATA[
        (SENSOR_DATA["room"] == room) &
        (SENSOR_DATA["sensor_name"] == sensor_name) &
        (SENSOR_DATA["timestamp"] == ts)
    ]

    if df.empty:
        return {"error": "No matching record"}

    rec = df.iloc[0]

    return {
        "timestamp": str(rec["timestamp"]),
        "room": room,
        "sensor_name": sensor_name,
        "value": float(rec["value"])
    }


# 5. AVERAGE SENSOR DATA

def avg_sensor_data(room: str, sensor_name: str, start_time: str, end_time: str):
    global SENSOR_DATA
    if SENSOR_DATA is None:
        return {"error": "Sensor data not loaded"}

    start = pd.to_datetime(start_time)
    end = pd.to_datetime(end_time)

    df = SENSOR_DATA[
        (SENSOR_DATA["room"] == room) &
        (SENSOR_DATA["sensor_name"] == sensor_name) &
        (SENSOR_DATA["timestamp"] >= start) &
        (SENSOR_DATA["timestamp"] <= end)
    ]

    if df.empty:
        return {"error": "No data in interval"}

    avg_val = df["value"].mean()

    return {
        "room": room,
        "sensor_name": sensor_name,
        "start": str(start_time),
        "end": str(end_time),
        "average_value": float(avg_val)
    }

# 6. SET DEVICE STATE (SIMULATED ACTUATOR)

def set_device_state(room: str, device: str, state: str):
    global DEVICE_STATES

    if room not in DEVICE_STATES:
        DEVICE_STATES[room] = {}

    DEVICE_STATES[room][device] = state

    action = {
        "timestamp": str(datetime.now()),
        "room": room,
        "device": device,
        "state": state
    }

    print(f" DEVICE ACTION: {room}.{device} -> {state}")

    return {
        "status": "success",
        "action": action
    }

# 7. ADD AUTOMATION RULE

def add_automation_rule(rule_text: str, structured_rule: Dict[str, Any], **kwargs):
    """Flexible validation for action/state fields"""
    global AUTOMATION_RULES
    
    if not structured_rule or structured_rule is None:
        return {"status": "error", "message": "Structured rule cannot be null"}
    
    if isinstance(structured_rule.get('sensor_name'), list):
        return {"status": "error", "message": "SINGLE SENSOR ONLY - no arrays allowed"}
    

    structured_rule_copy = structured_rule.copy()
    if 'action' in structured_rule_copy and 'state' not in structured_rule_copy:
        structured_rule_copy['state'] = structured_rule_copy.pop('action', 'on')
    

    required_fields = ['sensor_name', 'threshold_value', 'device', 'state']
    if not all(key in structured_rule_copy for key in required_fields):
        return {"status": "error", "message": f"Missing required fields: {required_fields}"}
    
    rule = {
        "rule_text": rule_text,
        "structured": structured_rule_copy,  
        "created_at": str(datetime.now())
    }
    
    AUTOMATION_RULES.append(rule)
    return {"status": "success", "rule_stored": rule}



# 8. LIST AUTOMATION RULES

def list_automation_rules():
    return {
        "rule_count": len(AUTOMATION_RULES),
        "rules": AUTOMATION_RULES
    }
def check_rules(time_period: str = None):
    """Multi-agent rule engine: check stored rules vs current sensors"""
    global SENSOR_DATA, AUTOMATION_RULES, DEVICE_STATES 
    
    triggered = []
    
    for rule in AUTOMATION_RULES:
        structured = rule['structured']
        if not structured:  
            continue
            
       
        if all(key in structured for key in ['sensor_name', 'threshold_value', 'device', 'state']):
            room = structured.get('room', 'living_room')  
            sensor_name = structured['sensor_name']
            threshold = structured['threshold_value']
            device = structured['device']
            state = structured['state']
            
            
            if time_period:
                sensor_data = get_latest_sensor_data_time_filtered(room, sensor_name, time_period)
            else:
                sensor_data = get_latest_sensor_data(room, sensor_name)
            
            if sensor_data.get('error') or sensor_data['value'] <= threshold:
                continue
            
            # Execute action
            result = set_device_state(room, device, state)
            if result['status'] == 'success':
                triggered.append(f"{room}.{device} → {state} (rule: {rule['rule_text'][:50]}...)")
        
       
        elif 'condition' in structured and 'actions' in structured:
            cond = structured['condition']
            sensor_info = cond.get('sensor', {})
            room = sensor_info.get('room', 'living_room')
            sensor_name = sensor_info.get('sensor_name', 'temperature')
            operator = cond.get('comparison_operator', cond.get('operator', '>'))
            threshold = cond.get('value')
            
            # Get sensor data
            if time_period:
                sensor_data = get_latest_sensor_data_time_filtered(room, sensor_name, time_period)
            else:
                sensor_data = get_latest_sensor_data(room, sensor_name)
            
            if sensor_data.get('error'):
                continue
            
            current_value = sensor_data['value']
            
            # Evaluate condition
            condition_met = False
            if operator == '>' and current_value > threshold:
                condition_met = True
            elif operator == '>=' and current_value >= threshold:
                condition_met = True
            elif operator == '<' and current_value < threshold:
                condition_met = True
            elif operator == '<=' and current_value <= threshold:
                condition_met = True
            
            if not condition_met:
                continue
            
            # Execute first action
            actions = structured['actions']
            if actions:
                action = actions[0]
                device = action.get('device')
                state = action.get('state')
                if device and state:
                    result = set_device_state(room, device, state)
                    if result['status'] == 'success':
                        triggered.append(f"{room}.{device} → {state} (rule: {rule['rule_text'][:50]}...)")
        
        # === LEGACY FORMAT SUPPORT ===
        elif all(key in structured for key in ['sensor_name', 'threshold_value']):
            
            room = 'living_room'
            sensor_data = get_latest_sensor_data(room, structured['sensor_name'])
            if sensor_data.get('value', 0) > structured['threshold_value']:
                set_device_state(room, 'fan', 'on')  # Default action
                triggered.append(f"Legacy rule triggered: {rule['rule_text'][:50]}...")
    
    return {
        "status": "checked", 
        "rules_triggered": triggered if triggered else "None triggered",
        "total_rules": len(AUTOMATION_RULES),
        "time_period": time_period or "all_day"
    }


def get_latest_sensor_data_time_filtered(room: str, sensor_name: str, time_period: str):
    """Get latest sensor data in specific time period (morning, afternoon, evening, night)"""
    global SENSOR_DATA
    if SENSOR_DATA is None:
        return {"error": "No data"}
    
    # time periods 
    now = pd.Timestamp.now().normalize()  
    periods = {
        "evening": (now + pd.Timedelta(hours=18), now + pd.Timedelta(hours=23, minutes=59)),
        "morning": (now + pd.Timedelta(hours=6), now + pd.Timedelta(hours=12)),
        "afternoon": (now + pd.Timedelta(hours=12), now + pd.Timedelta(hours=18)),
        "night": (now, now + pd.Timedelta(hours=6))
    }
    
    if time_period not in periods:
        return {"error": "Invalid time period"}
    
    start_time, end_time = periods[time_period]
    df = SENSOR_DATA[
        (SENSOR_DATA["room"] == room) &
        (SENSOR_DATA["sensor_name"] == sensor_name) &
        (SENSOR_DATA["timestamp"] >= start_time) &
        (SENSOR_DATA["timestamp"] <= end_time)
    ]
    
    if df.empty:
        return {"error": f"No {time_period} data"}
    
    latest = df.iloc[-1]
    return {
        "timestamp": latest["timestamp"],
        "room": room, 
        "sensor_name": sensor_name,
        "value": float(latest["value"]),
        "time_period": time_period
    }

def check_rules(time_period: str = None):
    """Check stored rules against current sensor data (time-aware)"""
    global AUTOMATION_RULES, DEVICE_STATES
    triggered = []
    
    for rule in AUTOMATION_RULES:
        structured = rule['structured']
        

        if 'condition' in structured and 'sensor' in structured['condition']:
            cond = structured['condition']
            sensor_info = cond['sensor']
            

            if time_period:
                sensor_data = get_latest_sensor_data_time_filtered(
                    sensor_info['room'], sensor_info['sensor_name'], time_period
                )
            else:
                sensor_data = get_latest_sensor_data(sensor_info['room'], sensor_info['sensor_name'])
            
            if 'error' in sensor_data:
                continue
            
            current_value = sensor_data['value']
            threshold = cond.get('value', 0)
            operator = cond.get('comparison_operator', '>').replace('>=', 'ge')
            

            if operator in ['>', 'gt'] and current_value > threshold:
                execute_rule_action(structured, triggered)
            elif operator in ['>=', 'ge'] and current_value >= threshold:
                execute_rule_action(structured, triggered)
        

        elif all(k in structured for k in ['sensor_name', 'threshold_value']):
            sensor_data = get_latest_sensor_data("living_room", structured['sensor_name'])
            if sensor_data.get('value', 0) > structured['threshold_value']:
                execute_rule_action(structured, triggered)
    
    return {"status": "checked", "rules_triggered": triggered}

def execute_rule_action(structured, triggered):
    """Helper to execute rule actions"""
    actions = structured.get('actions', [{}])[0]
    room = structured['condition']['sensor']['room'] if 'condition' in structured else "living_room"
    device = actions.get('device', 'fan')
    state = actions.get('state', 'on')
    
    result = set_device_state(room, device, state)
    if result['status'] == 'success':
        triggered.append(f"{room}.{device} → {state}")
