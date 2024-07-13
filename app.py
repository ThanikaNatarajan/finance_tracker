import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

conn = sqlite3.connect('finance_tracker.db', check_same_thread=False)
conn.execute('''CREATE TABLE IF NOT EXISTS transactions
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 date TEXT, category TEXT, amount REAL, description TEXT)''')
conn.commit()

def add_transaction(date, category, amount, description):
    conn.execute("INSERT INTO transactions (date, category, amount, description) VALUES (?, ?, ?, ?)",
                 (date, category, amount, description))
    conn.commit()

def get_all_transactions():
    return pd.read_sql_query("SELECT * FROM transactions", conn)

def delete_transaction(transaction_id):
    conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()

st.title('Finance Tracker')

st.header('Add New Transaction')
date = st.date_input('Date', datetime.now())
category = st.selectbox('Category', ['Income', 'Housing', 'Food', 'Transportation', 'Utilities', 'Entertainment', 'Other'])
amount = st.number_input('Amount', min_value=0.01, format='%0.2f')
description = st.text_input('Description')

if st.button('Add Transaction'):
    add_transaction(date.strftime('%Y-%m-%d'), category, amount, description)
    st.success('Transaction added successfully!')
    st.rerun()

st.header('All Transactions')
transactions = get_all_transactions()
if not transactions.empty:
    # Add a "Delete" column to the DataFrame
    transactions['Delete'] = False
    
    # Use st.data_editor to create an editable table with delete buttons
    edited_df = st.data_editor(
        transactions,
        column_config={
            "id": st.column_config.NumberColumn("ID"),
            "date": st.column_config.DateColumn("Date"),
            "category": st.column_config.TextColumn("Category"),
            "amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
            "description": st.column_config.TextColumn("Description"),
            "Delete": st.column_config.CheckboxColumn("Delete")
        },
        disabled=["id", "date", "category", "amount", "description"],
        hide_index=True,
        use_container_width=True
    )
    
    # Check if any rows are marked for deletion
    rows_to_delete = edited_df[edited_df['Delete']]['id'].tolist()
    if rows_to_delete:
        for row_id in rows_to_delete:
            delete_transaction(row_id)
        st.success(f"Deleted {len(rows_to_delete)} transaction(s)")
        st.rerun()
else:
    st.write('No transactions found.')

if not transactions.empty:
    total_income = transactions[transactions['category'] == 'Income']['amount'].sum()
    total_expenses = transactions[transactions['category'] != 'Income']['amount'].sum()
    balance = total_income - total_expenses
    st.header('Balance')
    st.write(f'Total Income: ${total_income:.2f}')
    st.write(f'Total Expenses: ${total_expenses:.2f}')
    st.write(f'Current Balance: ${balance:.2f}')
else:
    st.write('No transactions to calculate balance.')