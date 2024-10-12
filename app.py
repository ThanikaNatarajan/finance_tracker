import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import hashlib

# Initialize connection to the database
conn = sqlite3.connect('finance_tracker.db', check_same_thread=False)

# Create necessary tables before attempting to migrate
conn.execute('''CREATE TABLE IF NOT EXISTS transactions
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 date TEXT, category TEXT, amount REAL, description TEXT, type TEXT)''')
conn.execute('''CREATE TABLE IF NOT EXISTS categories
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT UNIQUE)''')
conn.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE, password TEXT)''')
conn.commit()

# Database migration and initialization
def migrate_database():
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS income")
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'type' not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN type TEXT")
    cursor.execute('''CREATE TABLE IF NOT EXISTS goals
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT,
                       target_amount REAL,
                       current_amount REAL,
                       deadline TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS scheduled_transactions
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       date TEXT,
                       category TEXT,
                       amount REAL,
                       description TEXT,
                       type TEXT,
                       frequency TEXT)''')
    conn.commit()

migrate_database()

# Hash password function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# CRUD functions for users
def add_user(username, password):
    hashed_password = hash_password(password)
    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()

def validate_user(username, password):
    hashed_password = hash_password(password)
    user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password)).fetchone()
    return user is not None

# Login page
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if validate_user(username, password):
            st.session_state.logged_in = True
            st.success("Logged in successfully!")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")
    if st.button("Register"):
        if username and password:
            try:
                add_user(username, password)
                st.success("User registered successfully!")
            except sqlite3.IntegrityError:
                st.error("Username already exists")
        else:
            st.error("Please enter a username and password")
else:
    # Initialize connection to the database
    conn = sqlite3.connect('finance_tracker.db', check_same_thread=False)

    # CRUD functions for goals
    def add_goal(name, target_amount, deadline):
        conn.execute("INSERT INTO goals (name, target_amount, current_amount, deadline) VALUES (?, ?, ?, ?)",
                     (name, target_amount, 0, deadline.strftime('%Y-%m-%d')))
        conn.commit()

    def get_goals():
        df = pd.read_sql_query("SELECT * FROM goals", conn)
        df['deadline'] = pd.to_datetime(df['deadline'])
        return df

    def update_goal(goal_id, name, target_amount, current_amount, deadline):
        conn.execute("UPDATE goals SET name = ?, target_amount = ?, current_amount = ?, deadline = ? WHERE id = ?",
                     (name, target_amount, current_amount, deadline.strftime('%Y-%m-%d'), goal_id))
        conn.commit()

    def delete_goal(goal_id):
        conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        conn.commit()

    # Function to update goals based on current balance
    def update_goals_with_balance(balance):
        goals = get_goals()
        if goals.empty:
            return
        total_allocated = goals['current_amount'].sum()
        unallocated_balance = max(0, balance - total_allocated)
        if unallocated_balance == 0:
            return
        total_remaining = goals['target_amount'].sum() - goals['current_amount'].sum()
        if total_remaining <= 0:
            return
        for _, goal in goals.iterrows():
            remaining = goal['target_amount'] - goal['current_amount']
            if remaining <= 0:
                continue
            proportion = remaining / total_remaining
            allocation = min(remaining, unallocated_balance * proportion)
            new_current_amount = goal['current_amount'] + allocation
            update_goal(goal['id'], goal['name'], goal['target_amount'], new_current_amount, goal['deadline'])

    # CRUD functions for transactions
    def add_transaction(date, category, amount, description, transaction_type):
        conn.execute("INSERT INTO transactions (date, category, amount, description, type) VALUES (?, ?, ?, ?, ?)",
                     (date, category, amount, description, transaction_type))
        conn.commit()

    def get_all_transactions():
        df = pd.read_sql_query("SELECT * FROM transactions", conn)
        df['date'] = pd.to_datetime(df['date'])
        return df

    def delete_transaction(transaction_id):
        conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()

    def update_transaction(transaction_id, date, category, amount, description, transaction_type):
        conn.execute("UPDATE transactions SET date = ?, category = ?, amount = ?, description = ?, type = ? WHERE id = ?",
                     (date.strftime('%Y-%m-%d'), category, amount, description, transaction_type, transaction_id))
        conn.commit()

    # Function to get statistics
    def get_statistics():
        transactions = get_all_transactions()
        if not transactions.empty:
            income = transactions[transactions['type'] == 'Income']['amount'].sum()
            expenses = transactions[transactions['type'] == 'Expense']['amount'].sum()
            balance = income - expenses
            update_goals_with_balance(balance)
            return income, expenses, balance
        return 0, 0, 0

    # CRUD functions for categories
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

    # Functions for scheduled transactions
    def add_scheduled_transaction(date, category, amount, description, transaction_type, frequency):
        conn.execute("INSERT INTO scheduled_transactions (date, category, amount, description, type, frequency) VALUES (?, ?, ?, ?, ?, ?)",
                     (date, category, amount, description, transaction_type, frequency))
        conn.commit()

    def get_scheduled_transactions():
        return pd.read_sql_query("SELECT * FROM scheduled_transactions", conn)

    def delete_scheduled_transaction(transaction_id):
        conn.execute("DELETE FROM scheduled_transactions WHERE id = ?", (transaction_id,))
        conn.commit()

    def process_scheduled_transactions():
        scheduled = get_scheduled_transactions()
        today = datetime.now().date()
        for _, transaction in scheduled.iterrows():
            transaction_date = datetime.strptime(transaction['date'], '%Y-%m-%d').date()
            if transaction_date <= today:
                add_transaction(transaction['date'], transaction['category'], transaction['amount'],
                                transaction['description'], transaction['type'])
                if transaction['frequency'] == 'One-time':
                    delete_scheduled_transaction(transaction['id'])
                elif transaction['frequency'] == 'Weekly':
                    new_date = (transaction_date + timedelta(days=7)).strftime('%Y-%m-%d')
                elif transaction['frequency'] == 'Monthly':
                    new_date = (transaction_date + timedelta(days=30)).strftime('%Y-%m-%d')
                elif transaction['frequency'] == 'Yearly':
                    new_date = (transaction_date + timedelta(days=365)).strftime('%Y-%m-%d')
                conn.execute("UPDATE scheduled_transactions SET date = ? WHERE id = ?", (new_date, transaction['id']))
        conn.commit()

    # Streamlit app setup
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
    if st.sidebar.button("Goals"):
        change_page("Goals")
    if st.sidebar.button("Scheduled Transactions"):
        change_page("Scheduled Transactions")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.experimental_rerun()

    # Process scheduled transactions
    process_scheduled_transactions()

    # Dashboard
    if st.session_state.page == "Dashboard":
        st.title('Finance Dashboard')

        # Get statistics
        income, expenses, balance = get_statistics()

        # Display statistics in box-like components
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Income", value=f"${income:.2f}")
        with col2:
            st.metric(label="Total Expenses", value=f"${expenses:.2f}")
        with col3:
            st.metric(label="Current Balance", value=f"${balance:.2f}")

        # Add Transaction button
        if st.button('Add New Transaction'):
            change_page("Transactions")
            st.rerun()

        # Display recent transactions
        st.subheader("Recent Transactions")
        transactions = get_all_transactions().tail(5)
        if not transactions.empty:
            st.dataframe(transactions[['date', 'category', 'amount', 'description', 'type']], use_container_width=True)
        else:
            st.write("No transactions found.")

        # Display goals progress
        st.subheader("Financial Goals Progress")
        goals = get_goals()
        if not goals.empty:
            for _, goal in goals.iterrows():
                progress = min(goal['current_amount'] / goal['target_amount'], 1.0)
                st.write(f"{goal['name']}: ${goal['current_amount']:.2f} / ${goal['target_amount']:.2f}")
                st.progress(progress)
        else:
            st.write("No goals set. Add goals in the Goals section.")

        # Data visualization
        st.subheader("Expense Breakdown")
        expenses = get_all_transactions()[get_all_transactions()['type'] == 'Expense']
        if not expenses.empty:
            fig = px.pie(expenses, values='amount', names='category', title='Expense Categories', hole=0.4)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig)

        st.subheader("Income vs Expenses Over Time")
        transactions = get_all_transactions()
        if not transactions.empty:
            transactions['month'] = transactions['date'].dt.to_period('M')
            monthly_summary = transactions.groupby(['month', 'type'])['amount'].sum().unstack()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=monthly_summary.index.astype(str), y=monthly_summary['Income'], mode='lines+markers', name='Income'))
            fig.add_trace(go.Scatter(x=monthly_summary.index.astype(str), y=monthly_summary['Expense'], mode='lines+markers', name='Expense'))
            fig.update_layout(title='Monthly Income vs Expenses', xaxis_title='Month', yaxis_title='Amount', barmode='group')
            st.plotly_chart(fig)

    # Transactions page
    elif st.session_state.page == "Transactions":
        st.title('Transactions')

        # Add transaction form
        st.subheader('Add New Transaction')
        date = st.date_input('Date', datetime.now())
        categories = get_categories()['name'].tolist()
        category = st.selectbox('Category', categories)
        amount = st.number_input('Amount', min_value=0.01, format='%0.2f')
        description = st.text_input('Description')
        transaction_type = st.selectbox('Transaction Type', ['Income', 'Expense'])

        if st.button('Add Transaction'):
            add_transaction(date.strftime('%Y-%m-%d'), category, amount, description, transaction_type)
            st.success('Transaction added successfully!')
            st.rerun()

        # Display all transactions with dynamic search
        st.subheader('All Transactions')
        search_query = st.text_input('Search Transactions')
        transactions = get_all_transactions()
        if search_query:
            transactions = transactions[transactions.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
        if not transactions.empty:
            transactions['Delete'] = False
            edited_df = st.data_editor(
                transactions,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "date": st.column_config.DateColumn("Date"),
                    "category": st.column_config.SelectboxColumn("Category", options=categories),
                    "amount": st.column_config.NumberColumn("Amount", format="$%.2f", min_value=0.01, step=0.01),
                    "description": st.column_config.TextColumn("Description"),
                    "type": st.column_config.SelectboxColumn("Type", options=['Income', 'Expense']),
                    "Delete": st.column_config.CheckboxColumn("Delete")
                },
                hide_index=True,
                use_container_width=True
            )

            if not edited_df.equals(transactions):
                for index, row in edited_df.iterrows():
                    if row['Delete']:
                        delete_transaction(row['id'])
                    elif (row['date'] != transactions.loc[index, 'date'] or
                          row['category'] != transactions.loc[index, 'category'] or
                          row['amount'] != transactions.loc[index, 'amount'] or
                          row['description'] != transactions.loc[index, 'description'] or
                          row['type'] != transactions.loc[index, 'type']):
                        update_transaction(row['id'], row['date'], row['category'], row['amount'], row['description'],
                                           row['type'])
                st.success('Transactions updated successfully!')
                st.rerun()
        else:
            st.write('No transactions found.')

    # Categories page
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
            categories['Delete'] = False  # Add Delete column
            edited_df = st.data_editor(
                categories,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "name": st.column_config.TextColumn("Category Name"),
                    "Delete": st.column_config.CheckboxColumn("Delete"),
                },
                hide_index=True,
                use_container_width=True
            )

            # Handle updates and deletions
            if not edited_df.equals(categories):
                for index, row in edited_df.iterrows():
                    if row['Delete']:
                        delete_category(row['id'])
                    elif row['name'] != categories.loc[index, 'name']:
                        update_category(row['id'], row['name'])
                st.success('Categories updated successfully!')
                st.rerun()
        else:
            st.write('No categories found.')

    elif st.session_state.page == "Goals":
        st.title('Financial Goals')

        # Add goal form
        st.subheader('Add New Goal')
        goal_name = st.text_input('Goal Name')
        target_amount = st.number_input('Target Amount', min_value=0.01, format='%0.2f')
        deadline = st.date_input('Deadline')

        if st.button('Add Goal'):
            add_goal(goal_name, target_amount, deadline)
            st.success('Goal added successfully!')
            st.rerun()

        # Display and edit goals
        st.subheader('All Goals')
        goals = get_goals()
        if not goals.empty:
            goals['Delete'] = False  # Add Delete column
            edited_df = st.data_editor(
                goals,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "name": st.column_config.TextColumn("Goal Name"),
                    "target_amount": st.column_config.NumberColumn("Target Amount", format="$%.2f", min_value=0.01, step=0.01),
                    "current_amount": st.column_config.NumberColumn("Current Amount", format="$%.2f", min_value=0.0, step=0.01),
                    "deadline": st.column_config.DateColumn("Deadline"),
                    "Delete": st.column_config.CheckboxColumn("Delete"),
                },
                hide_index=True,
                use_container_width=True
            )

            # Check for updates and deletions
            if not edited_df.equals(goals):
                for index, row in edited_df.iterrows():
                    if row['Delete']:
                        delete_goal(row['id'])
                    elif (row['name'] != goals.loc[index, 'name'] or
                          row['target_amount'] != goals.loc[index, 'target_amount'] or
                          row['current_amount'] != goals.loc[index, 'current_amount'] or
                          row['deadline'] != goals.loc[index, 'deadline']):
                        update_goal(row['id'], row['name'], row['target_amount'], row['current_amount'], row['deadline'])
                st.success('Goals updated successfully!')
                st.rerun()
        else:
            st.write('No goals found.')

        # Manually update goals with current balance
        if st.button('Update Goals with Current Balance'):
            _, _, balance = get_statistics()  # This will update the goals
            st.success(f'Goals updated with current balance: ${balance:.2f}')
            st.rerun()

    # Scheduled Transactions page
    elif st.session_state.page == "Scheduled Transactions":
        st.title('Scheduled Transactions')

        # Add scheduled transaction form
        st.subheader('Add New Scheduled Transaction')
        date = st.date_input('Start Date', datetime.now())
        categories = get_categories()['name'].tolist()
        category = st.selectbox('Category', categories)
        amount = st.number_input('Amount', min_value=0.01, format='%0.2f')
        description = st.text_input('Description')
        transaction_type = st.selectbox('Transaction Type', ['Income', 'Expense'])
        frequency = st.selectbox('Frequency', ['One-time', 'Weekly', 'Monthly', 'Yearly'])

        if st.button('Add Scheduled Transaction'):
            add_scheduled_transaction(date.strftime('%Y-%m-%d'), category, amount, description, transaction_type, frequency)
            st.success('Scheduled transaction added successfully!')
            st.rerun()

        # Display scheduled transactions
        st.subheader('All Scheduled Transactions')
        scheduled_transactions = get_scheduled_transactions()
        if not scheduled_transactions.empty:
            scheduled_transactions['date'] = pd.to_datetime(scheduled_transactions['date'])  # Convert to datetime
            scheduled_transactions['Delete'] = False
            edited_df = st.data_editor(
                scheduled_transactions,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "date": st.column_config.DateColumn("Next Date"),
                    "category": st.column_config.SelectboxColumn("Category", options=categories),
                    "amount": st.column_config.NumberColumn("Amount", format="$%.2f", min_value=0.01, step=0.01),
                    "description": st.column_config.TextColumn("Description"),
                    "type": st.column_config.SelectboxColumn("Type", options=['Income', 'Expense']),
                    "frequency": st.column_config.SelectboxColumn("Frequency", options=['One-time', 'Weekly', 'Monthly', 'Yearly']),
                    "Delete": st.column_config.CheckboxColumn("Delete")
                },
                hide_index=True,
                use_container_width=True
            )

            # Handle updates and deletions
            if not edited_df.equals(scheduled_transactions):
                for index, row in edited_df.iterrows():
                    if row['Delete']:
                        delete_scheduled_transaction(row['id'])
                    else:
                        # Update the scheduled transaction (you'll need to implement this function)
                        # update_scheduled_transaction(row['id'], row['date'], row['category'], row['amount'], row['description'], row['type'], row['frequency'])
                        pass
                st.success('Scheduled transactions updated successfully!')
                st.rerun()
        else:
            st.write('No scheduled transactions found.')

        # Process scheduled transactions button
        if st.button('Process Scheduled Transactions'):
            process_scheduled_transactions()
            st.success('Scheduled transactions processed successfully!')
            st.rerun()