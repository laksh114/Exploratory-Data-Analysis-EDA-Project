import os
import pandas as pd
import numpy as np

def seed_all_datasets(target_dir):
    """
    Generate synthetic sample datasets resembling standard benchmark datasets
    and write them as CSV files to target_dir.
    """
    os.makedirs(target_dir, exist_ok=True)
    
    # 1. Titanic Sample
    titanic_path = os.path.join(target_dir, 'titanic.csv')
    if not os.path.exists(titanic_path):
        np.random.seed(42)
        n = 200
        titanic = pd.DataFrame({
            'PassengerId': range(1, n + 1),
            'Survived': np.random.choice([0, 1], size=n, p=[0.6, 0.4]),
            'Pclass': np.random.choice([1, 2, 3], size=n, p=[0.25, 0.25, 0.5]),
            'Name': [f"Passenger, Name {i}" for i in range(1, n + 1)],
            'Sex': np.random.choice(['male', 'female'], size=n, p=[0.6, 0.4]),
            'Age': np.random.choice([np.nan, 22.0, 38.0, 26.0, 35.0, 54.0, 2.0, 27.0, 14.0, 4.0], size=n),
            'SibSp': np.random.choice([0, 1, 2, 3], size=n, p=[0.7, 0.2, 0.05, 0.05]),
            'Parch': np.random.choice([0, 1, 2], size=n, p=[0.8, 0.1, 0.1]),
            'Ticket': [f"A/5 {np.random.randint(1000, 9999)}" for _ in range(n)],
            'Fare': np.round(np.random.exponential(scale=32.0, size=n) + 7.5, 2),
            'Cabin': np.random.choice([np.nan, 'C85', 'C123', 'E46', 'G6'], size=n, p=[0.7, 0.1, 0.05, 0.05, 0.1]),
            'Embarked': np.random.choice(['S', 'C', 'Q', np.nan], size=n, p=[0.7, 0.2, 0.08, 0.02])
        })
        # Introduce some missing ages/embarked
        titanic.to_csv(titanic_path, index=False)
        print("Generated titanic.csv")

    # 2. Student Performance Sample
    student_path = os.path.join(target_dir, 'student_performance.csv')
    if not os.path.exists(student_path):
        np.random.seed(42)
        n = 150
        students = pd.DataFrame({
            'StudentID': range(1001, 1001 + n),
            'Gender': np.random.choice(['Male', 'Female'], size=n),
            'Race_Ethnicity': np.random.choice(['Group A', 'Group B', 'Group C', 'Group D'], size=n),
            'Parental_Education': np.random.choice(["Bachelor's Degree", "Some College", "High School", "Master's Degree"], size=n),
            'Lunch': np.random.choice(['Standard', 'Free/Reduced'], size=n, p=[0.6, 0.4]),
            'Test_Preparation': np.random.choice(['None', 'Completed'], size=n, p=[0.7, 0.3]),
            'Math_Score': np.clip(np.random.normal(loc=66, scale=15, size=n).astype(int), 0, 100),
            'Reading_Score': np.clip(np.random.normal(loc=69, scale=14, size=n).astype(int), 0, 100),
            'Writing_Score': np.clip(np.random.normal(loc=68, scale=15, size=n).astype(int), 0, 100)
        })
        students.to_csv(student_path, index=False)
        print("Generated student_performance.csv")

    # 3. Customer Churn Sample
    churn_path = os.path.join(target_dir, 'customer_churn.csv')
    if not os.path.exists(churn_path):
        np.random.seed(42)
        n = 250
        churn = pd.DataFrame({
            'CustomerID': [f"CUST-{i:04d}" for i in range(1, n + 1)],
            'Gender': np.random.choice(['Male', 'Female'], size=n),
            'SeniorCitizen': np.random.choice([0, 1], size=n, p=[0.85, 0.15]),
            'Partner': np.random.choice(['Yes', 'No'], size=n),
            'Dependents': np.random.choice(['Yes', 'No'], size=n, p=[0.3, 0.7]),
            'Tenure_Months': np.random.randint(1, 72, size=n),
            'PhoneService': np.random.choice(['Yes', 'No'], size=n, p=[0.9, 0.1]),
            'MultipleLines': np.random.choice(['Yes', 'No', 'No phone service'], size=n, p=[0.4, 0.5, 0.1]),
            'InternetService': np.random.choice(['DSL', 'Fiber optic', 'No'], size=n, p=[0.3, 0.5, 0.2]),
            'Contract': np.random.choice(['Month-to-month', 'One year', 'Two year'], size=n, p=[0.5, 0.25, 0.25]),
            'PaperlessBilling': np.random.choice(['Yes', 'No'], size=n),
            'PaymentMethod': np.random.choice(['Electronic check', 'Mailed check', 'Bank transfer', 'Credit card'], size=n),
            'MonthlyCharges': np.round(np.random.normal(loc=64, scale=30, size=n) + 15, 2),
            'TotalCharges': np.nan, # Will compute below
            'Churn': np.random.choice(['Yes', 'No'], size=n, p=[0.27, 0.73])
        })
        # Calculate TotalCharges based on monthly charges and tenure
        churn['TotalCharges'] = np.round(churn['MonthlyCharges'] * churn['Tenure_Months'], 2)
        # Introduce a few missing TotalCharges
        churn.loc[np.random.choice(churn.index, 5, replace=False), 'TotalCharges'] = np.nan
        churn.to_csv(churn_path, index=False)
        print("Generated customer_churn.csv")

    # 4. Heart Disease Sample
    heart_path = os.path.join(target_dir, 'heart_disease.csv')
    if not os.path.exists(heart_path):
        np.random.seed(42)
        n = 180
        heart = pd.DataFrame({
            'Age': np.random.randint(29, 78, size=n),
            'Sex': np.random.choice([1, 0], size=n, p=[0.67, 0.33]), # 1=Male, 0=Female
            'ChestPainType': np.random.choice(['Typical Angina', 'Atypical Angina', 'Non-anginal Pain', 'Asymptomatic'], size=n),
            'RestingBP': np.random.randint(94, 200, size=n),
            'Cholesterol': np.random.randint(126, 410, size=n),
            'FastingBS': np.random.choice([0, 1], size=n, p=[0.85, 0.15]),
            'RestingECG': np.random.choice(['Normal', 'ST-T Wave Anomaly', 'Left Ventricular Hypertrophy'], size=n),
            'MaxHR': np.random.randint(71, 202, size=n),
            'ExerciseAngina': np.random.choice(['Yes', 'No'], size=n, p=[0.33, 0.67]),
            'Oldpeak': np.round(np.random.uniform(0.0, 6.2, size=n), 1),
            'ST_Slope': np.random.choice(['Upsloping', 'Flat', 'Downsloping'], size=n),
            'Target': np.random.choice([0, 1], size=n, p=[0.46, 0.54]) # 1=Heart Disease, 0=Normal
        })
        heart.to_csv(heart_path, index=False)
        print("Generated heart_disease.csv")
        
    # 5. House Prices Sample
    house_path = os.path.join(target_dir, 'house_prices.csv')
    if not os.path.exists(house_path):
        np.random.seed(42)
        n = 150
        sizes = np.random.randint(800, 4500, size=n)
        bedrooms = np.random.choice([1, 2, 3, 4, 5], size=n, p=[0.1, 0.3, 0.4, 0.15, 0.05])
        bathrooms = np.random.choice([1.0, 1.5, 2.0, 2.5, 3.0, 4.0], size=n)
        age = np.random.randint(0, 100, size=n)
        prices = sizes * 150 + bedrooms * 20000 + bathrooms * 15000 - age * 800 + np.random.normal(0, 25000, size=n)
        
        houses = pd.DataFrame({
            'HouseID': range(1, n + 1),
            'SquareFootage': sizes,
            'Bedrooms': bedrooms,
            'Bathrooms': bathrooms,
            'YearBuilt': 2026 - age,
            'GarageCars': np.random.choice([0, 1, 2, 3], size=n, p=[0.1, 0.4, 0.4, 0.1]),
            'Neighborhood': np.random.choice(['Suburbs', 'Urban', 'Rural', 'Downtown'], size=n),
            'Price': np.round(np.clip(prices, 50000, None), 2)
        })
        houses.to_csv(house_path, index=False)
        print("Generated house_prices.csv")

if __name__ == '__main__':
    seed_all_datasets('./dataset')
