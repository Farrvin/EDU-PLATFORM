from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import random
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learning_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

db = SQLAlchemy(app)
mail = Mail(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    difficulty = db.Column(db.String(10), nullable=False)  # 'easy', 'medium', 'hard'
    topic = db.Column(db.String(100), nullable=False)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    level = db.Column(db.Integer, nullable=False)  # 1, 2, or 3
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    time_spent = db.Column(db.Integer, nullable=False)  # in seconds
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class InterviewResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    questions_answers = db.Column(db.Text, nullable=False)  # JSON string
    score = db.Column(db.Integer, nullable=False)
    feedback = db.Column(db.Text)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudentEngagement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    activity_duration = db.Column(db.Integer, nullable=False)  # in seconds
    inactivity_periods = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# No login system - direct access

# Learning Resources with YouTube links
LEARNING_RESOURCES = {
    'Python': {
        'basic': [
            {'title': 'Python Tutorial for Beginners', 'url': 'https://www.youtube.com/watch?v=_uQrJ0TkZlc', 'duration': '6:14:07'},
            {'title': 'Python Crash Course', 'url': 'https://www.youtube.com/watch?v=JJmcL1N2KQs', 'duration': '4:26:52'},
            {'title': 'Learn Python - Full Course', 'url': 'https://www.youtube.com/watch?v=rfscVS0vtbw', 'duration': '4:26:52'}
        ],
        'intermediate': [
            {'title': 'Python OOP Tutorial', 'url': 'https://www.youtube.com/watch?v=ZDa-Z5JzLYM', 'duration': '2:31:28'},
            {'title': 'Python Data Structures', 'url': 'https://www.youtube.com/watch?v=R-HLU9Fl5ug', 'duration': '1:54:23'},
            {'title': 'Python Functions Deep Dive', 'url': 'https://www.youtube.com/watch?v=9Os0o3wzS_I', 'duration': '2:12:11'}
        ],
        'advanced': [
            {'title': 'Advanced Python Concepts', 'url': 'https://www.youtube.com/watch?v=WiQqqB9MlkA', 'duration': '2:52:27'},
            {'title': 'Python Decorators', 'url': 'https://www.youtube.com/watch?v=FsAPt_9Bf3U', 'duration': '1:00:56'},
            {'title': 'Python Generators', 'url': 'https://www.youtube.com/watch?v=bD05uGo_sVI', 'duration': '34:24'}
        ]
    },
    'JavaScript': {
        'basic': [
            {'title': 'JavaScript Tutorial for Beginners', 'url': 'https://www.youtube.com/watch?v=PkZNo7MFNFg', 'duration': '3:26:41'},
            {'title': 'JavaScript Crash Course', 'url': 'https://www.youtube.com/watch?v=hdI2bqOjy3c', 'duration': '1:40:11'},
            {'title': 'Learn JavaScript', 'url': 'https://www.youtube.com/watch?v=jS4aFq5-91M', 'duration': '8:56:26'}
        ],
        'intermediate': [
            {'title': 'JavaScript DOM Manipulation', 'url': 'https://www.youtube.com/watch?v=5fb2aPlgoys', 'duration': '2:26:27'},
            {'title': 'Async JavaScript', 'url': 'https://www.youtube.com/watch?v=PoRJizFvM7s', 'duration': '1:47:42'},
            {'title': 'JavaScript ES6+', 'url': 'https://www.youtube.com/watch?v=NCwa_xi0Uuc', 'duration': '2:21:37'}
        ],
        'advanced': [
            {'title': 'Advanced JavaScript Concepts', 'url': 'https://www.youtube.com/watch?v=Mus_vwhTCq0', 'duration': '3:25:23'},
            {'title': 'JavaScript Design Patterns', 'url': 'https://www.youtube.com/watch?v=kuirGzhGhyw', 'duration': '1:15:47'},
            {'title': 'JavaScript Performance', 'url': 'https://www.youtube.com/watch?v=8aGhZQkoFbQ', 'duration': '1:42:15'}
        ]
    },
    'Java': {
        'basic': [
            {'title': 'Java Tutorial for Beginners', 'url': 'https://www.youtube.com/watch?v=eIrMbAQSU34', 'duration': '9:18:49'},
            {'title': 'Java Programming', 'url': 'https://www.youtube.com/watch?v=xk4_1vDrzzo', 'duration': '14:13:00'},
            {'title': 'Learn Java 8', 'url': 'https://www.youtube.com/watch?v=grEKMHGYyns', 'duration': '9:58:32'}
        ],
        'intermediate': [
            {'title': 'Java OOP Concepts', 'url': 'https://www.youtube.com/watch?v=6T_HgnjoYwM', 'duration': '2:19:33'},
            {'title': 'Java Collections Framework', 'url': 'https://www.youtube.com/watch?v=NyIxIEQckLs', 'duration': '2:52:27'},
            {'title': 'Java Exception Handling', 'url': 'https://www.youtube.com/watch?v=1XAfapkBQjk', 'duration': '1:23:45'}
        ],
        'advanced': [
            {'title': 'Advanced Java Programming', 'url': 'https://www.youtube.com/watch?v=Ae-r8hsbPUo', 'duration': '4:23:46'},
            {'title': 'Java Multithreading', 'url': 'https://www.youtube.com/watch?v=r_MbozD32eo', 'duration': '2:34:12'},
            {'title': 'Java Spring Framework', 'url': 'https://www.youtube.com/watch?v=VvGjZgqojMc', 'duration': '3:12:45'}
        ]
    }
}

# Assignment Questions
ASSIGNMENT_QUESTIONS = {
    'Python': {
        'basic': [
            {'title': 'Variables and Data Types', 'description': 'Create variables of different data types and perform basic operations.', 'type': 'code', 'points': 10, 'time_estimate': '30 min'},
            {'title': 'Control Structures', 'description': 'Write a program using if-else statements and loops.', 'type': 'code', 'points': 15, 'time_estimate': '45 min'},
            {'title': 'Functions', 'description': 'Create functions to solve basic mathematical problems.', 'type': 'code', 'points': 15, 'time_estimate': '45 min'},
            {'title': 'Lists and Strings', 'description': 'Manipulate lists and strings using built-in methods.', 'type': 'code', 'points': 10, 'time_estimate': '30 min'}
        ],
        'advanced': [
            {'title': 'Object-Oriented Programming', 'description': 'Design and implement classes with inheritance and polymorphism.', 'type': 'code', 'points': 25, 'time_estimate': '90 min'},
            {'title': 'File Handling', 'description': 'Read from and write to files, handle exceptions properly.', 'type': 'code', 'points': 20, 'time_estimate': '60 min'},
            {'title': 'Data Analysis Project', 'description': 'Use pandas and numpy to analyze a dataset and create visualizations.', 'type': 'text', 'points': 30, 'time_estimate': '120 min'},
            {'title': 'Web Scraping', 'description': 'Build a web scraper using requests and BeautifulSoup.', 'type': 'code', 'points': 25, 'time_estimate': '90 min'}
        ]
    },
    'JavaScript': {
        'basic': [
            {'title': 'Variables and Functions', 'description': 'Create variables and functions to perform basic calculations.', 'type': 'code', 'points': 10, 'time_estimate': '30 min'},
            {'title': 'DOM Manipulation', 'description': 'Use JavaScript to modify HTML elements and handle events.', 'type': 'code', 'points': 15, 'time_estimate': '45 min'},
            {'title': 'Arrays and Objects', 'description': 'Work with arrays and objects to store and manipulate data.', 'type': 'code', 'points': 15, 'time_estimate': '45 min'},
            {'title': 'Form Validation', 'description': 'Create a form with client-side validation using JavaScript.', 'type': 'code', 'points': 10, 'time_estimate': '30 min'}
        ],
        'advanced': [
            {'title': 'Asynchronous Programming', 'description': 'Implement promises, async/await, and fetch API calls.', 'type': 'code', 'points': 25, 'time_estimate': '90 min'},
            {'title': 'React Component', 'description': 'Build a React component with state management and props.', 'type': 'code', 'points': 20, 'time_estimate': '60 min'},
            {'title': 'API Integration', 'description': 'Create a web application that consumes a REST API.', 'type': 'text', 'points': 30, 'time_estimate': '120 min'},
            {'title': 'Testing', 'description': 'Write unit tests for JavaScript functions using Jest.', 'type': 'code', 'points': 25, 'time_estimate': '90 min'}
        ]
    }
}

# Mock data for questions (you can expand this)
SAMPLE_QUESTIONS = {
    'Python': [
        {
            'question': 'What is the correct way to create a list in Python?',
            'options': ['list = []', 'list = ()', 'list = {}', 'list = ""'],
            'correct': 0,
            'difficulty': 'easy',
            'topic': 'Data Structures'
        },
        {
            'question': 'Which keyword is used to define a function in Python?',
            'options': ['function', 'def', 'define', 'func'],
            'correct': 1,
            'difficulty': 'easy',
            'topic': 'Functions'
        },
        {
            'question': 'What is the output of print(2**3)?',
            'options': ['6', '8', '9', '23'],
            'correct': 1,
            'difficulty': 'medium',
            'topic': 'Operators'
        },
        {
            'question': 'Which of the following is used for exception handling in Python?',
            'options': ['try-catch', 'try-except', 'catch-throw', 'handle-error'],
            'correct': 1,
            'difficulty': 'medium',
            'topic': 'Exception Handling'
        },
        {
            'question': 'What is a decorator in Python?',
            'options': ['A design pattern', 'A function that modifies another function', 'A class method', 'A variable type'],
            'correct': 1,
            'difficulty': 'hard',
            'topic': 'Advanced Concepts'
        }
    ],
    'JavaScript': [
        {
            'question': 'How do you declare a variable in JavaScript?',
            'options': ['var x;', 'variable x;', 'declare x;', 'x variable;'],
            'correct': 0,
            'difficulty': 'easy',
            'topic': 'Variables'
        },
        {
            'question': 'Which method is used to add an element to the end of an array?',
            'options': ['add()', 'append()', 'push()', 'insert()'],
            'correct': 2,
            'difficulty': 'easy',
            'topic': 'Arrays'
        },
        {
            'question': 'What is the correct way to write a JavaScript array?',
            'options': ['var colors = "red", "green", "blue"', 'var colors = ["red", "green", "blue"]', 'var colors = (1:"red", 2:"green", 3:"blue")', 'var colors = 1 = ("red"), 2 = ("green"), 3 = ("blue")'],
            'correct': 1,
            'difficulty': 'medium',
            'topic': 'Arrays'
        }
    ],
    'Java': [
        {
            'question': 'Which of the following is the correct way to declare a main method in Java?',
            'options': ['public static void main(String[] args)', 'static public void main(String[] args)', 'public void main(String[] args)', 'void main(String[] args)'],
            'correct': 0,
            'difficulty': 'easy',
            'topic': 'Methods'
        },
        {
            'question': 'What is the size of int in Java?',
            'options': ['16 bits', '32 bits', '64 bits', '8 bits'],
            'correct': 1,
            'difficulty': 'medium',
            'topic': 'Data Types'
        }
    ]
}

# Comedy content for breaks
COMEDY_CONTENT = [
    "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
    "How many programmers does it take to change a light bulb? None, that's a hardware problem! 💡",
    "Why do Java developers wear glasses? Because they can't C#! 🤓",
    "A SQL query goes into a bar, walks up to two tables and asks: 'Can I join you?' 🍺",
    "Why did the programmer quit his job? He didn't get arrays! 📊"
]

# Routes
@app.route('/')
def index():
    return render_template('login_portal.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        user_type = data.get('user_type')
        
        user = User.query.filter_by(username=username, user_type=user_type).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_type'] = user_type
            session['username'] = username
            return jsonify({'success': True, 'user_type': user_type})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
    return render_template('login_portal.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('user_type')
    
    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'success': False, 'message': 'Username already exists'})
    
    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({'success': False, 'message': 'Email already registered'})
    
    # Create new user
    new_user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        user_type=user_type
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        print(f"✓ New {user_type} registered: {username}")
        return jsonify({'success': True, 'message': 'Registration successful! Please login.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'})

@app.route('/teacher/dashboard')
def teacher_dashboard_auth():
    if 'user_id' not in session or session.get('user_type') != 'teacher':
        return redirect(url_for('login'))
    return render_template('teacher_dashboard.html')

@app.route('/student/dashboard')
def student_dashboard_auth():
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect(url_for('login'))
    return render_template('student_dashboard.html')

@app.route('/teacher')
def teacher_dashboard():
    return render_template('teacher_dashboard.html')

@app.route('/student')
def student_dashboard():
    return render_template('student_dashboard.html')

# Teacher Routes
@app.route('/teacher/subjects')
def teacher_subjects():
    # Get subjects from the first teacher (demo mode)
    teacher = User.query.filter_by(user_type='teacher').first()
    if teacher:
        subjects = Subject.query.filter_by(teacher_id=teacher.id).all()
    else:
        subjects = []
    return render_template('teacher_subjects.html', subjects=subjects)

@app.route('/teacher/add_subject', methods=['POST'])
def add_subject():
    data = request.get_json()
    # Get first teacher for demo mode
    teacher = User.query.filter_by(user_type='teacher').first()
    if not teacher:
        return jsonify({'success': False, 'message': 'No teacher found'})
    
    subject = Subject(
        name=data.get('name'),
        description=data.get('description'),
        teacher_id=teacher.id
    )
    
    db.session.add(subject)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Subject added successfully'})

@app.route('/teacher/edit_subject/<int:subject_id>', methods=['POST'])
def edit_subject(subject_id):
    data = request.get_json()
    subject = Subject.query.get_or_404(subject_id)
    
    subject.name = data.get('name')
    subject.description = data.get('description')
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Subject updated successfully'})

@app.route('/teacher/delete_subject/<int:subject_id>', methods=['DELETE'])
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    db.session.delete(subject)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Subject deleted successfully'})

@app.route('/teacher/generate_question_paper', methods=['POST'])
def generate_question_paper():
    data = request.get_json()
    subject_name = data.get('subject')
    difficulty = data.get('difficulty', 'medium')
    num_questions = min(max(int(data.get('num_questions', 10)), 10), 30)  # Min 10, Max 30
    
    if subject_name in SAMPLE_QUESTIONS:
        questions = SAMPLE_QUESTIONS[subject_name]
        if difficulty != 'all':
            questions = [q for q in questions if q['difficulty'] == difficulty]
        
        # Duplicate questions if needed to meet the requirement
        while len(questions) < num_questions:
            questions.extend(SAMPLE_QUESTIONS[subject_name])
        
        selected_questions = random.sample(questions, num_questions)
        
        # Remove correct answers for question paper
        question_paper = []
        for q in selected_questions:
            question_paper.append({
                'question': q['question'],
                'options': q['options'],
                'difficulty': q['difficulty'],
                'topic': q['topic']
                # Note: 'correct' answer is removed from question paper
            })
        
        return jsonify({'success': True, 'questions': question_paper})
    
    return jsonify({'success': False, 'message': 'Subject not found'})

@app.route('/teacher/student_performance')
def student_performance():
    # Get first teacher for demo mode (no login system)
    teacher = User.query.filter_by(user_type='teacher').first()
    if not teacher:
        return render_template('student_performance.html', 
                               performance_data=[], 
                               students_data=[], 
                               interview_data=[],
                               analytics_data={})
    
    # Get all quiz results for performance analysis
    quizzes = db.session.query(Quiz, User, Subject).join(User, Quiz.student_id == User.id).join(Subject, Quiz.subject_id == Subject.id).filter(Subject.teacher_id == teacher.id).all()
    
    performance_data = []
    for quiz, student, subject in quizzes:
        performance_data.append({
            'student_name': student.username,
            'subject': subject.name,
            'level': quiz.level,
            'score': quiz.score,
            'total_questions': quiz.total_questions,
            'percentage': round((quiz.score / quiz.total_questions) * 100, 2),
            'time_spent': quiz.time_spent,
            'completed_at': quiz.completed_at.strftime('%Y-%m-%d %H:%M'),
            'type': 'quiz'
        })
    
    # Get all interview results
    interviews = db.session.query(InterviewResult, User, Subject).join(User, InterviewResult.student_id == User.id).join(Subject, InterviewResult.subject_id == Subject.id).filter(Subject.teacher_id == teacher.id).all()
    
    interview_data = []
    for interview, student, subject in interviews:
        max_score = len(json.loads(interview.questions_answers)) * 5
        percentage = round((interview.score / max_score) * 100, 2) if max_score > 0 else 0
        interview_data.append({
            'student_name': student.username,
            'subject': subject.name,
            'score': interview.score,
            'max_score': max_score,
            'percentage': percentage,
            'feedback': interview.feedback,
            'completed_at': interview.completed_at.strftime('%Y-%m-%d %H:%M'),
            'type': 'interview'
        })
    
    # Get all registered students with their counts
    students = User.query.filter_by(user_type='student').all()
    students_data = []
    for student in students:
        quiz_count = Quiz.query.filter_by(student_id=student.id).count()
        interview_count = InterviewResult.query.filter_by(student_id=student.id).count()
        
        # Calculate average scores
        student_quizzes = Quiz.query.filter_by(student_id=student.id).all()
        avg_quiz_score = 0
        if student_quizzes:
            total_percentage = sum((q.score / q.total_questions) * 100 for q in student_quizzes)
            avg_quiz_score = round(total_percentage / len(student_quizzes), 2)
        
        student_interviews = InterviewResult.query.filter_by(student_id=student.id).all()
        avg_interview_score = 0
        if student_interviews:
            total_percentage = 0
            for interview in student_interviews:
                max_score = len(json.loads(interview.questions_answers)) * 5
                if max_score > 0:
                    total_percentage += (interview.score / max_score) * 100
            avg_interview_score = round(total_percentage / len(student_interviews), 2) if student_interviews else 0
        
        students_data.append({
            'username': student.username,
            'email': student.email,
            'created_at': student.created_at,
            'quiz_count': quiz_count,
            'interview_count': interview_count,
            'avg_quiz_score': avg_quiz_score,
            'avg_interview_score': avg_interview_score
        })
    
    # Generate analytics data for charts
    analytics_data = {
        'student_comparison': [],
        'subject_performance': {},
        'performance_trends': [],
        'score_distributions': {
            'quiz': {'0-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0},
            'interview': {'0-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0}
        }
    }
    
    # Student comparison data
    for student_data in students_data:
        analytics_data['student_comparison'].append({
            'student': student_data['username'],
            'quiz_avg': student_data['avg_quiz_score'],
            'interview_avg': student_data['avg_interview_score']
        })
    
    # Subject performance data
    for perf in performance_data:
        subject = perf['subject']
        if subject not in analytics_data['subject_performance']:
            analytics_data['subject_performance'][subject] = {'quiz': [], 'interview': []}
        analytics_data['subject_performance'][subject]['quiz'].append(perf['percentage'])
    
    for interview in interview_data:
        subject = interview['subject']
        if subject not in analytics_data['subject_performance']:
            analytics_data['subject_performance'][subject] = {'quiz': [], 'interview': []}
        analytics_data['subject_performance'][subject]['interview'].append(interview['percentage'])
    
    # Score distribution data
    for perf in performance_data:
        percentage = perf['percentage']
        if percentage <= 20:
            analytics_data['score_distributions']['quiz']['0-20'] += 1
        elif percentage <= 40:
            analytics_data['score_distributions']['quiz']['21-40'] += 1
        elif percentage <= 60:
            analytics_data['score_distributions']['quiz']['41-60'] += 1
        elif percentage <= 80:
            analytics_data['score_distributions']['quiz']['61-80'] += 1
        else:
            analytics_data['score_distributions']['quiz']['81-100'] += 1
    
    for interview in interview_data:
        percentage = interview['percentage']
        if percentage <= 20:
            analytics_data['score_distributions']['interview']['0-20'] += 1
        elif percentage <= 40:
            analytics_data['score_distributions']['interview']['21-40'] += 1
        elif percentage <= 60:
            analytics_data['score_distributions']['interview']['41-60'] += 1
        elif percentage <= 80:
            analytics_data['score_distributions']['interview']['61-80'] += 1
        else:
            analytics_data['score_distributions']['interview']['81-100'] += 1
    
    # Performance trends (combine quiz and interview data by date)
    all_performance = performance_data + interview_data
    all_performance.sort(key=lambda x: x['completed_at'])
    analytics_data['performance_trends'] = all_performance
    
    return render_template('student_performance.html', 
                           performance_data=performance_data, 
                           students_data=students_data,
                           interview_data=interview_data,
                           analytics_data=analytics_data)

@app.route('/teacher/predict_performance', methods=['POST'])
def predict_performance():
    # ML-powered teacher performance prediction
    
    data = request.get_json()
    hours_studied = data.get('hours_studied')
    attendance_percentage = data.get('attendance_percentage')
    previous_score = data.get('previous_score')
    
    if hours_studied is not None and attendance_percentage is not None and previous_score is not None:
        # Use ML model for prediction
        if ml_model:
            features = np.array([[hours_studied, attendance_percentage, previous_score]])
            predicted_score = ml_model.predict(features)[0]
            predicted_score = round(predicted_score, 2)
            
            # Generate recommendations based on prediction
            recommendations = []
            if predicted_score < 60:
                recommendations.extend([
                    "Focus on foundational concepts",
                    "Increase study hours gradually",
                    "Improve class attendance",
                    "Provide additional learning resources"
                ])
            elif predicted_score < 75:
                recommendations.extend([
                    "Good progress! Continue current study pattern",
                    "Focus on weak areas identified in assessments",
                    "Practice more challenging problems"
                ])
            else:
                recommendations.extend([
                    "Excellent performance predicted!",
                    "Challenge with advanced topics",
                    "Consider peer tutoring opportunities",
                    "Prepare for advanced certifications"
                ])
            
            return jsonify({
                'success': True,
                'predicted_score': predicted_score,
                'recommendations': recommendations,
                'model_used': 'ML Model'
            })
        else:
            return jsonify({'success': False, 'message': 'ML model not available'})
    
    # Fallback: use student data if no input provided
    student_id = data.get('student_id')
    if not student_id:
        student = User.query.filter_by(user_type='student').first()
        if student:
            student_id = student.id
        else:
            return jsonify({'success': False, 'message': 'No students found'})
    
    # Get student's quiz history for fallback prediction
    quizzes = Quiz.query.filter_by(student_id=student_id).all()
    
    if len(quizzes) < 1:
        return jsonify({
            'success': True,
            'predicted_score': round(random.uniform(65, 95), 2),
            'recommendations': [
                "Student shows potential in programming concepts",
                "Encourage more hands-on practice",
                "Focus on algorithmic thinking"
            ],
            'model_used': 'Demo Mode'
        })
    
    # Simple prediction based on recent performance
    recent_scores = [q.score / q.total_questions for q in quizzes[-5:]]
    avg_performance = sum(recent_scores) / len(recent_scores)
    predicted_score = avg_performance + random.uniform(-0.1, 0.1)
    predicted_score = max(0, min(1, predicted_score))
    
    recommendations = []
    if predicted_score < 0.6:
        recommendations.append("Focus on basic concepts")
        recommendations.append("Provide additional practice materials")
    elif predicted_score < 0.8:
        recommendations.append("Review medium difficulty topics")
        recommendations.append("Encourage more practice")
    else:
        recommendations.append("Challenge with advanced topics")
        recommendations.append("Consider leadership roles in group activities")
    
    return jsonify({
        'success': True,
        'predicted_score': round(predicted_score * 100, 2),
        'recommendations': recommendations,
        'model_used': 'Historical Data'
    })

@app.route('/teacher/topic_recommendations', methods=['POST'])
def topic_recommendations():
    # Mock teacher topic recommendations
    
    data = request.get_json()
    student_id = data.get('student_id')
    
    # If no student_id provided, use demo student
    if not student_id:
        student = User.query.filter_by(user_type='student').first()
        if student:
            student_id = student.id
    
    # Get student's quiz performance by topic
    quizzes = Quiz.query.filter_by(student_id=student_id).all() if student_id else []
    
    # Mock topic analysis (in real implementation, analyze by topic performance)
    weak_topics = ['Functions', 'Data Structures', 'Algorithms']
    strong_topics = ['Variables', 'Basic Syntax']
    
    recommendations = {
        'focus_topics': weak_topics,
        'strength_topics': strong_topics,
        'suggested_sequence': ['Review Variables', 'Practice Functions', 'Master Data Structures', 'Advanced Algorithms']
    }
    
    return jsonify({'success': True, 'recommendations': recommendations})

@app.route('/teacher/interview_results')
def teacher_interview_results():
    # Mock interview results
    # Get first teacher for demo mode (no login system)
    teacher = User.query.filter_by(user_type='teacher').first()
    if not teacher:
        return render_template('teacher_interview_results.html', interview_data=[])
    
    # Get interview results for teacher's subjects
    results = db.session.query(InterviewResult, User, Subject).join(User, InterviewResult.student_id == User.id).join(Subject, InterviewResult.subject_id == Subject.id).filter(Subject.teacher_id == teacher.id).all()
    
    interview_data = []
    for result, student, subject in results:
        interview_data.append({
            'student_name': student.username,
            'subject': subject.name,
            'score': result.score,
            'feedback': result.feedback,
            'completed_at': result.completed_at.strftime('%Y-%m-%d %H:%M'),
            'questions_answers': json.loads(result.questions_answers)
        })
    
    return render_template('teacher_interview_results.html', interview_data=interview_data)

# Student Routes
@app.route('/student/subjects')
def student_subjects():
    subjects = Subject.query.all()
    return render_template('student_subjects.html', subjects=subjects)

@app.route('/student/learning_path/<int:subject_id>')
def learning_path(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    # Mock progress calculation (can be enhanced with actual user data)
    progress = random.randint(20, 80)
    recommended_level = 'basic'
    
    resources = LEARNING_RESOURCES.get(subject.name, {
        'basic': [{'title': 'Introduction to ' + subject.name, 'url': '#', 'duration': '1:00:00'}],
        'intermediate': [{'title': 'Intermediate ' + subject.name, 'url': '#', 'duration': '2:00:00'}],
        'advanced': [{'title': 'Advanced ' + subject.name, 'url': '#', 'duration': '3:00:00'}]
    })
    
    return render_template('learning_path.html', 
                         subject=subject, 
                         recommended_level=recommended_level, 
                         progress=progress,
                         resources=resources)

@app.route('/student/quiz/<int:subject_id>/<int:level>')
def quiz(subject_id, level):
    subject = Subject.query.get_or_404(subject_id)
    
    # Get questions based on level
    question_counts = {1: 10, 2: 20, 3: 30}
    num_questions = question_counts.get(level, 10)
    
    if subject.name in SAMPLE_QUESTIONS:
        questions = SAMPLE_QUESTIONS[subject.name]
        # Duplicate questions if needed
        while len(questions) < num_questions:
            questions.extend(SAMPLE_QUESTIONS[subject.name])
        selected_questions = random.sample(questions, num_questions)
    else:
        selected_questions = []
    
    return render_template('quiz.html', 
                         subject=subject, 
                         level=level, 
                         questions=selected_questions)

@app.route('/student/submit_quiz', methods=['POST'])
def submit_quiz():
    
    data = request.get_json()
    subject_id = data.get('subject_id')
    level = data.get('level')
    answers = data.get('answers')
    time_spent = data.get('time_spent')
    
    # Calculate score
    subject = Subject.query.get(subject_id)
    if subject.name in SAMPLE_QUESTIONS:
        questions = SAMPLE_QUESTIONS[subject.name]
        score = 0
        for i, answer in enumerate(answers):
            if i < len(questions) and answer == questions[i]['correct']:
                score += 1
        
        total_questions = len(answers)
        percentage = (score / total_questions) * 100
        
        # Mock quiz result saving (since no login system)
        print(f"Quiz completed: Subject {subject.name}, Level {level}, Score {score}/{total_questions}")
        
        return jsonify({
            'success': True,
            'score': score,
            'total_questions': total_questions,
            'percentage': percentage,
            'passed': percentage >= 60
        })
    
    return jsonify({'success': False, 'message': 'Subject not found'})

@app.route('/student/submit_assignment', methods=['POST'])
def submit_assignment():
    data = request.get_json()
    subject_id = data.get('subject_id')
    answers = data.get('answers')  # List of answers submitted
    # Here you would process the answers; we will mock this for now

    feedback = ["Good attempt!", "Consider reviewing algorithms.", "Great explanation of concepts!"]  # Mock feedback
    score = len([ans for ans in answers if ans.strip() != ""]) * 5  # Mock scoring

    return jsonify({
        'success': True,
        'score': score,
        'feedback': feedback
    })

@app.route('/student/view_feedback/<int:assignment_id>', methods=['GET'])
def view_feedback(assignment_id):
    # Mock data for the purpose of this example
    feedback = "Excellent work on the assignment. Keep improving your coding skills!"
    details = {
        'questions_answered': 8,
        'correct_answers': 6,
        'percentage': 75,
        'feedback': feedback
    }
    return jsonify({'success': True, 'details': details})

# This route is now defined below, removing duplicate

# This route is now defined below with resume upload, removing duplicate

# This route is now defined below, removing duplicate

# New route for assignments
@app.route('/student/assignments/<int:subject_id>')
def assignments(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    # Get assignment questions for this subject
    basic_questions = ASSIGNMENT_QUESTIONS.get(subject.name, {}).get('basic', [])
    advanced_questions = ASSIGNMENT_QUESTIONS.get(subject.name, {}).get('advanced', [])
    
    return render_template('assignments.html', 
                         subject=subject, 
                         basic_questions=basic_questions,
                         advanced_questions=advanced_questions)

@app.route('/student/assignments/<int:subject_id>/download/<level>')
def download_assignment(subject_id, level):
    subject = Subject.query.get_or_404(subject_id)
    
    # Get assignment questions for the specified level
    questions = ASSIGNMENT_QUESTIONS.get(subject.name, {}).get(level, [])
    
    if not questions:
        return jsonify({'success': False, 'message': 'No assignments found for this level'})
    
    # Generate assignment content
    assignment_content = f"Assignment: {subject.name} - {level.title()} Level\n\n"
    assignment_content += "Instructions: Complete the following assignments to test your knowledge.\n\n"
    
    for i, question in enumerate(questions, 1):
        assignment_content += f"{i}. {question['title']}\n"
        assignment_content += f"   Description: {question['description']}\n"
        assignment_content += f"   Type: {question['type']}\n"
        assignment_content += f"   Points: {question['points']}\n"
        assignment_content += f"   Estimated Time: {question['time_estimate']}\n\n"
    
    # Return as downloadable file
    from flask import Response
    return Response(
        assignment_content,
        mimetype='text/plain',
        headers={'Content-Disposition': f'attachment; filename={subject.name}_{level}_assignments.txt'}
    )


# Route for interview with resume upload
@app.route('/student/interview/<int:subject_id>')
def interview(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    # Provide default interview questions based on subject
    default_questions = [
        "Tell me about yourself and your background.",
        f"What interests you most about {subject.name}?",
        f"Describe a project you've worked on using {subject.name}.",
        f"What are the key concepts in {subject.name} that you find challenging?",
        f"How do you stay updated with {subject.name} trends and developments?",
        "What are your career goals related to this technology?",
        "Describe a time when you had to debug a difficult problem.",
        "How do you approach learning new technologies?",
        "What would you say are your strengths in programming?",
        "Where do you see yourself in the next 5 years?"
    ]
    
    return render_template('interview.html', subject=subject, questions=default_questions)

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import numpy as np

# Load the trained ML model for student score prediction
try:
    ml_model = joblib.load('student_score_model.joblib')
    print("✓ ML model loaded successfully")
except FileNotFoundError:
    print("⚠ ML model not found. Please run train_model.py first")
    ml_model = None

# Sample data for training
training_data = {
    'attributes': [
        {'learning_score': 80, 'reading_score': 75, 'previous_exam_marks': 85, 'study_hours': 4, 'sleep_hours': 8, 'attendance_rate': 95, 'stress_level': 4},
        {'learning_score': 70, 'reading_score': 65, 'previous_exam_marks': 75, 'study_hours': 3, 'sleep_hours': 7, 'attendance_rate': 85, 'stress_level': 5},
        {'learning_score': 90, 'reading_score': 80, 'previous_exam_marks': 85, 'study_hours': 5, 'sleep_hours': 9, 'attendance_rate': 95, 'stress_level': 3},
        {'learning_score': 60, 'reading_score': 50, 'previous_exam_marks': 60, 'study_hours': 2, 'sleep_hours': 6, 'attendance_rate': 80, 'stress_level': 7},
        # Add more sample data as needed
    ],
    'scores': [88, 74, 92, 65]
}

# Train a simple model for student performance prediction
scaler = StandardScaler()
model = RandomForestRegressor(n_estimators=100, random_state=42)

X_train = scaler.fit_transform([[d['learning_score'], d['reading_score'], d['previous_exam_marks'], d['study_hours'], d['sleep_hours'], d['attendance_rate'], d['stress_level']] for d in training_data['attributes']])
y_train = training_data['scores']

model.fit(X_train, y_train)

# ML-powered performance prediction route
@app.route('/student/performance_prediction', methods=['GET', 'POST'])
def performance_prediction():
    if request.method == 'POST':
        print("📊 ML Prediction POST request received")
        hours_studied = float(request.form['hours_studied'])
        attendance_percentage = float(request.form['attendance_percentage'])
        previous_score = float(request.form['previous_score'])
        
        print(f"Input values - Hours: {hours_studied}, Attendance: {attendance_percentage}%, Previous: {previous_score}")

        # Make prediction if model is loaded
        if ml_model:
            features = np.array([[hours_studied, attendance_percentage, previous_score]])
            predicted_score = ml_model.predict(features)[0]
            predicted_score = round(predicted_score, 2)
            print(f"✅ ML Model prediction: {predicted_score}")
            return render_template('result.html', 
                                   predicted_score=predicted_score,
                                   hours_studied=hours_studied,
                                   attendance_percentage=attendance_percentage,
                                   previous_score=previous_score)
        else:
            print("❌ ML model is not available")
            return "ML model is not available. Please train the model first."
    return render_template('performance_prediction.html')

@app.route('/student/upload_resume', methods=['POST'])
def upload_resume():
    # Handle resume upload and analysis
    if 'resume' not in request.files:
        return jsonify({'success': False, 'message': 'No resume file uploaded'})
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    # Mock resume analysis - in real app, use NLP to extract skills
    mock_skills = ['Python', 'Machine Learning', 'Data Analysis', 'Web Development']
    mock_projects = ['E-commerce Website', 'Data Visualization Dashboard', 'ML Classification Model']
    
    # Generate interview questions based on resume
    questions = [
        "Tell me about yourself and your background.",
        f"I see you have experience with {mock_skills[0]}. Can you tell me about a project where you used it?",
        f"How did you implement {mock_projects[0]}? What challenges did you face?",
        f"Explain your experience with {mock_skills[1]}. What algorithms have you worked with?",
        f"Tell me about {mock_projects[1]}. What technologies did you use?",
        f"How would you approach a new {mock_skills[2]} project?",
        f"What was the most challenging aspect of {mock_projects[2]}?",
        f"How do you stay updated with {mock_skills[3]} trends?",
        "Where do you see yourself in the next 5 years?",
        "What are your strengths and areas for improvement?",
        "Why should we hire you for this position?"
    ]
    
    return jsonify({
        'success': True,
        'questions': questions,
        'extracted_skills': mock_skills,
        'extracted_projects': mock_projects
    })

@app.route('/student/games')
def games():
    return render_template('games.html')

@app.route('/student/submit_interview', methods=['POST'])
def submit_interview():
    data = request.get_json()
    subject_id = data.get('subject_id')
    answers = data.get('answers')
    
    # Simple scoring based on answer length and keywords
    total_score = 0
    feedback = []
    
    for i, answer in enumerate(answers):
        score = 0
        if len(answer.strip()) > 50:
            score += 3
        elif len(answer.strip()) > 20:
            score += 2
        else:
            score += 1
        
        # Check for technical keywords (basic keyword matching)
        keywords = ['python', 'javascript', 'java', 'programming', 'code', 'development', 'algorithm', 'data', 'function']
        keyword_count = sum(1 for keyword in keywords if keyword.lower() in answer.lower())
        score += min(keyword_count, 2)
        
        total_score += score
        
        if score < 3:
            feedback.append(f"Question {i+1}: Consider providing more detailed and technical answers.")
        elif score < 5:
            feedback.append(f"Question {i+1}: Good answer, but could include more technical details.")
        else:
            feedback.append(f"Question {i+1}: Excellent answer with good technical content.")
    
    # Save interview result to database
    try:
        # Get first student for demo mode (since no login system)
        student = User.query.filter_by(user_type='student').first()
        if student:
            interview_result = InterviewResult(
                student_id=student.id,
                subject_id=subject_id,
                questions_answers=json.dumps([{'question': f'Question {i+1}', 'answer': answer} for i, answer in enumerate(answers)]),
                score=total_score,
                feedback='\n'.join(feedback)
            )
            db.session.add(interview_result)
            db.session.commit()
            print(f"✅ Interview result saved: Student {student.username}, Subject {subject_id}, Score {total_score}")
        else:
            print("⚠️ No student found to save interview result")
    except Exception as e:
        print(f"❌ Error saving interview result: {e}")
    
    return jsonify({
        'success': True,
        'score': total_score,
        'max_score': len(answers) * 5,
        'feedback': feedback,
        'passed': total_score >= (len(answers) * 3)
    })

@app.route('/api/comedy_content')
def get_comedy_content():
    return jsonify({'content': random.choice(COMEDY_CONTENT)})

@app.route('/api/engagement_check', methods=['POST'])
def engagement_check():
    
    data = request.get_json()
    activity_type = data.get('activity_type')
    duration = data.get('duration')
    inactivity_periods = data.get('inactivity_periods', 0)
    
    # Mock engagement tracking (no login system)
    print(f"Engagement tracked: {activity_type}, duration: {duration}, inactivity: {inactivity_periods}")
    
    # Suggest break if too many inactivity periods
    suggest_break = inactivity_periods > 3
    
    return jsonify({
        'success': True,
        'suggest_break': suggest_break,
        'message': 'Are you bored? Want to take a short game break or continue?' if suggest_break else None
    })

# Remove duplicate database initialization function

def init_database():
    """Initialize database with tables and sample data"""
    db.create_all()
    
    # Create sample users if they don't exist
    if not User.query.filter_by(username='teacher1').first():
        teacher = User(
            username='teacher1',
            email='teacher@example.com',
            password_hash=generate_password_hash('teacher123'),
            user_type='teacher'
        )
        db.session.add(teacher)
        db.session.commit()
        
        # Add sample subjects
        subjects = [
            Subject(name='Python', description='Learn Python programming', teacher_id=teacher.id),
            Subject(name='JavaScript', description='Learn JavaScript programming', teacher_id=teacher.id),
            Subject(name='Java', description='Learn Java programming', teacher_id=teacher.id)
        ]
        
        for subject in subjects:
            db.session.add(subject)
        
        db.session.commit()
        print("✓ Sample teacher and subjects created")
    
    # Create multiple student accounts
    student_accounts = [
        {'username': 'student1', 'email': 'student1@example.com', 'password': 'student123'},
        {'username': 'student2', 'email': 'student2@example.com', 'password': 'student123'},
        {'username': 'student3', 'email': 'student3@example.com', 'password': 'student123'},
        {'username': 'student4', 'email': 'student4@example.com', 'password': 'student123'},
        {'username': 'student5', 'email': 'student5@example.com', 'password': 'student123'}
    ]
    
    for account in student_accounts:
        if not User.query.filter_by(username=account['username']).first():
            student = User(
                username=account['username'],
                email=account['email'],
                password_hash=generate_password_hash(account['password']),
                user_type='student'
            )
            db.session.add(student)
    
    db.session.commit()
    print("✓ Sample students created")
    
    print("✓ Database initialized successfully")

if __name__ == '__main__':
    with app.app_context():
        try:
            init_database()
            print("\n🚀 Starting AI-Powered Smart Learning Platform...")
            print("📖 Demo Credentials:")
            print("   Teacher - Username: teacher1, Password: teacher123")
            print("   Student - Username: student1, Password: student123")
            print("\n🌐 Access the application at: http://localhost:5000")
            print("\n" + "="*60)
            
            app.run(debug=True, host='0.0.0.0', port=5000)
        except Exception as e:
            print(f"❌ Error starting application: {e}")
            print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
