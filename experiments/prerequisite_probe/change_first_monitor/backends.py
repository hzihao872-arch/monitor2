"""Backend protocol and deterministic software-only scripted backend."""
import json


class ScriptedBackend:
    def __init__(self, answers):
        self.answers = answers
        self.requests = []
        self.identity = 'scripted-mock-no-model'

    def generate(self, request):
        self.requests.append({k: v for k, v in request.items() if k != 'images'} | {'images': len(request['images'])})
        answer = self.answers[request['stage']]
        if callable(answer):
            answer = answer(request)
        return json.dumps(answer, ensure_ascii=False) if isinstance(answer, dict) else answer
