# -*- coding: utf-8 -*-
"""Untitled6.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/126FlxsVImJ2_gemk_iNFoWFiesd-JwlT
"""

import streamlit as st

# Custom CSS to adjust layout
st.markdown("""
    <style>
        .reportview-container {
            max-width: 100%;
        }
        .sidebar .sidebar-content {
            background-color: #f0f2f6;
        }
    </style>
""", unsafe_allow_html=True)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from math import sqrt
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor
import shap
import warnings
warnings.filterwarnings('ignore')


def check_password():
    """Password authentication"""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    return True

def main():
    """Main application logic"""
    st.title("Coal-Fired Power Plant Performance Predictor")

    # Dark mode toggle
    dark_mode = st.sidebar.checkbox("Dark Mode")
    if dark_mode:
        st.markdown("""
        <style>
            .reportview-container {background: #0e1117; color: white;}
            .stMetric {color: black !important;}
        </style>
        """, unsafe_allow_html=True)

    # File upload section
    st.header("📁 Data Upload")
    uploaded_file = st.file_uploader("Upload dataset (CSV)", type="csv")
    validation_file = st.file_uploader("Upload validation data (CSV)", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file, header=1)
        features = ['CFR', 'TAF', 'MSP', 'MST', 'MSF', 'FWT', 'RHT', 'CV', 'Power']

        # Data exploration
        st.header("🔍 Data Exploration")

        # KDE Plot
        st.subheader("Feature Distribution")
        df_normalized = (df[features] - df[features].min()) / (df[features].max() - df[features].min())
        fig, ax = plt.subplots(figsize=(5, 3.65))
        for feature in features:
            sns.kdeplot(df_normalized[feature], ax=ax, label=feature)
        plt.legend(bbox_to_anchor=(0.5, 1.55), ncol=4, loc='upper center')
        st.pyplot(fig)

        # Correlation matrix
        st.subheader("Correlation Heatmap")
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(df.corr(), annot=True, cmap="viridis", ax=ax)
        st.pyplot(fig)

        # Model selection
        st.header("🎯 Model Configuration")
        model_type = st.radio("Prediction Target:", ("Thermal Efficiency (TE)", "Heat Rate (THR)"))

        # Model parameters
        params = {
            'TE': {'eta':0.1, 'gamma':0.3, 'reg_lambda':0.8, 'max_depth':6, 'n_estimators':500},
            'THR': {'eta':0.05, 'gamma':0.2, 'reg_lambda':1.0, 'max_depth':5, 'n_estimators':700}
        }

        # Model training
        target = 'TE' if model_type.startswith('Thermal') else 'THR'
        X = df.drop(columns=['TE', 'THR'])
        y = df[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        @st.cache_resource
        def train_model():
            return XGBRegressor(**params[target], verbosity=0).fit(X_train, y_train)

        model = train_model()
        predictions = model.predict(X_test)

        # Metrics
        st.header("📈 Model Performance")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Training R²", f"{r2_score(y_train, model.predict(X_train)):.3f}")
            st.metric("Training RMSE", f"{sqrt(mean_squared_error(y_train, model.predict(X_train))):.2f}")
        with col2:
            st.metric("Test R²", f"{r2_score(y_test, predictions):.3f}")
            st.metric("Test RMSE", f"{sqrt(mean_squared_error(y_test, predictions)):.2f}")

        # SHAP analysis
        st.header("📊 Feature Contributions")
        explainer = shap.Explainer(model)
        shap_values = explainer(X)
        fig, ax = plt.subplots()
        shap.summary_plot(shap_values, X, show=False)
        st.pyplot(fig)

        # Mathematical model
        st.header("🧮 Linear Regression Comparison")
        lr_model = LinearRegression().fit(X_train, y_train)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Linear Train R²", f"{r2_score(y_train, lr_model.predict(X_train)):.3f}")
        with col2:
            st.metric("Linear Test R²", f"{r2_score(y_test, lr_model.predict(X_test)):.3f}")

        # Validation
        if validation_file:
            st.header("🔬 Validation Results")
            val_df = pd.read_csv(validation_file, header=1)
            val_pred = model.predict(val_df.drop(columns=['TE', 'THR']))
            results = pd.DataFrame({
                'Actual': val_df[target],
                'Predicted': val_pred,
                'Error': abs(val_df[target] - val_pred)
            })
            st.dataframe(results.style.format("{:.2f}"), height=300)

        # Prediction interface
        st.header("🎛️ Make Predictions")
        input_data = {}
        cols = st.columns(3)
        for i, feature in enumerate(features):
            with cols[i%3]:
                input_data[feature] = st.number_input(feature, value=float(df[feature].mean()))

        if st.button("Predict"):
            prediction = model.predict(pd.DataFrame([input_data]))
            st.success(f"Predicted {target}: {prediction[0]:.2f}")

if __name__ == "__main__":
    if check_password():
        main()