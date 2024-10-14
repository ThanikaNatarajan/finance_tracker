# Finance Tracker

#### Video Demo: 

#### Description:
Finance Tracker is a comprehensive personal finance management application built with Python and Streamlit. It allows users to track their income and expenses, set and monitor financial goals, manage recurring transactions, and visualize their financial data through an intuitive web interface.

## Features

1. **User Authentication**: Secure login and registration system to protect user data.

2. **Dashboard**: 
   - Overview of total income, expenses, and current balance
   - Recent transactions display
   - Financial goals progress
   - Expense breakdown visualization
   - Income vs Expenses over time chart

3. **Transaction Management**:
   - Add new transactions with date, category, amount, description, and type (Income/Expense)
   - View, edit, and delete existing transactions
   - Search functionality for transactions

4. **Category Management**:
   - Add, edit, and delete transaction categories

5. **Financial Goals**:
   - Set financial goals with target amounts and deadlines
   - Track progress towards goals
   - Automatic allocation of unallocated balance to goals

6. **Scheduled Transactions**:
   - Set up recurring transactions (weekly, monthly, yearly)
   - Automatic processing of scheduled transactions

7. **Data Visualization**:
   - Pie chart for expense breakdown by category
   - Line chart for income vs expenses over time

## Technical Details

### Main Components:

1. **Database**: SQLite database (`finance_tracker.db`) for data storage
2. **Backend**: Python with SQLite for database operations
3. **Frontend**: Streamlit for the web interface
4. **Data Processing**: Pandas for data manipulation
5. **Visualization**: Plotly for interactive charts

### Key Files:

- `finance_tracker.py`: Main application file containing all the logic and Streamlit UI code
- `finance_tracker.db`: SQLite database file

### Libraries Used:

- `streamlit`: For creating the web application
- `sqlite3`: For database operations
- `pandas`: For data manipulation and analysis
- `plotly`: For creating interactive visualizations
- `hashlib`: For password hashing

## How It Works

1. **Database Setup**: The application initializes the SQLite database and creates necessary tables if they don't exist.

2. **User Authentication**: Users can register and log in. Passwords are hashed for security.

3. **Navigation**: The sidebar allows users to navigate between different sections of the app.

4. **Dashboard**: Displays an overview of the user's financial status and visualizations.

5. **Transactions**: Users can add, view, edit, and delete transactions. The data is stored in the SQLite database.

6. **Categories**: Users can manage transaction categories, which are used when adding transactions.

7. **Goals**: Financial goals can be set, tracked, and updated. The system automatically allocates unallocated balance to goals.

8. **Scheduled Transactions**: Users can set up recurring transactions, which are automatically processed based on their frequency.

## Design Choices

1. **Streamlit**: Chosen for its simplicity in creating data apps and its ability to run Python scripts as web applications.

2. **SQLite**: Used for its lightweight nature and ease of setup, making it perfect for a personal finance application.

3. **Plotly**: Selected for creating interactive and visually appealing charts that enhance the user experience.

4. **Single File Structure**: While not ideal for larger applications, keeping all code in a single file simplifies deployment and is sufficient for this project's scope.

5. **Password Hashing**: Implemented to ensure user security, even though it's a local application.

6. **Automatic Goal Updating**: This feature was added to encourage users to allocate their savings towards their financial goals automatically.

## Future Improvements

1. Code Refactoring: Split the application into multiple files for better organization and maintainability.
2. Data Export: Add functionality to export financial data for backup or analysis in other tools.
3. Budget Setting: Implement a budgeting feature to set spending limits for different categories.
4. Mobile Responsiveness: Optimize the UI for better mobile experience.
5. Multi-Currency Support: Add support for tracking finances in multiple currencies.

This Finance Tracker project demonstrates the power of combining Python's data processing capabilities with Streamlit's ability to create interactive web applications quickly. It provides a solid foundation for personal finance management that can be extended and customized further.
