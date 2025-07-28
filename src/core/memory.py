# src/core/memory.py

class PromptMemory:
    def __init__(self):
        self.recent_drugs = set()
        self.last_prompt = None
        self.last_response = None

    def already_mentioned(self, drug_name: str) -> bool:
        return drug_name.lower() in self.recent_drugs

    def remember_drug(self, drug_name: str):
        self.recent_drugs.add(drug_name.lower())

    def update(self, prompt: str, response: str):
        self.last_prompt = prompt
        self.last_response = response

    def reset(self):
        self.recent_drugs.clear()
        self.last_prompt = None
        self.last_response = None
