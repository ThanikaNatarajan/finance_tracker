import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Initialize connection to the database
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

def get_statistics():
    transactions = get_all_transactions()
    if not transactions.empty:
        total_income = transactions[transactions['category'] == 'Income']['amount'].sum()
        total_expenses = transactions[transactions['category'] != 'Income']['amount'].sum()
        balance = total_income - total_expenses
        return total_income, total_expenses, balance
    return 0, 0, 0

st.set_page_config(page_title="Finance Tracker", layout="wide")

# Initialize session state for navigation
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

# Function to change page
def change_page(page):
    st.session_state.page = page

# Sidebar for navigation
st.sidebar.title("Navigation")
if st.sidebar.button("Dashboard"):
    change_page("Dashboard")
if st.sidebar.button("Transactions"):
    change_page("Transactions")

if st.session_state.page == "Dashboard":
    st.title('Finance Dashboard')

    # Get statistics
    total_income, total_expenses, balance = get_statistics()

    # Display statistics in box-like components
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Income", value=f"${total_income:.2f}", delta="Income")
    with col2:
        st.metric(label="Total Expenses", value=f"${total_expenses:.2f}", delta="Expenses")
    with col3:
        st.metric(label="Current Balance", value=f"${balance:.2f}", delta="Balance")

    # Add Transaction button
    if st.button('Add New Transaction'):
        change_page("Transactions")
        st.rerun()

    # Display recent transactions
    st.subheader("Recent Transactions")
    transactions = get_all_transactions().tail(5)  # Get last 5 transactions
    if not transactions.empty:
        st.dataframe(transactions[['date', 'category', 'amount', 'description']], use_container_width=True)
    else:
        st.write("No transactions found.")

elif st.session_state.page == "Transactions":
    st.title('Transactions')

    # Add transaction form
    st.subheader('Add New Transaction')
    date = st.date_input('Date', datetime.now())
    category = st.selectbox('Category', ['Income', 'Housing', 'Food', 'Transportation', 'Utilities', 'Entertainment', 'Other'])
    amount = st.number_input('Amount', min_value=0.01, format='%0.2f')
    description = st.text_input('Description')

    if st.button('Add Transaction'):
        add_transaction(date.strftime('%Y-%m-%d'), category, amount, description)
        st.success('Transaction added successfully!')
        st.rerun()

    # Display all transactions
    st.subheader('All Transactions')
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