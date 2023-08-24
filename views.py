from flask import Blueprint, render_template, request
from channel_stats import get_channel_stats

views = Blueprint(__name__, 'views')

@views.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        channel_id = request.form.get('channelID')
        data = get_channel_stats(channel_id)
        
        return data

    return render_template('index.html')