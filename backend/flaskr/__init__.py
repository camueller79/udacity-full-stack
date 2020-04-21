import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import sys
from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app, resources={'/': {'origins': '*'}})

  '''
  Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

  '''
  an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def get_categories():

    # get all categories and add to a dictionary
    categories = Category.query.all()
    cat_dict = {}
    for category in categories:
      #cat_dict[category.id] = category.type
      # cat_dict.append(str(category.id) + ":" + category.type)
      cat_dict[category.id] = category.type

    # if no categories found, abort with 404 error
    if (len(cat_dict) == 0):
      abort(404)

    # return data to view
    return jsonify({
      'success': True,
      'categories': cat_dict
    })

  ''' 
  endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 
  '''
  
  @app.route('/questions')
  def get_questions():
    # get all questions and paginate them into a selection
    all_questions = Question.query.all()
    total = len(all_questions)
    selection = paginate(request, all_questions)
    # get all categories, then add them to a list
    categories_query = Category.query.all()
    categories = []
    for category in categories_query:
      categories.append(category.type)

    # abort with 404 error if no questions
    if (len(selection) == 0):
      abort(404)
    # return json data
    return jsonify({
      'success': True,
      'questions': selection,
      'total_questions': total,
      'categories': categories
    })
    
  '''
  An endpoint to DELETE question using a question ID. 
  '''
  @app.route('/questions/<int:id>', methods=['DELETE'])
  def delete_question(id):
    # get the question from the database
    question = Question.query.get(id)
    #check to see if the question was found
    if question is None:
      abort(404)
    try:
      # we have a question, so let's delete it
      question.delete()
      # return a response indicating success
      return jsonify({
        'success': True,
        'deleted': id
      })
    except:
      # error deleting question
      abort(422)

  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  as well as search for existing questions

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods=['POST'])
  def post_question():

    # get the request
    body = request.get_json()

    # if we were sent a search term, then we search existing questions
    if (body.get('searchTerm')):
      search_term = body.get('searchTerm')
      selection = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()

      if (len(selection) == 0):
        abort(404)
      
      # paginate the results
      results = paginate(request, selection)

      # return results
      return jsonify({
        'success': True,
        'questions': results,
        'total_questions': len(results)
      })
    # if no search term, then we try to add a new question
    else:
      # get data from body
      new_question = body.get('question')
      new_answer = body.get('answer')
      new_difficulty = body.get('difficulty')
      new_category = body.get('category')

      # make sure each field has data in it
      if ((new_question is None) or (new_answer is None) or (new_difficulty is None) or (new_category is None)):
        abort(422)
      try:
        question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)
        question.insert()

        # get all questions including new one, and paginate
        selection = Question.query.all()
        current_questions = paginate(request, selection)

        # return data for view
        return jsonify({
          'success': True,
          'created': question.id,
          'question_created': question.question,
          'questions': current_questions,
          'total_questions': len(selection)
        })
      except:
        # abort on exception
        abort(422)

  
  ''' 
  GET endpoint to get questions based on category. 
  '''
  @app.route('/categories/<int:id>/questions')
  def get_questions_by_category(id):
    
    # get the category by id
    category = Category.query.get(id)
    if not category:
      abort(400)
    
    # get questions in the selected category
    questions = Question.query.filter_by(category=category.id).all()

    # paginate the results
    question_paginated = paginate(request, questions)

    # return the results
    return jsonify({
      'success': True,
      'questions': question_paginated,
      'total_questions': len(questions),
      'current_category': category.type
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
  def post_random_quiz_question():

    # get the request body
    body = request.get_json()
    if not body:
      abort(400)

    # get the previous questions
    previous_questions = body['previous_questions']
    # get the category
    quiz_category_id = body['quiz_category']['id']

    if (quiz_category_id == 0 ):
      questions = Question.query.all()
    else:
      questions = Question.query.filter_by(category=quiz_category_id).all()
    total = len(questions)
    if (total == len(previous_questions)):
      return jsonify({'success':True})

    # new list of unused questions
    new_list = []
    for q in questions:
      if (q.id not in previous_questions):
        new_list.append(q)
    question = random.choice(new_list)

    return jsonify({
      'success': True,
      'question': question.format()
    })

    # if (quiz_category_id == 0 ):
    #   if previous_questions is None:
    #     print(previous_questions)
    #     questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
    #   else:
    #     questions = Question.query.all()
    # else:
    #   category = Category.query.get(quiz_category_id)
    #   if previous_questions is None:
    #     print(previous_questions)
    #     questions = Question.query.filter(Question.id.notin_(previous_questions),Question.category == category.id).all()
    #   else:
    #     questions = Question.query.filter(Question.category == category.id).all()

    # next_question = random.choice(questions).format()
    # if not next_question:
    #   abort(404)
    # # next_question = questions[0].format()
    # if next_question is None:
    #   next_question = False
    # return jsonify({
    #   'success': True,
    #   'question': next_question
    # })

  '''
  Error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success': False,
      'error': 404,
      'message': "resource not found"
    }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'success': False,
      'error': 422,
      'message': "unprocessable"
    }), 422
  
  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      'success': False,
      'error': 400,
      'message': "bad request"
    }), 400
  return app

    