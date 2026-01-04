from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from pathlib import Path

# Define model path with Path and resolve (Update this path accordingy to your folder structure)
MODEL_PATH = Path(r"E:\Home_Automation\qwen2.5_local").resolve() 

print(f"Loading model from: {MODEL_PATH.as_posix()}")

tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH.as_posix()))
model = AutoModelForCausalLM.from_pretrained(
    str(MODEL_PATH.as_posix()),
    device_map="auto",
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
)

print("Model loaded successfully.")

def run_llm(prompt: str) -> str:
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=256)
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print("\n[RAW LLM OUTPUT]\n", decoded)  # <-- Add this debug print
    return decoded


