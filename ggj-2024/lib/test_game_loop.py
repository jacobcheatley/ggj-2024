import requests
import random
import json
from openai import OpenAI

client = OpenAI()


with open("./system_prompt.txt", encoding="utf8") as f:
    sys_prompt = f.read()



def get_rankings(lst):
    sorted_positions = sorted(range(len(lst)), key=lambda k: lst[k], reverse = True)
    return [sorted_positions.index(i)+1 for i in range(len(lst))]

# •	Select Theme – King requests jokes about theme
themes = ["dogs", "cats", "mice", "snails"]
theme = random.choice(themes)
# •	Players respond on phones
players = ["Fraser"]#, "Jacob", "Richard", "Sally"]
jokes = []
for player in players:
    jokes.append(input(f"Ok, I want you to tell me a joke about {theme} :  "))

# •	List of responses captured from players

# •	Prompt for Joke grading:
#    o	Inputs -> Theme + Joke
#    o	Outputs ->  Relevance Score + Funny Score

scores = []
for joke in jokes:
    score_prompt = f"""Get Score:
    Theme: {theme}
    Joke: {joke}
    """
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": score_prompt}
    ]
    )
    score_response = completion.choices[0].message
    print(score_response)
    score = json.loads(score_response.content.split("Score:")[1])
    print(score)
    scores.append(score)

points = []
for score in scores:
    points.append(score["relevance"]*score["funniness"])
rankings = get_rankings(points)

# •	Prompt for Kings Judgement:
#    o	Inputs -> Joke, relevance score, funny score, position, name
#    o	Outputs -> Dialogue of King

for i, joke in enumerate(jokes):
    response_prompt = f"""Get Response:
    Theme: {theme}
    Joke: {joke}
    Score: {json.dumps(scores[i])}
    Position: {rankings[i]}
    Name: {players[i]}
    """
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": response_prompt}
    ]
    )
    
    kings_response = completion.choices[0].message
    print(kings_response)
    kings_response_dialouge = json.loads(kings_response.content.split("Response:")[1])
    print(kings_response_dialouge)
# •	King recites judgement.
# •	Worst player is killed.
# •	If more than one player lives:
#    o	Loop To step 1.
# •	Else:
#    o	Declare Winner