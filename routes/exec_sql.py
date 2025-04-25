from flask import Flask, render_template, request, Blueprint
import sqlite3

exec_sql_bp = Blueprint('exec_sql', __name__)


def query_db(query, params=()):
    conn = sqlite3.connect('instance/hotel.db')
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results


@exec_sql_bp.route('/sql', methods=['GET', 'POST'])
def index():
    data = []
    columns = []
    error = None

    if request.method == 'POST':
        try:
            query = request.form['query']
            results = query_db(query)
            print(query)
            if results:
                conn = sqlite3.connect('instance/hotel.db')
                cursor = conn.cursor()
                cursor.execute(query)
                columns = [description[0] for description in cursor.description]
                conn.close()

                data = results
            else:
                error = "None of data return."

        except sqlite3.Error as e:
            error = f"Error: {str(e)}"

    return render_template('query.html', data=data, columns=columns, error=error)

