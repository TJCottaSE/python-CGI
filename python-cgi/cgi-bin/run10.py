#!/usr/bin/python
# Tony Cotta 
# SER 421
# Last Modified 10/30/17
# Tested under python ver 2.7.14

# Author Names cannot contain spaces since the username is assumed to be 
# the authors name. Spaces in the authors name will break persistence 
# across pages.

# User name "guest" cannot be given permissions other than Guest

# Articles cannot have the same title

import sys, os, cgi, cgitb, datetime, Cookie, json, time
from os import environ, path
import xml.etree.ElementTree as ET

# Main Program
def main(controller = 1):
	user_id = 'guest'
	if (controller == 1):
		user_id = getUserFromCookie()
	elif (controller == 2): # Used for Logout
		user_id = 'guest'
	thisUser = User(uName = user_id)
	# WARNING: ^^ This breaks if a user with username "guest" is added
	# to the persistent store with privledges other than Guest.

	thisUser2 = checkUserLogin(thisUser)
	thisUser = thisUser2

	formData = getFormData()

	if (formData[0] == 'logout'):
		formData[1] = 'guest'
		formData[7] = 'Guest'

	if (formData[2] == 'create' or formData[2] == 'edit'):
		saveArticle(formData)

	if (formData[6] == 'true'):
		deleteArticle(formData[3])

	updatedUser = buildHeader(thisUser, formData)

	buildBody(updatedUser, formData)

	buildFooter()

	print headerContent + htmlContent


#############################################################
# MODULES													#
#############################################################

# Builds the HTTP Header and <HEAD>
def buildHeader(user, data, code = 200):
	global headerContent
	headerContent = ""
	setHTTPStatusCode(code)
	thisUser = setCookies(user, data)
	setContentType()
	buildHead()
	return thisUser

# Builds the <BODY> of the reponse
def buildBody(user, data):
	global htmlContent
	htmlContent = ""
	page = data[0]
	uName = data[1]
	ref = data[2]

	setTitle(page)
	
	newUser = User()
	newData = data
	newData[2] = 'news'
	if (page == 'logout'):
		showLoginButton(newUser, page)
		showCreateLink(newUser, page)
	else:
		showLoginButton(user, page)
		showCreateLink(user, page)

	if (page == 'logout'):
		buildHeader(newUser, newData)
		showArticles(newUser)
	elif (page == 'news'):
		showArticles(user)
	elif (page == 'login'):
		showLoginPage()
	elif (page == 'create'):
		createStory()
	elif (page == 'edit'):
		editStory(data[3])
	elif (page == 'delete'):
		showDelete(data[3])
	elif (page == 'article'):
		showArticlePage(data[3])
	else:
		print "Something went wrong"

# Closes the HTML document
def buildFooter():
	printb( "</BODY></HTML>")

# Gets the form data submitted by the user 
def getFormData():
	form = cgi.FieldStorage()
	page = getPageType(form)
	uName = getUserNameFromForm(form)
	ref = getRefer(form)
	title = getTitle(form)
	visibility = getVisibility(form)
	article = getArticle(form)
	delete = getAction(form)
	type = getUserType(form)
	return [page, uName, ref, title, visibility, article, delete, type]


#############################################################
# buildHeader Module Methods                                #
#############################################################

# Sets the userID cookie and its expiration in the HTTP Header
def setCookies(user, data):
	thisUser = User('Guest', 'guest')
	if (data[2] == 'login'):
		thisUser.setUserName(data[1])
		thisUser2 = checkUserLogin(thisUser)
		thisUser = thisUser2
	elif (data[2] != 'logout'):
		thisUser = user
	else:
		pass

	# Get the current time
	now = datetime.datetime.now()
	# Add 1 hour to the current time
	expires = now + datetime.timedelta(hours=1)
	# ^^ will be used to expire a cookie ^^

	printh( "Set-Cookie:UserID=%s;Expires=%s" % (thisUser.getuName(), expires))
	# ^^ Generally a bad idea to pass userID's here ^^

	return thisUser

# Sets the HTTP Status code in the response header
def setHTTPStatusCode(statusNumber):
	printh( "Status: {0}".format(statusNumber))

# Sets the HTTP content type in the response header
def setContentType():
	printh( "Content-type: text/html; charset=utf-8")
	printh( "")
#	^^ DO NOT REMOVE: Ends Http Header with space

# Starts the HTML Content Sections
def buildHead():
	printb( """<HTML>
		<HEAD>
			<TITLE>NEW News Articles</TITLE>
		</HEAD>""")


#############################################################
# buildBody Module Methods                                  #
#############################################################

