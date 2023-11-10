
from queries import search_item_to_QAwiki, search_id_to_QAwiki
import pdb
from utils import parse_similar_question

def similar_query(similar_question, original_question):
    response_QAwiki_id, similar_questions = search_id_to_QAwiki(similar_question)
    response_QAwiki_query = search_item_to_QAwiki(response_QAwiki_id)
    sparql_of_similar_question = response_QAwiki_query["query"]

    parse_similar_question_response = parse_similar_question(similar_question, original_question, sparql_of_similar_question)

    if parse_similar_question_response['entities_original_question'] != None:
        return {
            'similar_question_response': parse_similar_question_response,
            'sparql_of_similar_question': sparql_of_similar_question
        }
    else:
        return None
