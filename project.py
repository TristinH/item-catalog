import string, random

from flask import *
from flask import session as login_session

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Base, InstrumentCategory, Instrument

# initialize app 
app = Flask(__name__)

# create client id
CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

# setup engine for the database
engine = create_engine('sqlite:///instrumentscatalog.db')
Base.metadata.bind = engine

# start a session with the database
DBSession = sessionmaker(bind=engine)
session = DBSession()

# get all the categories once so we don't have to keep 
# querying for it
categories = session.query(InstrumentCategory).order_by(InstrumentCategory.category)

# helper function to get a category given the id
def getCategory(category_id):
	return session.query(InstrumentCategory).get(category_id)

# helper function to get an instrument given the id
def getInstrument(instrument_id):
	return session.query(Instrument).get(instrument_id)

# if the user enters an invalid ID in the url, flash
# an error message and redirect to the home page
def showUserError():
	flash("Invalid category or instrument ID")
	return redirect(url_for('displayHome'))


# main page handler
@app.route('/')
@app.route('/categories/')
def displayHome():
	return render_template('base.html', categories=categories, username=login_session.get('username'))


# sign in page, creates a state for the login
@app.route('/login')
def login():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) 
					for x in range(32))
	login_session['state'] = state
	return render_template('login.html', STATE=state)


# log user in 
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
    	login_session['access_token'] = credentials.access_token
    	print credentials.access_token
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# log the user out
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: ' 
    print login_session.get('username')

    if access_token is None:
		print 'Access Token is None'
		response = make_response(json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session.get('access_token')
    print url
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result

    if result['status'] == '200':
		del login_session['access_token'] 
		del login_session['gplus_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		response = make_response(json.dumps('Successfully disconnected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response
    else:	
    	response = make_response(json.dumps('Failed to revoke token for given user.', 400))
    	response.headers['Content-Type'] = 'application/json'
    	return response


# handler to display a single category with its instruments
@app.route('/category/<int:category_id>/')
def displayCategory(category_id):
	# get the category passed and display it's instruments
	category = getCategory(category_id)

	# check if the category ID is valid
	if not category:
		return showUserError()
	else:
		instruments = session.query(Instrument).filter_by(category_id=category_id).all()
		return render_template('category.html', categories=categories, 
								category=category, instruments=instruments)


# handler to add a new category to the database
@app.route('/category/add/', methods=['GET', 'POST'])
def addCategory():
	# check what HTTP method is being used
	if request.method == 'GET':
		return render_template('categoryadd.html')
	else:
		category = request.form['category']
		new_category = InstrumentCategory(category=category)
		session.add(new_category)
		session.commit()
		flash("%s added" % category)

		return redirect(url_for('displayCategory', categories=categories, category_id=category_id))


# handler to edit an existing category
@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
	# get the category
	category = getCategory(category_id)

	# check if the category ID is valid
	if not category:
		return showUserError()
	else:
		# check what HTTP method is being used
		if request.method == 'GET':
			return render_template('categoryedit.html', categories=categories, category=category)
		else:	
			category.category = request.form['category']
			session.add(category)
			session.commit()
			flash("%s updated" % category.category)

			return redirect(url_for('displayCategory', category_id=category_id))


# handler to delete an existing category
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
	# get the category
	category = getCategory(category_id)

	# check if the category ID is valid
	if not category:
		return showUserError()
	else:
		# check what HTTP method is being used
		if request.method == 'GET':
			return render_template('categorydelete.html', categories=categories, category=category)
		else:	
			session.delete(category)
			session.commit()
			flash("%s deleted" % category.category)

			return redirect(url_for('displayHome'))


# handler to display a single instrument information
@app.route('/category/<int:category_id>/<int:instrument_id>/')
def displayInstrument(category_id, instrument_id):
	# get the instruments category and instrument
	category = getCategory(category_id)
	instrument = getInstrument(instrument_id)

	# check if the category ID and instrument ID are valid
	if not (category and instrument):
		return showUserError()
	else:
		return render_template('instrument.html', categories=categories,
								category=category, instrument=instrument)

# handler to add a new instrument to the database
@app.route('/category/<int:category_id>/add/', methods=['GET', 'POST'])
def addInstrument(category_id):
	# get the category to add the instrument to
	category = getCategory(category_id)

	# check if the category ID is valid
	if not category:
		return showUserError()
	else:
		if request.method == 'GET':
			return render_template('instrumentadd.html', categories=categories, category=category)
		else:
			name = request.form['name']
			description = request.form['description']
			brand = request.form['brand']
			color = request.form['color']
			new_instrument = Instrument(name=name, description=description, brand=brand,
										color=color, category_id=category_id)
			session.add(new_instrument)
			session.commit()
			flash("%s added" % name)

			return redirect(url_for('displayInstrument', category_id=category_id,
									instrument_id=new_instrument.id))


# handler to edit and existing instrument
@app.route('/category/<int:category_id>/<int:instrument_id>/edit/', methods=['GET', 'POST'])
def editInstrument(category_id, instrument_id):
	# get the instrument's category and the instrument
	category = getCategory(category_id)
	instrument = getInstrument(instrument_id)

	# check if the category ID and instrument ID are valid
	if not (category and instrument):
		return showUserError()
	else:
		if request.method == 'GET':
			return render_template('instrumentedit.html', categories=categories,
								   category=category, instrument=instrument)
		else:
			instrument.name = request.form['name']
			instrument.description = request.form['description']
			instrument.brand = request.form['brand']
			instrument.color = request.form['color']
			session.add(instrument)
			session.commit()
			flash("%s updated" % instrument.name)

			return redirect(url_for('displayInstrument', category_id=category_id,
									instrument_id=instrument_id))


# handler to delete and existing instrument
@app.route('/category/<int:category_id>/<int:instrument_id>/delete/', methods=['GET', 'POST'])
def deleteInstrument(category_id, instrument_id):
	# get the instrument's category and the instrument
	category = getCategory(category_id)
	instrument = getInstrument(instrument_id)

	# check if the category ID and instrument ID are valid
	if not (category and instrument):
		return showUserError()
	else:
		# check what HTTP method is being used
		if request.method == 'GET':
			return render_template('instrumentdelete.html', categories=categories, category=category,
								   instrument=instrument)
		else:	
			session.delete(instrument)
			session.commit()
			flash("%s deleted" % instrument.name)

			return redirect(url_for('displayCategory', category_id=category_id))


# provide a JSON API endpoint for an entire category's instruments
@app.route('/category/<int:category_id>/JSON/')
def supplyCategoryJSON(category_id):
	# get the category
	category = getCategory(category_id)
	instruments = session.query(Instrument).filter_by(category_id=category_id).all()
	return jsonify(Instruments=[instrument.serialize for instrument in instruments])


# provide a JSON API endpoint for a single instrument
@app.route('/category/<int:category_id>/<int:instrument_id>/JSON/')
def supplyInstruemntJSON(category_id, instrument_id):
	# get the instrument
	instrument = getInstrument(instrument_id)
	return jsonify(Instrument=instrument.serialize)


if __name__ == '__main__':
	app.secret_key = 'i3jiofh130frh0i1'
	app.debug = True
	app.run(host = '0.0.0.0', port = 5000)