# Choose the page type to display
def setTitle(page):
	if (page == 'news' or page =='logout'):
		printb( "<BODY><H1>NEW News Articles</H1><br/>")
	elif (page == 'login'):
		printb( "<BODY><H1>Login</H1><br/>")
	elif (page == 'create'):
		printb( "<BODY><H1>Create Story</H1><br/>")
	elif (page == 'edit'):
		printb( "<BODY><H1>Edit Story</H1><br/>")
	elif (page == 'delete'):
		printb( "<BODY><H1>Delete Story</H1><br/>")
	elif (page == 'article'):
		pass
	else:
		printb( "<BODY><H1>Error: Title Error</H1><br/>")

# Method that dynamically decides if the Login or Logoff prompt should be shown.
def showLoginButton(user, page):
	if (user.getType() == 'Guest' and page != 'login'):
		# Display the login prompt if the user is of type guest and not on the login page
		# Note: all users are 'Guest' by default until they log in.
		printb( "<FORM METHOD='POST' ACTION='http://localhost:8080/'>")
		printb( "<INPUT TYPE='submit' VALUE='Login'>")
		printb( "<INPUT TYPE='hidden' NAME='page' VALUE='login'></FORM>")	
	elif (user.getType() != 'Guest' and page != 'login'):
		# Display the logout button if user is logged in and not on the login page
		printb( "<FORM METHOD='POST' ACTION='http://localhost:8080/'>")
		printb( "<INPUT TYPE='submit' VALUE='Logout'>")
		printb( "<INPUT TYPE='hidden' NAME='page' VALUE='logout'></FORM>")
	
	printb( "<p>Hello %s, you are currently browsing with %s privledges.</p><br/>" % (user.getuName(), user.getType()))

# Method that dynamically add the ability to create a news story if they are a reporter
def showCreateLink(user, page):
	if (user.getType() == 'Reporter' and page != 'create'):
		printb( "<a href='?page=create'>Create New Article</a><br/>")

# Method that dynamically decides which articles to show based on user type.
def showArticles(user):
	# Parse the xml document for stories
	tree = ET.parse('news.xml')	
	root = tree.getroot()
	for article in root.iter('ARTICLE'):
		title = article.find('TITLE').text
		author = article.find('AUTHOR').text
		public = article.find('PUBLIC').text
		content = article.find('CONTENT').text
		title2 = title
		# Display stories by user type
		if (user.getType() == 'Subscriber'):
			# Subscribers can read any news story
			# SHOW ALL STORIES
			printb( "<a href='?page=article&title={0}'>{1}</a><br/>".format(title, title))

		elif (user.getType() == 'Reporter'):
			# Reporter can view public stories, and stories written by them
			if (public == "T" or author == user.getuName()):
				
				if (user.getuName() == author):
					editBtn = "<a href='?page=edit&title={0}'><button>Edit</button></a>".format(title)
					deleteBtn = "<a href='?page=delete&title={0}'><button>Delete</button></a>".format(title)
					printb( "<a href='?page=article&title={0}'>{1}</a>{2}{3}<br/>".format(title, title, editBtn, deleteBtn))
				
				else:
					printb( "<a href='?page=article&title={0}'>{1}</a><br/>".format(title, title))

		else:
			# User must be a guest
			# Show all PUBLIC stories
			if public == "T":
				printb( "<a href='?page=article&title={0}'>{1}</a><br/>".format(title, title))

# Createa the Display of the login page
def showLoginPage():
	printb( """ 	<BODY>
		<FORM METHOD='POST' ACTION='?page=news'>User Name:<br>
			<input type='text' name='userName' cols='50' required><br>
			User Role:
			<tab indent=26>Subscriber<input type='radio' name='userRole' value='Subscriber'>
			<t>
			<tab indent=6>Reporter<input type='radio' name='userRole' value='Reporter' checked>
			<br>
			<input type='hidden' NAME='refer' VALUE='login'>
			<input type='submit' value='Submit'><br>
		</form> """)

# Creates the Display of the create story page
def createStory():
	printb( """	<BODY>
		<form action='?page=news' method='POST'>Title:<br>
			<input type='text' name='title' cols='50' required>
			<br>Article Visibility:
			<tab indent=26>Public<input type='radio' name='visibility' value='T'><t>
			<tab indent=6>Private<input type='radio' name='visibility' value='F' checked><br>
				<textarea name='article' rows='20' cols='85' required></textarea>
				<br><input type='hidden' NAME='refer' VALUE='create'>
				<input type='submit' value='Submit'>
				<br>
		</form>""")

