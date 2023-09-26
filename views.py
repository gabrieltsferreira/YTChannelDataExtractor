from flask import Blueprint, render_template, request, send_file
from channel_stats import get_channel_stats

views = Blueprint(__name__, 'views')

@views.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        channel_id = request.form.get('channelID')
        
        channel_info, insights = get_channel_stats(channel_id)
        
        # Invalid channel ID
        if channel_info == None:
            return render_template('index.html', error=True)
        
        check = request.form.getlist('check')[0]
        
        if check == 'download':
            return send_file(
                'output/download.csv',
                mimetype='text/csv',
                download_name= channel_info['channel_name'] + ' Channel Data' '.csv',
                as_attachment=True
            )
                
        elif check == 'analyse':           
            return render_template('results.html', channel_info = channel_info, insights = insights)
    
    
    return render_template('index.html')