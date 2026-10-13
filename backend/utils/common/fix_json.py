# Connect to the database
from core.config import Session
from db.models import Subtopic
import json

filename = '../data/json/blueprint.json'
# Open the file in read mode ('r')
with open(filename, 'r', encoding='utf-8') as file:
    data = json.load(file)

def update_subchapters():
    db = Session()

    for chapter in data["chapters"]:
        for subchapter in chapter["subchapters"]:
            name, source = subchapter["name"], subchapter["url"]
            db.query(Subtopic).filter(Subtopic.subtopic_name == name).update({"source": source})
            db.commit()

    return None
    # subchaters = db.query(Subtopic).filter(Subtopic.chapter_id == 1).all()
    # for subchater in subchaters:
    #     print(subchater.subtopic_name)

update_subchapters()

