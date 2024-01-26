import requests
import random
import json

def get_rankings(lst):
    sorted_positions = sorted(range(len(lst)), key=lambda k: lst[k], reverse = True)
    return [sorted_positions.index(i)+1 for i in range(len(lst))]

# •	Select Theme – King requests jokes about theme
themes = ["dogs", "cats", "mice", "snails"]
theme = random.choice(themes)
# •	Players respond on phones
players = ["Fraser", "Jacob", "Richard", "Sally"]
jokes = []
for player in players:
    jokes.append(input(f"Ok, I want you to tell me a joke about {theme}/n"))

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
    score_response = requests(OPENAI_REQUEST, score_prompt)
    score = json.loads(score_response.split("Score:")[1])
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
    kings_response = requests(OPENAI_REQUEST, response_prompt)
    kings_response_string = json.loads(kings_response.split("Response:")[1])
    print(kings_response_string)
# •	King recites judgement.
# •	Worst player is killed.
# •	If more than one player lives:
#    o	Loop To step 1.
# •	Else:
#    o	Declare Winner