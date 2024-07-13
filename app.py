import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Connect to the SQLite database
conn = sqlite3.connect('finance_tracker.db')
c = conn.cursor()

# Create table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS transactions
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              date TEXT,
              category TEXT,
              amount REAL,
              description TEXT)''')
conn.commit()

def add_transaction(date, category, amount, description):
    c.execute("INSERT INTO transactions (date, category, amount, description) VALUES (?, ?, ?, ?)",
              (date, category, amount, description))
    conn.commit()

def get_all_transactions():
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    return df

st.title('Finance Tracker')

# Add transaction form
st.header('Add New Transaction')
date = st.date_input('Date', datetime.now())
category = st.selectbox('Category', ['Income', 'Housing', 'Food', 'Transportation', 'Utilities', 'Entertainment', 'Other'])
amount = st.number_input('Amount', min_value=0.01, format='%0.2f')
description = st.text_input('Description')

if st.button('Add Transaction'):
    add_transaction(date.strftime('%Y-%m-%d'), category, amount, description)
    st.success('Transaction added successfully!')

# Display all transactions
st.header('All Transactions')
transactions = get_all_transactions()
st.dataframe(transactions)

# Display total balance
total_income = transactions[transactions['category'] == 'Income']['amount'].sum()
total_expenses = transactions[transactions['category'] != 'Income']['amount'].sum()
balance = total_income - total_expenses
st.header('Balance')
st.write(f'Total Income: ${total_income:.2f}')
st.write(f'Total Expenses: ${total_expenses:.2f}')
st.write(f'Current Balance: ${balance:.2f}')

# Close the database connection
conn.close()