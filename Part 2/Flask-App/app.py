from flask import Flask, render_template, request, redirect, session
from gensim.models.fasttext import FastText
import pandas as pd
import pickle
import os
from bs4 import BeautifulSoup

# generate vector representation for all job documents
def gen_docVecs(wv,tk_txts):
    # creating an empty dataframe
    doc_vec = pd.DataFrame()
    
    # looping through all document content
    for i in range(0,len(tk_txts)):
        tokens = tk_txts[i]

        # A temporary dataframe to store value for 1st doc & for 2nd doc remove the details of 1st & proced through 2nd and so on..)
        temp = pd.DataFrame()

        # looping through each token from a document and spliting with space
        for word_index in range(0, len(tokens)):
            try:
                word = tokens[word_index]
                # if word is present in embeddings then proceed
                word_vec = wv[word]

                # if word is present then adding it to temporary dataframe
                temp = temp.append(pd.Series(word_vec), ignore_index = True)
            except:
                pass
        
        # the sum of each column
        doc_vector = temp.sum()

        # add each document value to the final df
        doc_vec = doc_vec.append(doc_vector, ignore_index = True) 
    return doc_vec

app = Flask(__name__)
app.secret_key = os.urandom(16) 

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/accounting')
def accounting():
    return render_template('accounting.html')

@app.route('/engineering')
def engineering():
    return render_template('engineering.html')

@app.route('/healthcare')
def healthcare():
    return render_template('healthcare.html')

@app.route('/hospitality')
def hospitality():
    return render_template('hospitality.html')

@app.route('/it')
def it():
    return render_template('it.html')

@app.route('/advertising')
def advertising():
    return render_template('advertising.html')

@app.route('/sales')
def sales():
    return render_template('sales.html')

@app.route('/teaching')
def teaching():
    return render_template('teaching.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/<folder>/<filename>')
def article(folder, filename):
    return render_template('/' + folder + '/' + filename + '.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'username' in session:
        if request.method == 'POST':

            # Read the content from admin page
            job_title = request.form['title']
            job_desc = request.form['description']

            # print("job_title:---", job_title)
            # print("job_desc:---", job_desc)

            # Classify the job content
            if request.form['button'] == 'Classify':

                # Tokenize the job content
                tokenized_data = job_desc.split(' ')

                # Loading the FastText model
                jobsFT = FastText.load("jobsFT.model")
                jobsFT_wv= jobsFT.wv

                # Generate vector representation of the tokenized job data
                jobsFT_dvs = gen_docVecs(jobsFT_wv, [tokenized_data])

                # Load the Logistic Regression model
                pkl_filename = "fastText_uw_LR_model.pickle"
                with open(pkl_filename, 'rb') as file:
                    model = pickle.load(file)

                # Label prediction of tk_data
                y_pred = model.predict(jobsFT_dvs)
                y_pred = y_pred[0]

                return render_template('admin.html', prediction=y_pred, title=job_title, description=job_desc)
            
            elif request.form['button'] == 'Save':
                # First check if the recommended job category is empty
                cat_recommend = request.form['category']
                if cat_recommend == '':
                    return render_template('admin.html', prediction=cat_recommend,
                                        title=job_title, description=job_desc,
                                        category_flag='Recommended category must not be empty.')

                elif cat_recommend not in ['Accounting_Finance', 'Engineering', 'Healthcare_Nursing', 'Hospitality_Catering', 'IT', 'PR_Advertising_Marketing', 'Sales', 'Teaching']:
                    return render_template('admin.html', prediction=cat_recommend,
                                        title=job_title, description=job_desc,
                                        category_flag='Recommended category must belong to: Accounting_Finance, Engineering, Healthcare_Nursing, Hospitality_Catering, IT, PR_Advertising_Marketing, Sales, Teaching')

                else:

                    # Reading the html job template
                    soup = BeautifulSoup(open('templates/job_template.html'), 'html.parser')
                    
                    # Adding the job title
                    admin_page_title = soup.find('div', { 'class' : 'title' })
                    title = soup.new_tag('h1', id='data-title')
                    title.append(job_title)
                    admin_page_title.append(title)

                    # Add the job description
                    admin_page_desc = soup.find('div', { 'class' : 'data-job' })
                    content = soup.new_tag('p')
                    content.append(job_desc)
                    admin_page_desc.append(content)

                    # writing into a new html
                    filename_list = job_title.split()
                    filename = '_'.join(filename_list)
                    filename =  cat_recommend + '/' + filename + ".html"
                    with open("templates/" + filename, "w", encoding='utf-8') as file:
                        print(filename)
                        file.write(str(soup))

                    # Redirect to the newly-generated news article
                    return redirect('/' + filename.replace('.html', ''))

        else:
            return render_template('admin.html')
    
    else:
        return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect('/admin')
    else:
        if request.method == 'POST':
            if (request.form['username'] == 'Pallavi') and (request.form['password'] == 'Bhimte'):
                session['username'] = request.form['username']
                return redirect('/admin')
            else:
                return render_template('login.html', login_message='Username or password is invalid.')
        else:
            return render_template('login.html')


@app.route('/logout')
def logout():
    # remove the username from the session
    session.pop('username', None)

    return redirect('/')


@app.route('/search', methods = ['POST'])
def search():

    if request.method == 'POST':
    
        if request.form['search'] == 'Search':
            search_string = request.form["searchword"]

            # search over all the html files in templates to find the search_string
            article_search = []
            dir_path = 'templates'
            for folder in os.listdir(dir_path):
                if os.path.isdir(os.path.join(dir_path, folder)):
                    for filename in sorted(os.listdir(os.path.join(dir_path, folder))):
                        if filename.endswith('html'):
                            with open(os.path.join(dir_path, folder, filename), encoding="utf8") as file:
                                file_content = file.read()

                                # search for the string within the file
                                if search_string in file_content:
                                    article_search.append([folder, filename.replace('.html', '')])
            
            # generate the right format for the Jquery script in search.html
            num_results = len(article_search)

            return render_template('search.html', num_results=num_results, search_string=search_string,
                                   article_search=article_search)
    else:
        return render_template('home.html')