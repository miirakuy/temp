import os
import random
from flask import (
  Flask, 
  request, 
  abort, 
  jsonify
)
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import func
from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  """Initialize the core application."""
  app = Flask(__name__, instance_relative_config=True)
  setup_db(app)

  """Initialize Plugin."""
  db = SQLAlchemy(app)

  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app, resource={r"/api.*": {"origin": "*"}})

  def paginate_questions(request, selection):
    """
    Returns questions to be displayed per user request.
    Args:
        request: A integer value representing a page number.
        selection: A list of dictionaries representing all questions. 
    Returns:
        current_questions: A list of dictionaries representing sets of questions.
        The number of questions to be displayed is controled by QUESTIONS_PER_PAGE constant.
    """
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions
  
  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow_Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Contorl-Allow_Methods', 'GET,POST,DELETE')
    return response

  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories', methods=['GET'])
  def retrieve_categories():
    """
    Returns all category ids and corresponding types.
    Args:
        None.
    Returns:
        success: A boolean True representing information retrieval succeeds.
        categories: A dictionaly representing all categories.
    Raises:
        HTTP 404 Not Found: If category information retrieval fails.
    """
    try:
      c_selection = Category.query.order_by(Category.id).all()

      categories_dict = { category.id: category.type for category in c_selection }
      
      return jsonify({
        'success': True,
        'categories': categories_dict
      })
    
    except Exception:
      abort(404)

  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions', methods=['GET'])
  def retrieve_questions():
    """
    Returns all questions, total number of questions, 
    all categories, and the categories in the currently displayed page.

    Args:
        None.
    Returns:
        success: A boolean True representing information retrieval succeeds.
        questions: A list of dictionaries representing sets of questions. 
        total_questions: An integer value representing a total number of questions.
        categories: A dictionaly representing all categories.
        current_category: A list of the categories of currently displayed questions.
    Raises:
        HTTP 404 Not Found: If no questions can be displayed on a page, 
        or information retrieval fails.
    """
    try:
      q_selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, q_selection)

      c_selection = Category.query.order_by(Category.id).all()
      categories_dict = { category.id: category.type for category in c_selection }

      current_category = [ question['category'] for question in current_questions ]

      if len(current_questions) == 0:
        abort(404)

      return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': len(q_selection),
        'categories': categories_dict,
        'current_category': current_category
      })

    except Exception:
      abort(404)

  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:id>', methods=['DELETE'])
  def delete_question(id):
    """
    Returns an id of the deleted question and new total number of questions.
    Args:
        id: An integer value representing an id of a question to delete.
    Returns:
        success: A boolean True representing delete operation succeeds.
        deleted: An integer value representing an id of the deleted question.
        total_questions: An integer value representing a total number of questions after the deletion.
    Raises:
        HTTP 404 Not Found: If there is no question to delete.
        HTTP 422 Unprocessable Entity Error: If question deletion fails.
    """
    try:
      selection = Question.query.filter(Question.id == id).one_or_none()

      if selection is None:
        abort(404)

      selection.delete()
      q_selection = Question.query.order_by(Question.id).all()

      return jsonify({
        'success': True,
        'deleted': id,
        'total_questions': len(q_selection)
      })
    
    except Exception:
      abort(422)

    finally:
      db.session.close()

  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods=['POST'])
  def create_question():
    """
    Returns an id of the newly created question and new total number of questions.
    Args:
        None.
    Returns:
        success: A boolean True representing create operation succeeds.
        created: An integer value representing an id of the created question.
        total_questions: An integer value representing a total number of questions after the creation.
    Raises:
        HTTP 422 Unprocessable Entity Error: If no value is given, 
        or question creation fails.
    """
    body = request.get_json()

    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_difficulty = body.get('difficulty', None)
    new_category = body.get('category', None)

    if not (new_question and new_answer and new_difficulty and new_category):
      abort(422)

    try:
      question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)
      question.insert()

      return jsonify({
        'success': True,
        'created': question.id,
        'total_questions': len(Question.query.all())
      })

    except Exception:
      abort(422)

    finally:
      db.session.close()

  '''
  @TODO:
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/search', methods=['POST'])
  def search_questions():
    """
    Returns all searched questions, total number of questions, 
    and the categories of searched questions.

    Args:
        None.
    Returns:
        success: A boolean True representing search operation succeeds.
        questions: A list of dictionaries comprises of questions corresponding to the search term.
        total_questions: An integer value representing a total number of searched questions.
        current_category: A list of the categories of searched questions.
    Raises:
        HTTP 404 Not Found: If question retrieval by search term fails.
    """
    body = request.get_json()
    search_term = body.get('searchTerm', None)

    try:
      q_selection = Question.query.filter(Question.question.ilike('%{}%'.format(search_term))).all()
      search_result = [ question.format() for question in q_selection ]
      current_category = [ question.category for question in q_selection ]

      return jsonify({
        'success': True,
        'questions': search_result,
        'total_questions': len(q_selection),
        'current_category': current_category
      })

    except Exception:
      abort(404)

  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:id>/questions', methods=['GET'])
  def retrieve_by_category(id):
    """
    Returns all questions of the selected category, total number of 
    questions of the selected category, and the selected category.

    Args:
        id: An integer value representing a category.
    Returns:
        success: A boolean True representing information retrieval succeeds.
        questions: A list of dictionaries representing sets of questions.
        corresponding to the selected category.
        total_questions: An integer value representing a total number of questions.
        corresponding to the selected category.
        current_category: A list of the categories of currently displayed questions.
    Raises:
        HTTP 404 Not Found: If question or category information retrieval fails.
    """
    try:
      if id not in [0, 1, 2, 3, 4, 5, 6]:
        abort(404)

      q_selection = Question.query.filter_by(category=str(id)).order_by(Question.id).all()
      questions = [ question.format() for question in q_selection ]
      current_category = [ question.category for question in q_selection ]

      return jsonify({
        'success': True,
        'questions': questions,
        'total_questions': len(q_selection),
        'current_category': current_category
      })

    except Exception:
      abort(404)

  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def quizzes():
    """
    Returns question randomly from all questions of the selected 
    category or all questions.

    Args:
        None.
    Returns:
        success: A boolean True representing information retrieval succeeds.
        questions: A list of dictionaries representing sets of questions.
    Raises:
        HTTP 404 Not Found: If wrong category is given, or 
        question information retrieval fails.
    """
    body = request.get_json()
    previous_questions = body.get('previous_questions')
    quiz_category = body.get('quiz_category')

    try:
      if int(quiz_category['id']) not in [0, 1, 2, 3, 4, 5, 6]:
        abort(404)

      if quiz_category['id'] == 0:
        question = Question.query.filter(Question.id.notin_(previous_questions)).order_by(func.random()).first()
      else:
        question = Question.query.filter(Question.category == quiz_category['id']).filter(Question.id.notin_
        (previous_questions)).order_by(func.random()).first()

      return jsonify({
          'success': True,
          'question': question.format()
      })

    except Exception:
      abort(404)

  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      'success': False,
      'error': 400,
      'message': "bad request"
    }), 400

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success': False,
      'error': 404,
      'message': "resource not found"
    }), 404

  @app.errorhandler(405)
  def method_not_allowed(error):
    return jsonify({
      'success': False,
      'error': 405,
      'message': "method not allowed"
    }), 405


  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'success': False,
      'error': 422,
      'message': "unprocessable"
    }), 422

  @app.errorhandler(500)
  def internal_sever_error(error):
    return jsonify({
      'success': False,
      'error': 500,
      'message': "internal server error"
    }), 500

  return app
