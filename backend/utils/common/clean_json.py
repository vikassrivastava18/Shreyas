import json

filename = '../data/json/innovativemindset.json'

# Open the file in read mode ('r')
with open(filename, 'r', encoding='utf-8') as file:
    data = json.load(file)

for chapter in data["chapters"]:
    for i, subchapter in enumerate(chapter["subchapters"]):
        sub_name, content = subchapter["name"], subchapter["content"]

        # For all the subchapters except the last
        if i < len(chapter["subchapters"]) - 1:
            next_sub_name = chapter["subchapters"][i+1]["name"]
            start_ind, end_ind = content.find(sub_name), content.find(next_sub_name)
        else:
            start_ind, end_ind = content.find(sub_name), len(content)
        sub_cont = content[start_ind:end_ind]
        subchapter["content"] = sub_cont


# License Blueprint Reading Copyright © 2025 .... Share This Book
filename = '../data/json/innovativemindset.json'
# Open the file in write mode ('w')
with open(filename, 'w') as file:
    json.dump(data, file, indent=4) # 'indent=4' makes the file human-readable
