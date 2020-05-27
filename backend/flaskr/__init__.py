import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

from utils import get_paginated_questions

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  cors = CORS(app, resource={'/':{'origins':'*'}})

  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
      response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')

      return response
      
  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route("/categories")
  def get_categories():
      try:
          categories = Category.query.all()
          d = {}
          for category in categories:
              d[category.id] = category.type
   
          return jsonify({
              'success': True,
              'categories': d
          }), 200
      except:
          abort(500)
          
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
  @app.route('/questions')
  def get_questions():
      questions = Question.query.order_by(Question.id).all()
      total_questions = len(questions)
      categories = Category.query.order_by(Category.id).all()

      current_questions = get_paginated_questions(request, questions, QUESTIONS_PER_PAGE)

      if len(current_questions) == 0: 
          abort(404)
      
      d = {}
      for category in categories:
          d[category.id] = category.type

      return jsonify({
          'success': True,
          'total_questions': total_questions,
          'categories': d,
          'questions': current_questions  
      }), 200
  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
      try:
          question = Question.query.get(question_id)
          question.delete()

          return jsonify({
                  'success': True,
                  'message': "Questions get deleted successfully"
              }), 200  
      except:
          abort(422)

  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route("/questions", methods=['POST'])
  def create_question():
      data = request.get_json()

      question = data.get('question', None)
      answer = data.get('answer', None)
      category = data.get('category', None)
      difficulty = data.get('difficulty', None)

      if (not question) or (not answer) or (not category) or (not difficulty):
          abort(422)

      try:
          question = Question(
              question=question, 
              answer=answer, 
              category=category, 
              difficulty=difficulty)

          question.insert()

          return jsonify({
              'success': True,
              'message': 'Question gets created successfully'
          }), 201

      except:
          abort(422)

  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/questions/search', methods=['POST'])
  def search_questions():
      data = request.get_json()
      search_term = data.get('searchTerm', '')

      if search_term == '':
          abort(422)
 
      try:
          questions = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()

          if len(questions) == 0: 
              abort(404)
          
          paginated_questions = get_paginated_questions(request, questions, QUESTIONS_PER_PAGE)

          return jsonify({
                  'success': True,
                  'questions': paginated_questions,
                  'total_questions': len(Question.query.all())
              }), 200

      except:
          abort(404)

  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route("/categories/<int:category_id>/questions")
  def get_questions_by_category(category_id):
      category = Category.query.filter_by(id=category_id).one_or_none()

      if (category is None):
          abort(422)

      questions = Question.query.filter_by(category=category_id).all()

      paginated_questions = get_paginated_questions(request, questions, QUESTIONS_PER_PAGE)

      return jsonify({
              'success': True,
              'questions': paginated_questions,
              'total_questions': len(questions),
              'category': category.type
          })

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
  def get_quiz_question():
      data = request.get_json()
      previous_questions = data.get('previous_questions')
      quiz_category = data.get('quiz_category')

      if (not quiz_category) or (not previous_questions):
          abort(400)

      if quiz_category['id'] == 0:
          questions = Question.query.all()
      else:
          questions = Question.query.filter_by(category=quiz_category['id']).all()

      # get a random question 
      next_question = questions[random.randint(0, len(questions)-1)]

      found = True
      num_of_tries = 0
      while found:
          if next_question.id in previous_questions:
              if num_of_tries >= len(questions) - 1: break
              else: num_of_tries += 1
              next_question = questions[random.randint(0, len(questions)-1)]
          else:
              found = False
    
      return jsonify({
          'success': True,
          'question': next_question.format()
      }), 200

  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(422)
  def unprocessable(error):
      return jsonify({
          "success": False,
          "error": 422,
          "message": "unprocessable"
      }), 422

  @app.errorhandler(404)
  def not_found(error):
      return jsonify({
          "success": False,
          "error": 404,
          "message": "Resource not found"  
      }), 404

  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
           'success': False,
           'error': 400,
           'message': 'Bad request error'
       }), 400

  @app.errorhandler(500)
  def internal_server_error(error):
      return jsonify({
          'success': False,
          'error': 500,
          'message': 'Internal server error'
      }), 500
      
  return app

    