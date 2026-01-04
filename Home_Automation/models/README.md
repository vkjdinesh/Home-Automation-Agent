from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

LLM_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(LLM_NAME)
model = AutoModelForCausalLM.from_pretrained(
    LLM_NAME,
    device_map="cpu",
    torch_dtype=torch.float16
)

# Save tokenizer and model locally
save_dir = "./qwen2.5_local"
tokenizer.save_pretrained(save_dir)
model.save_pretrained(save_dir)
print(f"Model and tokenizer saved to {save_dir}")
