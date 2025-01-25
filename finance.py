#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
from PyPDF2 import PdfReader
import google.generativeai as genai
import re
import time
import json
from datetime import datetime

# Configure Gemini
genai.configure(api_key="AIzaSyA-9-lTQTWdNM43YdOXMQwGKDy0SrMwo6c")
model = genai.GenerativeModel('gemini-pro')

class FinanceAgent:
    def __init__(self):
        self.financial_terms = {
            'income_statement': ['revenue', 'gross profit', 'operating income', 'net income'],
            'balance_sheet': ['assets', 'liabilities', 'equity', 'debt'],
            'cash_flow': ['operating cash flow', 'investing cash flow', 'financing cash flow']
        }
        
    def analyze_with_gemini(self, text, prompt, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt + text)
                return response.text
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return f"API Error: {str(e)}"
        return "System busy - please try later"

    def process_financial_doc(self, uploaded_file):
        if uploaded_file.name.endswith('.pdf'):
            reader = PdfReader(uploaded_file)
            text = '\n'.join([page.extract_text() for page in reader.pages])
            return self._analyze_financial_text(text)
        return "Unsupported file format"

    def _analyze_financial_text(self, text):
        # Extract structured data
        findings = {}
        for category, terms in self.financial_terms.items():
            pattern = r'(?i)({}):?\s*(\$?[\d,\.]+)'.format('|'.join(terms))
            matches = re.findall(pattern, text)
            if matches:
                findings[category] = {match[0].lower(): self._clean_currency(match[1]) for match in matches}
        
        # Get AI analysis
        analysis_prompt = """Analyze this financial document:
        1. Identify key financial trends
        2. Highlight potential risks
        3. Calculate important ratios (ROE, ROI, Debt/Equity)
        4. Provide investment recommendations
        """
        analysis = self.analyze_with_gemini(analysis_prompt, text)
        
        return {
            "structured_data": findings,
            "ai_analysis": analysis
        }

    def stock_analyzer(self, ticker):
        prompt = f"""Analyze {ticker} stock:
        {{
            "current_analysis": {{
                "valuation": "",
                "technical_analysis": "",
                "fundamentals": ""
            }},
            "predictions": {{
                "1_week": "",
                "1_month": "",
                "1_year": ""
            }},
            "recommendation": ""
        }}"""
        try:
            response = self.analyze_with_gemini("", prompt)
            return json.loads(response.replace("```json", "").replace("```", ""))
        except:
            return {"error": "Failed to analyze stock"}

    def expense_tracker(self, receipt_text):
        prompt = f"""Analyze expense receipt:
        {{
            "vendor": "",
            "date": "YYYY-MM-DD",
            "amount": 0.00,
            "category": "",
            "tax_details": {{
                "gst": 0.00,
                "total_tax": 0.00
            }}
        }}
        Text: {receipt_text}"""
        try:
            response = self.analyze_with_gemini("", prompt)
            return json.loads(response.replace("```json", "").replace("```", ""))
        except:
            return {"error": "Failed to process receipt"}

    def _clean_currency(self, value):
        return float(re.sub(r'[^\d.]', '', value))

# Streamlit UI
st.set_page_config(page_title="AI Finance Agent", layout="wide")
st.title("💰 Financial Intelligence Assistant")

tab1, tab2, tab3, tab4 = st.tabs(["Document Analysis", "Stock Insights", "Expense Tracking", "Fraud Detection"])

with tab1:
    st.subheader("Financial Document Analysis")
    uploaded_file = st.file_uploader("Upload PDF (Annual Report, Balance Sheet)", type=['pdf'])
    
    if uploaded_file:
        agent = FinanceAgent()
        with st.spinner('Analyzing document...'):
            try:
                report = agent.process_financial_doc(uploaded_file)
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.subheader("Financial Metrics")
                    st.json(report["structured_data"])
                
                with col2:
                    st.subheader("Expert Analysis")
                    st.markdown(report["ai_analysis"])
                    
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")

with tab2:
    st.subheader("Stock Market Analysis")
    ticker = st.text_input("Enter stock ticker (e.g., AAPL):")
    
    if st.button("Analyze Stock"):
        agent = FinanceAgent()
        with st.spinner('Generating insights...'):
            analysis = agent.stock_analyzer(ticker)
            
            if "error" in analysis:
                st.error(analysis["error"])
            else:
                st.subheader(f"{ticker.upper()} Analysis")
                st.markdown("**Current Valuation**")
                st.write(analysis["current_analysis"]["valuation"])
                
                st.markdown("**Predictions**")
                col1, col2, col3 = st.columns(3)
                col1.write("1 Week: " + analysis["predictions"]["1_week"])
                col2.write("1 Month: " + analysis["predictions"]["1_month"])
                col3.write("1 Year: " + analysis["predictions"]["1_year"])
                
                st.markdown("**Recommendation**")
                st.success(analysis["recommendation"])

with tab3:
    st.subheader("Expense Management")
    receipt_text = st.text_area("Paste receipt text or upload PDF:")
    
    if st.button("Process Expense"):
        agent = FinanceAgent()
        with st.spinner('Categorizing expense...'):
            result = agent.expense_tracker(receipt_text)
            
            if "error" in result:
                st.error(result["error"])
            else:
                st.subheader("Expense Breakdown")
                cols = st.columns(4)
                cols[0].metric("Vendor", result["vendor"])
                cols[1].metric("Amount", f"${result['amount']:.2f}")
                cols[2].metric("Category", result["category"])
                cols[3].metric("Date", result["date"])
                
                st.markdown("**Tax Details**")
                st.write(f"GST: ${result['tax_details']['gst']:.2f}")
                st.write(f"Total Tax: ${result['tax_details']['total_tax']:.2f}")

with tab4:
    st.subheader("Transaction Monitoring")
    transaction_data = st.text_area("Enter transaction details:")
    
    if st.button("Check Fraud Risk"):
        agent = FinanceAgent()
        with st.spinner('Analyzing patterns...'):
            prompt = f"""Detect financial fraud risks in:
            {transaction_data}
            Output JSON with:
            {{
                "risk_level": "low/medium/high",
                "suspicious_patterns": [],
                "recommended_actions": []
            }}"""
            try:
                response = agent.analyze_with_gemini(prompt, "")
                result = json.loads(response.replace("```json", "").replace("```", ""))
                
                st.subheader("Risk Assessment")
                risk_color = {"low": "green", "medium": "orange", "high": "red"}.get(result["risk_level"], "gray")
                st.markdown(f"Risk Level: <span style='color:{risk_color}'>**{result['risk_level'].upper()}**</span>", 
                           unsafe_allow_html=True)
                
                st.markdown("**Suspicious Patterns**")
                for pattern in result["suspicious_patterns"]:
                    st.write(f"- {pattern}")
                    
                st.markdown("**Recommended Actions**")
                for action in result["recommended_actions"]:
                    st.write(f"- {action}")
                    
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")

st.divider()
st.caption("Note: This tool provides informational insights only, not financial advice. Always consult a qualified professional.")

