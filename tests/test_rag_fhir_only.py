# tests/test_rag_fhir_only.py

import sys, os, subprocess
import pytest

# ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.getcwd()))

from src.core.prompt_router import route_prompt, FUNCTION_FHIR
from src.core.rag_controller import rag_inference

@pytest.fixture(autouse=True)
def stub_subprocess_run(monkeypatch):
    """
    Stub out subprocess.run so that route_prompt returns
    deterministic JSON based solely on the actual USER question line.
    """
    def fake_run(cmd, stdout, stderr, text, timeout):
        full_prompt = cmd[-1]
        # isolate just the USER’s question text
        try:
            user_line = full_prompt.split("\nUSER:")[1].split("\n")[0].strip()
        except IndexError:
            user_line = ""

        if user_line == "What allergies do I have?":
            out = '{"function":"get_fhir_resources","arguments":{"patient":"emily","categories":["allergies"]}}'
        elif user_line == "Show me my active conditions.":
            out = '{"function":"get_fhir_resources","arguments":{"patient":"emily","categories":["conditions"]}}'
        elif user_line == "List my labs and current meds.":
            out = '{"function":"get_fhir_resources","arguments":{"patient":"emily","categories":["observations","currentMedications"]}}'
        elif user_line == "Show me my current medications.":
            out = '{"function":"get_fhir_resources","arguments":{"patient":"emily","categories":["currentMedications"]}}'
        elif user_line == "List my labs.":
            out = '{"function":"get_fhir_resources","arguments":{"patient":"emily","categories":["observations"]}}'
        elif user_line == "Give me my birth date and gender.":
            out = '{"function":"get_fhir_resources","arguments":{"patient":"emily","categories":["generalInfo"]}}'
        elif user_line == "What therapy sessions are scheduled?":
            out = '{"function":"get_fhir_resources","arguments":{"patient":"emily","categories":["carePlan"]}}'
        else:
            out = ''
        return subprocess.CompletedProcess(cmd, 0, out, "")

    monkeypatch.setattr(subprocess, 'run', fake_run)

@pytest.mark.parametrize("prompt, expected_cats", [
    ("What allergies do I have?",          ["allergies"]),
    ("Show me my active conditions.",      ["conditions"]),
    ("List my labs and current meds.",     ["observations", "currentMedications"]),
    ("Give me my birth date and gender.",  ["generalInfo"]),
    ("What therapy sessions are scheduled?",["carePlan"]),
])
def test_route_prompt_fhir(prompt, expected_cats):
    route = route_prompt(prompt)
    assert route["function"] == FUNCTION_FHIR
    cats = route["arguments"]["categories"]
    assert set(cats) == set(expected_cats)

@pytest.mark.parametrize("prompt, must_contain", [
    ("What allergies do I have?",           "Allergy:"),
    ("Show me my current medications.",     "(status:"),
    ("List my labs.",                       "g/dL"),
    ("Give me my birth date and gender.",   "Patient:"),
    ("What therapy sessions are scheduled?", "CarePlan:"),
])
def test_rag_inference_fhir(prompt, must_contain):
    result = rag_inference(prompt)
    assert result["source"] == "fhir"
    assert must_contain in result["response"]