# Gets the story to be edited, and then creates the edit story page with the appropriate content
def editStory(searchTitle):
	editableTitle = ""
	editableArticle = ""
	oldTitle = ""
	# Parse the xml document for stories
	tree = ET.parse('news.xml')	
	root = tree.getroot()
	for article in root.iter('ARTICLE'):
		title = article.find('TITLE').text
		oldTitle = title
		if (title == searchTitle):
			# parse data
			editableTitle = title
			editableAuthor = article.find('AUTHOR').text
			editableArticle = article.find('CONTENT').text
	# ^^ WARNING: This breaks if there is more than one article with the same name ^^ #

	printb( """	<BODY>
		<form action='?page=news' method='POST'>Title:{0}<br>
			<br>Article Visibility:
			<tab indent=26>Public<input type='radio' name='visibility' value='T'><t>
			<tab indent=6>Private<input type='radio' name='visibility' value='F' checked>
			<br>
			<textarea name='article' rows='20' cols='85' required>{1}</textarea>
			<br>
			<input type='hidden' NAME='refer' VALUE='edit'>
			<input type='hidden' NAME='title' VALUE='{0}'>
			<input type='submit' value='Submit'>
			<br>
			<input type='hidden' name='oldTitle' value='{2}'>
		</form>""".format(editableTitle, editableArticle, oldTitle))

# Shows the Page with a single article
def showArticlePage(searchTitle):
	articleText = ""
	author = ""
	dispTitle = ""
	# Parse the xml document for stories
	tree = ET.parse('news.xml')	
	root = tree.getroot()
	for article in root.iter('ARTICLE'):
		title = article.find('TITLE').text
		if (title == searchTitle):
			# parse data
			dispTitle = title
			author = article.find('AUTHOR').text
			articleText = article.find('CONTENT').text
	
	printb( "<BODY><h3>{0}</h3> by {1}<br/><br/>{2}".format(dispTitle, author, articleText))

# adds the delete button to the page, assumes user has proper permissions
def showDelete(searchTitle):
	articleText = ""
	author = ""
	dispTitle = ""
	# Parse the xml document for stories
	tree = ET.parse('news.xml')	
	root = tree.getroot()
	for article in root.iter('ARTICLE'):
		title = article.find('TITLE').text
		if (title == searchTitle):
			# parse data
			dispTitle = title
			author = article.find('AUTHOR').text
			articleText = article.find('CONTENT').text

	cancelBtn = "<a href='?page=news'><button>Cancel</button></a>"
	deleteBtn = "<a href='?page=news&delete=true&title={0}'><button>Delete</button></a>".format(title)			
	printb( "<h1>{0}</h1> by {1}<br/><br/>{2}<br/>".format(dispTitle, author, articleText))
	printb( "<br/><h2>Are you sure you want to delete this article?</h2>{0}{1}".format(deleteBtn, cancelBtn))


#############################################################
# getFormData Module Methods                                #
#############################################################

# Gets the type of page requested by the user or news as default
# FormData helper
def getPageType(form):
	page = 'news'
	# Get data from fields
	p = form.getvalue('page')
	if (p != None):
		page = p
	return page

# Gets the User Name passed from the login page form
# FormData helper
def getUserNameFromForm(form):
	uName = 'guest'
	u = form.getvalue('userName')
	printh ("UnamePassed:{0}".format(u))
	if (u != None):
		uName = u
	return uName

# Gets the refering page
# FormData helper
def getRefer(form):
	ref = 'none'
	r = form.getvalue('refer')
	if (r != 'none'):
		ref = r
	return ref

# Gets the title of the article to be added if it exists
# FormData helper
def getTitle(form):
	title = 'none'
	t = form.getvalue('title')
	if (t != None):
		title = t
	return title

# Gets the visibility of the article to be added if the article exists
# FormData helper
def getVisibility(form):
	vis = 'F'
	v = form.getvalue('visibility')
	if (v != None):
		vis = v
	return vis

# Gets the Article Content if the article exists
# FormData helper
def getArticle(form):
	article = 'none'
	a = form.getvalue('article')
	if (a != None):
		article = a
	return article

# Gets the delete action tag
def getAction(form):
	delete = 'false'
	d = form.getvalue('delete')
	if (d != None):
		delete = d
	return delete

# Gets the user type from form
def getUserType(form):
	type = 'Guest'
	t = form.getvalue('userRole')
	if (t != None):
		type = t
	return type


#############################################################
# HELPER FUNCTIONS                                          #
#############################################################

# Used for testing. Prints the current environment variables
def printEnvVars():
	printb( "<font size=+1>Environment</font><\br>");
	for name, value in os.environ.items():
		printb( "%s\t= %s <br/>" % (name, value))

