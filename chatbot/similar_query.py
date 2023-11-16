
import pdb
from chatbot.utils import parse_similar_question
from qa_autocomplete.utils import read_json

CACHED_QUESTIONS_TEMPLATES_PATH = "static/cached_questions/templates.json"

def similar_query(similar_question, original_question):

    templates = read_json(CACHED_QUESTIONS_TEMPLATES_PATH)
    sparql_of_similar_question = None
    entity_similar_question = None
    for template in templates:
        if template['question_en'].lower() == similar_question.lower():
            sparql_of_similar_question = template['query_template_en']
            entity_similar_question = template['matches_en'][0]['entity']

    parse_similar_question_response = parse_similar_question(original_question, entity_similar_question)

    if parse_similar_question_response['entities_original_question'] != None:
        return {
            'similar_question_response': parse_similar_question_response,
            'sparql_of_similar_question': sparql_of_similar_question
        }
    else:
        return None
