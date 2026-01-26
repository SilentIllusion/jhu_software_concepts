from flask import Flask, render_template

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

@app.route('/')
def home():
    return render_template('home.html', active_page='home')

@app.route('/projects')
def projects():
    return render_template('projects.html', active_page='projects')

@app.route('/contact')
def contact():
    return render_template('contact.html', active_page='contact')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
