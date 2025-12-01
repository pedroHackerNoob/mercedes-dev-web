from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/user')
def home():  # put application's code here
    return render_template('services.html')
@app.route('/user/style')
def services():
    return render_template('stylist.html')

@app.route('/user/style/confirm')
def xd():
    return render_template('confirmation.html')

@app.route('/mod')
def scheduleMod():
    return render_template('modSchedule.html')

@app.route('/admin')
def admin():
    return render_template('adminPanel.html')

if __name__ == '__main__':
    app.run()
