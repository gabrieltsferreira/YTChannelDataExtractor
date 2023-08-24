from flask import Blueprint, render_template, request

views = Blueprint(__name__, 'views')

@views.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        channel_id = request.form.get('channelID')
        print(channel_id)

    return render_template('index.html')