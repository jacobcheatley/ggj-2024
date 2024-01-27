import json
import random
from pathlib import Path

from openai import OpenAI


class King:
    def __init__(self, ai_config_path: Path) -> None:
        with open(ai_config_path / "system_prompt.txt", encoding="utf-8") as f:
            self.system_prompt = f.read()
        with open(ai_config_path / "themes.txt") as f:
            self.themes = f.readlines()

        self.client = OpenAI()
        self.theme = random.choice(self.themes).strip()

    def grade_joke(self, name, joke_text):
        # Score
        score_prompt = f"""Get Score:
            Theme: {self.theme}
            Joke: {joke_text}
            """
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": score_prompt}],
        )
        score_response = completion.choices[0].message
        score_dict = json.loads(score_response.content.split("Score:")[1])
        relevance = score_dict["relevance"]
        funniness = score_dict["funniness"]
        points = relevance * funniness

        # Response
        response_prompt = f"""Get Response:
            Theme: {self.theme}
            Joke: {joke_text}
            Score: {json.dumps(score_dict)}
            Points: {points}
            Name: {name}
            """
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": response_prompt}],
        )

        kings_response = completion.choices[0].message
        response_text = json.loads(kings_response.content.split("Response:")[1])

        return {"relevance": relevance, "funniness": funniness, "points": points, "response_text": response_text}