# Sets the user type. Sets user type to Guest by default
# If user is in persistent store, then the stored user type is applied.
def checkUserLogin(pUser):
	type = "Guest"
	try:
		json_file = 'newsusers.json'
		json_data = open(json_file)
		data = json.load(json_data)
		inStore = 'false'
		retUser = User()
    	# Access data
		for user in data['users']:
			# If the username is in the stored json list assign role as 
			# described in json file
			if (user['name'] == pUser.getuName()):
				type = user['role']
				inStore = 'true'
				retUser = User(type, pUser.getuName())

		# If username is not in persistent store, add it
		if (inStore == 'false' and pUser.getuName() != 'guest'):
			# Get Type from post
			# Get User Name from post

			tempUser = addNewUser()
			retUser = User(tempUser.getType(), tempUser.getuName())

 		json_data.close
 	except (ValueError, KeyError, TypeError):
		printb ("JSON format error")
	
	return retUser

# Get the user ID from a cookie if it exists otherwise set as guest
def getUserFromCookie():
	user_id = "guest"	
	cook = Cookie.SimpleCookie()
	if 'HTTP_COOKIE' in os.environ:
		cookie_string = os.environ.get('HTTP_COOKIE')
		cook.load(cookie_string)
	try:
		user_id = cook['UserID'].value
	except KeyError:
		pass
	
	return user_id


#############################################################
# I/O Functions                                             #
#############################################################

# Creates a file to represent a locked state. This is necessary
# since cgi's are their own processes that cannot talk to eachother.
# This implements a lock mechanism using the standard file system 
# components, rather than true thread synch, with something like 
# mutexes, or semaphores
def acquireFileLock(filename):
	filelock = filename + ".lock"
	# while the lock file exists
	while (os.path.isfile(filelock)):
		time.sleep(0.2) # busy wait
	# when the file no longer exists
	# create it, locking the file
	lock = open(filelock, 'wb+')
	lock.write("Locked") 
	lock.close()

# releases the lock on a resource
def releaseFileLock(filename):
	filelock = filename + ".lock"
	os.remove(filelock)

# Adds a new user to the persistent store
def addNewUser():
	acquireFileLock('newsusers.json')
	formData = getFormData()
	name = formData[1]
	type = formData[7]
	# Add the user to the persistent store
	json_data = open('newsusers.json', 'r+')
	data = json.load(json_data)
	data['users'].append({"name":name,"role":type})

	json_data.seek(0)        # <--- should reset file position to the beginning.
	json.dump(data, json_data, indent=4)
	json_data.truncate()     # remove remaining part
	releaseFileLock('newsusers.json')
	return User(formData[1], formData[7])

# Deletes all articles with title = searchTitle
def deleteArticle(searchTitle):
	acquireFileLock('news.xml')
	# Parse the xml document for stories
	tree = ET.parse('news.xml')	
	root = tree.getroot()
	for article in root.iter('ARTICLE'):
		title = article.find('TITLE').text
		if (title == searchTitle):
			root.remove(article)
	tree.write('news.xml')
	releaseFileLock('news.xml')

# Edits an existing article or creates a new one in the persistent store
def saveArticle(formData):
	acquireFileLock('news.xml')
	tree = ET.parse("news.xml")
	root = tree.getroot()
	# If the article should exist in the document already
	if (formData[2] == 'edit'):
		for article in root.iter('ARTICLE'):
			title = article.find('TITLE').text
			# If passed title=formData[3] matches parsed title, update fields
			if (formData[3] == title):
				vis = article.find('PUBLIC')
				vis.text = formData[4]
				con = article.find('CONTENT')
				con.text = formData[5]
				
	# Creating a new article element
	else:
		#news = tree.find('NEWS').text          # Get parent node from EXISTING tree
		b = ET.SubElement(root, 'ARTICLE')
		title = ET.SubElement(b, 'TITLE')
		title.text = formData[3]
		author = ET.SubElement(b, 'AUTHOR')
		author.text = formData[1]
		public = ET.SubElement(b, 'PUBLIC')
		public.text = formData[4]
		art = ET.SubElement(b, 'CONTENT')
		art.text = formData[5]
	
	tree.write("news.xml")
	releaseFileLock('news.xml')

# Adds content to html header
def printh(strToAdd):
	#print strToAdd
	global headerContent
	headerContent += strToAdd + "\n"

# Adds content to html page
def printb(strToAdd):
	#print strToAdd
	global htmlContent
	htmlContent += strToAdd


#############################################################
# CLASSES                                                   #
#############################################################
class User:
	# Constructor
	def __init__(self, type = 'Guest', uName = 'guest'):
		self.type = type
		self.uName = uName

	def getType(self):
		return self.type

	def setType(self, pType):
		self.type = pType

	def getuName(self):
		return self.uName

	def setUserName(self, pUname):
		self.uName = pUname

# Story Object 
class Story:
	# Constructor
	def __init__(self, status, author):
		self.status = status
		self.author = author

	def getStatus(self):
		return self.status

	def getAuthor(self):
		return self.author


#############################################################
# GLOBALS                                                   #
#############################################################
headerContent = ""
htmlContent = ""

#Execute Main Program
try:
	main()
except:
	cgi.print_exception()















