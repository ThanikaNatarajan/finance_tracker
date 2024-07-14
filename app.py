import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Initialize connection to the database
conn = sqlite3.connect('finance_tracker.db', check_same_thread=False)
conn.execute('''CREATE TABLE IF NOT EXISTS transactions
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 date TEXT, category TEXT, amount REAL, description TEXT)''')
conn.execute('''CREATE TABLE IF NOT EXISTS categories
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT UNIQUE)''')
conn.commit()

def add_transaction(date, category, amount, description):
    conn.execute("INSERT INTO transactions (date, category, amount, description) VALUES (?, ?, ?, ?)",
                 (date, category, amount, description))
    conn.commit()

def get_all_transactions():
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    df['date'] = pd.to_datetime(df['date'])
    return df

def delete_transaction(transaction_id):
    conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()

def update_transaction(transaction_id, date, category, amount, description):
    conn.execute("UPDATE transactions SET date = ?, category = ?, amount = ?, description = ? WHERE id = ?",
                 (date.strftime('%Y-%m-%d'), category, amount, description, transaction_id))
    conn.commit()

def get_statistics():
    transactions = get_all_transactions()
    if not transactions.empty:
        total_income = transactions[transactions['category'] == 'Income']['amount'].sum()
        total_expenses = transactions[transactions['category'] != 'Income']['amount'].sum()
        balance = total_income - total_expenses
        return total_income, total_expenses, balance
    return 0, 0, 0

def get_categories():
    return pd.read_sql_query("SELECT * FROM categories", conn)

def add_category(name):
    conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    conn.commit()

def update_category(category_id, new_name):
    conn.execute("UPDATE categories SET name = ? WHERE id = ?", (new_name, category_id))
    conn.commit()

def delete_category(category_id):
    conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()

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
if st.sidebar.button("Categories"):
    change_page("Categories")

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
    categories = get_categories()['name'].tolist()
    category = st.selectbox('Category', categories)
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
        
        # Use st.data_editor to create an editable table
        edited_df = st.data_editor(
            transactions,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "date": st.column_config.DateColumn("Date"),
                "category": st.column_config.SelectboxColumn("Category", options=categories),
                "amount": st.column_config.NumberColumn("Amount", format="$%.2f", min_value=0.01, step=0.01),
                "description": st.column_config.TextColumn("Description"),
                "Delete": st.column_config.CheckboxColumn("Delete")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Check for updates and deletions
        if not edited_df.equals(transactions):
            for index, row in edited_df.iterrows():
                if row['Delete']:
                    delete_transaction(row['id'])
                elif (row['date'] != transactions.loc[index, 'date'] or 
                      row['category'] != transactions.loc[index, 'category'] or 
                      row['amount'] != transactions.loc[index, 'amount'] or 
                      row['description'] != transactions.loc[index, 'description']):
                    update_transaction(row['id'], row['date'], row['category'], row['amount'], row['description'])
            st.success('Transactions updated successfully!')
            st.rerun()
    else:
        st.write('No transactions found.')

elif st.session_state.page == "Categories":
    st.title('Categories')

    # Add category form
    st.subheader('Add New Category')
    new_category = st.text_input('Category Name')
    if st.button('Add Category'):
        add_category(new_category)
        st.success('Category added successfully!')
        st.rerun()

    # Display and edit categories
    st.subheader('All Categories')
    categories = get_categories()
    if not categories.empty:
        edited_df = st.data_editor(
            categories,
            column_config={
                "id": st.column_config.NumberColumn("ID"),
                "name": st.column_config.TextColumn("Category Name"),
            },
            disabled=["id"],
            hide_index=True,
            use_container_width=True
        )
        
        # Check for updates
        if not edited_df.equals(categories):
            for index, row in edited_df.iterrows():
                if row['name'] != categories.loc[index, 'name']:
                    update_category(row['id'], row['name'])
            st.success('Categories updated successfully!')
            st.rerun()

        # Delete categories
        category_to_delete = st.selectbox('Select category to delete', categories['name'].tolist())
        if st.button('Delete Category'):
            category_id = categories[categories['name'] == category_to_delete]['id'].values[0]
            delete_category(category_id)
            st.success(f"Deleted category: {category_to_delete}")
            st.rerun()
    else:
        st.write('No categories found.')