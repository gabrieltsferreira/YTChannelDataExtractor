from flask import Blueprint, render_template, request, send_file
from channel_stats import get_channel_stats

views = Blueprint(__name__, 'views')

@views.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        channel_id = request.form.get('channelID')
        channel_info, data = get_channel_stats(channel_id)
        
        # send_file(
        #     'output/download.csv',
        #     mimetype='text/csv',
        #     download_name= channel_info['channel name'] + ' Channel Data' '.csv',
        #     as_attachment=True
        # )
        return render_template('results.html', channel_info = channel_info, data = data)
    
    
    return render_template('index.html')