from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import requests
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24)) 
# Number of records per page
RECORDS_PER_PAGE = 100

@app.route('/', methods=['GET', 'POST'])
def index():
    page = int(request.args.get('page', 1))
    
    if request.method == 'POST':
        base_url = request.form['base_url']
        partition = request.form['partition']
        username = request.form['username']
        password = request.form['password']
        
        # Store login data in session
        session['logged_in'] = True
        session['base_url'] = base_url
        session['partition'] = partition
        session['username'] = username
        session['password'] = password

        return redirect(url_for('index', page=1))

    if not session.get('logged_in'):
        return render_template('form.html')

    base_url = session.get('base_url')
    partition = session.get('partition')
    username = session.get('username')
    password = session.get('password')
    
    if not (base_url and partition and username and password):
        return render_template('form.html')

    un = partition + "/" + username
    url = f"https://{base_url}/pricefx/{partition}/productmanager.fetchformulafilteredproducts"
    payload = {
        "operationType": "fetch",
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers, auth=(un, password))
        response.raise_for_status()
        response_json = response.json()
        data_list = response_json.get('response', {}).get('data', [])

        total_records = len(data_list)
        start_index = (page - 1) * RECORDS_PER_PAGE
        end_index = start_index + RECORDS_PER_PAGE
        paginated_data = data_list[start_index:end_index]

        df = pd.DataFrame(paginated_data)
        html_table = df.to_html(index=False)
        
        total_pages = (total_records + RECORDS_PER_PAGE - 1) // RECORDS_PER_PAGE
        prev_page = page - 1 if page > 1 else None
        next_page = page + 1 if page < total_pages else None

        return render_template('results.html', table=html_table, prev_page=prev_page, next_page=next_page, page=page)
    except Exception as e:
        return str(e)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
