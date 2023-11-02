
from queries import search_item_to_QAwiki, search_id_to_QAwiki
import pdb
from utils import parse_similar_question

def similar_query(similar_question, original_question):
    response_QAwiki_id, similar_questions = search_id_to_QAwiki(similar_question)
    response_QAwiki_query = search_item_to_QAwiki(response_QAwiki_id)

    sparql_value_of_original_question, error = parse_similar_question(response_QAwiki_query["query"], similar_question ,original_question)
    if error == None:
        return sparql_value_of_original_question, error
    else:
        return None, error
