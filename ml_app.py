from flask import Flask, render_template, request
import joblib
import numpy as np

app = Flask(__name__)

# Load the trained model
model = joblib.load('student_score_model.joblib')

@app.route('/')
def home():
    return render_template('form.html')

@app.route('/predict', methods=['POST'])
def predict():
    # Get form data
    hours_studied = float(request.form['hours_studied'])
    attendance_percentage = float(request.form['attendance_percentage'])
    previous_score = float(request.form['previous_score'])
    
    # Make prediction
    features = np.array([[hours_studied, attendance_percentage, previous_score]])
    predicted_score = model.predict(features)[0]
    
    # Round to 2 decimal places
    predicted_score = round(predicted_score, 2)
    
    return render_template('result.html', 
                         predicted_score=predicted_score,
                         hours_studied=hours_studied,
                         attendance_percentage=attendance_percentage,
                         previous_score=previous_score)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
