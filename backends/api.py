import json

from pydantic import BaseModel
from fastapi import FastAPI
from prompt_generate import generate_prompt_from_json

app = FastAPI()

class Query(BaseModel):
    query: str
    background: str
    structure: str
    replace: str


@app.post("/prompt/generate")
def generate_prompt(query:Query):
    with open('C:\\Users\\29884\\Desktop\\北航课题\\demo\\knowledge.json','r',encoding='utf-8') as file:
        sample_json = json.load(file)
    prompt = generate_prompt_from_json(sample_json, query.query, query.background, query.structure, query.replace)
    return {"prompt": prompt}

@app.post("/knowledge/generate")
def generate_knowledge(query:Query):
    with open('C:\\Users\\29884\\Desktop\\北航课题\\demo\\knowledge.json','w',encoding='utf-8') as file:
        file.write(query.query)
    return {"result":"OK"}

@app.get("/knowledge/get")
def get_knowledge():
    with open('C:\\Users\\29884\\Desktop\\北航课题\\demo\\knowledge.json','r',encoding='utf-8') as file:
        sample_json = json.load(file)
        print(sample_json)
    return{"knowledge":sample_json}

@app.get("/template/get")
def get_template():
    with open('C:\\Users\\29884\\Desktop\\北航课题\\demo\\template.json','r',encoding='utf-8') as file:
        sample_json = json.load(file)
        return {
            "background":sample_json.get("background"),
            "structure":sample_json.get("structure"),
            "replace":sample_json.get("replace")
        }

@app.post("/template/generate")
def generate_template(query:Query):
    with open('C:\\Users\\29884\\Desktop\\北航课题\\demo\\template.json','w',encoding='utf-8') as file:
        content = json.dumps({"background":query.background, "structure":query.structure,"replace":query.replace})
        file.write(content)
    return {"result":"OK"}