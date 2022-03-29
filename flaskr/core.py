from flask import render_template,request,Blueprint

bp = Blueprint('core',__name__)

@bp.route('/')
def index():
    '''
    This is the home page view. Notice how it uses pagination to show a limited
    number of posts by limiting its query size and then calling paginate.
    '''
    
    return render_template('index.html')