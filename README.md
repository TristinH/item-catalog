# Installation/Run Instructions:

	Before trying to run the project ensure you have the latest versions of Flask and SQL Alchemy installed. You will also need 
	python 2.7 installed. First run the file db_setup.py. To do this use the command "python db_setup.py" in your terminal. This
	is crucial to setting up the database the app will use. If it is successful you will see a new file appear in the project 
	directory named instrumentscatalog which is a database file. 

	At this point you can run the project. Simply run the project.py file from the command line by executing the command "python 
	project.py". You should receive a response saying that the project is running on localhost port 5000. Open your browser and 
	navigate to http://localhost:5000. This should take you to the home page of the application. 

# Configuration:
	
	During development the project was mainly coded using sublime as the text editor. It was tested in google chrome. The modules
	from the python standard library used were string, random, httplib2, json, and requests. To be able to ensure the oauth 
	functionality, you will need a valid google client-id. This must be substituted in the login.html file in data-clientid. 
	Also, you need to put the client secrets JSON file that google generates for you in the project file and is used to get the 
	client id. For the database, the modules used were create_engine and sessionmaker. Also, the ORM classes from the db_setup 
	file are imported to perform database operations on the respective tables.

# Operation:

	The project supports all four database operation (create, read, update, and delete) for categories and items in the 
	categories (in this case instrument categories and individual instruments). Click on links to add new categories/items or 
	links to edit/delete existing categories/items. If you haven't signed in, these will prompt you to login with google to 
	authenticate you. Once you have been authenticated, you can add any new categories or instruments or edit/delete any 
	categories or instruments you have created. You will be taken to pages with respective forms for performing the operation you 
	are attempting to perform.      
