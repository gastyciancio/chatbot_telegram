
import pdb
from chatbot.utils import search_with_sparql_of_similar_question
from qa_autocomplete.utils import read_json

CACHED_QUESTIONS_TEMPLATES_PATH = "static/cached_questions/templates.json"

def similar_query(id_entity_selected, similar_questions):
    templates = read_json(CACHED_QUESTIONS_TEMPLATES_PATH)
    final_response = ''
    for similar_question in similar_questions:
        for template in templates:
            if template['question_en'].lower() == similar_question[0].lower():
                sparql_of_similar_question = template['query_template_en']
                response = search_with_sparql_of_similar_question(sparql_of_similar_question, id_entity_selected)
                if response['answer'] != "":
                    final_response = final_response + 'Using the question "'+ template['question_en'] +'" the answer is: '+ response['answer']
    return {
        "final_answer":final_response
    }