import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import joblib

def train_model():
    # Load dataset
    data = pd.read_csv('student_data.csv')

    # Features and target
    X = data[['hours_studied', 'attendance_percentage', 'previous_score']]
    y = data['final_score']

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Save model
    joblib.dump(model, 'student_score_model.joblib')

    print('Model trained and saved successfully!')

if __name__ == '__main__':
    train_model()
