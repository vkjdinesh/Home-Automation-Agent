# Home Automation LLM Agent

### Learning Objectives
Students will:
- Understand agent-based system design  
- Use an LLM as a controller  
- Implement tool calling with JSON  
- Design a rule engine  
- Simulate cyber-physical systems  
- Practice prompt engineering  

### Overview
In this assignment, you will build a simple home automation agent that can be programmed using natural language commands instead of traditional buttons or predefined rule editors.

Users will be able to type instructions like:

> “If the bedroom temperature is below 18 degrees, turn on the heater.”

Your system will:
- Understand the instruction using a Large Language Model (LLM)  
- Convert it into a structured rule  
- Store the rule  
- Continuously monitor sensor values  
- Automatically execute device actions when rules are satisfied  

This assignment demonstrates how **LLM-based agents** can support natural-language programming for smart environments.

### Background

**How current home automation works**  
- Modern smart home systems are typically rule-based, configured via apps, and built on IF–THEN logic.  

Examples:  
- IF temperature > 28°C → turn on AC  
- IF motion detected at night → turn on lights  

**Limitations of traditional systems:**  
- Require manual configuration  
- Cannot understand natural language  
- Lack conversational interaction  

**What LLMs bring:**  
- Users can type natural sentences  
- Describe vague concepts (e.g., “too cold”)  
- Define rules conversationally  
- AI converts language → structured logic  

Example:  
> “When it’s too hot in the living room, turn on the fan.”  

LLM interprets and generates a structured rule.

### What You Will Build

Your project consists of four main parts:

1. **Natural Language Agent**  
   - Reads user messages  
   - Uses an LLM  
   - Outputs JSON tool calls (not free-text answers)  

2. **Tools Layer**  
   - Functions for:  
     - Retrieving sensor readings  
     - Changing device states  
     - Adding rules  
     - Listing rules  
     - Evaluating rules  

3. **Rule Engine**  
   - Stores automation rules  
   - Checks sensors periodically  
   - Triggers actions when rule conditions hold  

4. **Simulated IoT Environment**  
   - Simulates temperature sensors and actuators (lights, fan, heater)  
   - No physical hardware required  

### Recommended Project Structure

```
Home_Automation/
├── agent.py # Natural language automation agent
├── tools.py # Rule engine, devices, sensors utilities
├── llm.py # Local LLM wrapper/loader
├── requirements.txt # Python dependencies (Including cloud based)
├── sensor_data.csv # This is synthetic data; please use/generate it according to your application context.
├── README.md # Assignment instructions
├── Qwen2.5_local/ # Placeholder folder for model files
  └── README.md # Instructions to download the model

```


### Downloading the Local LLM Model

- Due to size and licensing restrictions, model files are **not** included in this repository.  
- Please download the Qwen 2.5 local model manually and place it in:  
  `Home_Automation/Qwen2.5_local`

### Running the System

1. Create a virtual environment.  
2. Install dependencies:  
   ```bash
   pip install -r requirements.txt

3. Configure the local LLM path if necessary.
4. Run the agent: python agent.py

The program will start an interactive loop.

Example Commands
1. Try typing commands like:
2. turn on the bedroom light
3. What is the latest temperature in the kitchen
4. if temperature is less than 15 in bedroom turn on heater
**Sample Input and Output**
```
Input:
When it’s too cold in the living room, turn off the fan
Output:
{
  "tool": "add_automation_rule",
  "args": {
    "rule_text": "too cold in living room → fan off",
    "structured_rule": {
      "sensor_name": "temperature",
      "threshold_value": 20,
      "device": "fan",
      "state": "off",
      "room": "living_room"
    }
  },
  "result": {
    "status": "success",
    "rule_stored": {
      "rule_text": "too cold in living room → fan off",
      "structured": {
        "sensor_name": "temperature",
        "threshold_value": 20,
        "device": "fan",
        "state": "off",
        "room": "living_room"
      },
      "created_at": "2026-xx-xx 08:32:18.384904"
    }
  }
}
```

The rule engine will then turn the fan off when the condition is satisfied.

### Submission Requirements

Students must submit:
1. A working Python project
2. A recorded demo or screenshots
3. A short report including:
  - Architecture overview
  - Prompt design
  - Limitations
  - Possible extensions