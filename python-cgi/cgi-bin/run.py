#!/usr/bin/python
# Tony Cotta 
# SER 421
# Last Modified 10/25/17
import sys, os, cgi, cgitb, datetime, Cookie, json
from os import environ
import xml.etree.ElementTree as ET

# User Object 
# Types: Guest, Subscriber, Reporter
class User:
	# Constructor
	def __init__(self, type = 'Guest', uName = 'guest'):
		self.type = type
		self.uName = uName

	def getType(self):
		return self.type

	def getuName(self):
		return self.uName

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

		# Display stories by user type
		if user.getType() == 'Subscriber':
			# Subscribers can read any news story
			# SHOW ALL STORIES
			print "<p>%s</p>" % title

		elif user.getType() == 'Reporter':
			# Reporter can public stories, and stories written by them
			if (public == "T" or author == user.getuName()):
				print "<p>%s</p>" % title 
		else:
			# User must be a guest
			# Show all PUBLIC stories
			if public == "T":
				print "<p>%s</p>" % title

# Method that dynamically decides if the Login or Logoff propt should be shown.
def showLoginButton(user):
	if user.getType() == 'Guest':
		# Display the login prompt if the user is of type guest
		# Note: all users are 'Guest' by default until they log in.
		print "<FORM METHOD='POST' ACTION='http://localhost:8080/?Login=true'>"
		print "<INPUT TYPE='submit' VALUE='Login' NAME='Login2'></FORM>"		
	else:
		# Display the logout button 
		print "<FORM METHOD='POST' ACTION='http://localhost/?Login=false'>"
		print "<INPUT TYPE='submit' VALUE='Logout' NAME='Login2'></FORM>"
	
	print "<p>Hello %s, you are browsing with %s privledges. Here are today's news stories.</p><br/>" % (user.getuName(), user.getType())

# Sets the user type. Sets user type to Guest by default
# If user is in persistent store, then the stored user type is applied.
def checkUserLogin(user):
	type = "Guest"
	try:
		json_file = 'newsusers.json'
		json_data = open(json_file)
		data = json.load(json_data)
    	
    	# Access data
		for x in data['users']:
			# If the username is in the stored json list assign role as 
			# described in json file
			if (x['name'] == user.getuName()):
				type = x['role']
			#print x['name']
 		json_data.close
 	except (ValueError, KeyError, TypeError):
		print "JSON format error"

	return User(type, user.getuName())

def printHeader(expiration, user):
	# Write out the response header
	print "Set-Cookie:Expires=%s" % (expiration)
	print "Set-Cookie:UserID=%s" % (user.getuName())
	# ^^ Generally a bad idea to pass userID's here ^^
	print "content-type: text/html; charset=utf-8"
	print ""
	# Write out the HTML
	print "<HTML><HEAD><TITLE>NEW News Articles</TITLE></HEAD>"
	
	#printEnvVars()

# Used for testing. Prints the current environment variables
def printEnvVars():
	print "<font size=+1>Environment</font><\br>";
	for name, value in os.environ.items():
		print "%s\t= %s <br/>" % (name, value)

def showLoginPage():
	print """ 	<BODY>
		<FORM METHOD='POST' ACTION='http://localhost:8080/?Login=false'>User Name:<br>
			<input type='text' name='userName' cols='50' required><br>
			User Role:
			<tab indent=26>Subscriber<input type='radio' name='userRole' value='Subscriber'>
			<t>
			<tab indent=6>Reporter<input type='radio' name='userRole' value='Reporter' checked>
			<br>
			<input type='submit' value='Submit'><br>
		</form> """
	printEnvVars()

# Main Program Logic
def main():
	# Check for current user cookie value
	user_id = "guest"	
	cook = Cookie.SimpleCookie()
	if 'HTTP_COOKIE' in os.environ:
		cookie_string = os.environ.get('HTTP_COOKIE')
		cook.load(cookie_string)
	try:
		user_id = cook['UserID'].value
		#print "cookie data: " + data + "<br/>"
	except KeyError:
		pass
		#print "The cookie was not set or has expired<br>"

	# Get the current time
	now = datetime.datetime.now()
	# Add 1 hour to the current time
	expires = now + datetime.timedelta(hours=1)
	# ^^ will be used to expire a cookie ^^

	# Set this user type NEEDS TO BE MODIFIED
	thisUser = User(uName = user_id)

	# Used for testing
	firstUser = User('Subscriber', 'Admin')
	secondUser = User('Reporter', 'Brandon Wise')
	thirdUser = User(uName = 'Admin')
	fourthUser = User(uName = 'test')
	guestUser = User('Guest', 'guest')
	#thisUser = firstUser
	#thisUser = secondUser
	#thisUser = guestUser
	#thisUser = thirdUser
	#thisUser = fourthUser

	thisUser2 = checkUserLogin(thisUser)
	thisUser = thisUser2


	# Prints the HTTP Header and HEAD of the HTML
	printHeader(expires, thisUser)

	###########################################################################

	# Landing and Story Page Title Header
	print "<BODY><H1>NEW News Articles</H1><br/>"

#	INSERT BUSINESS LOGIC TO READ ENV VARIABLES TO DECIDE WHICH PAGE TO RENDER
	# Create instance of FieldStorage 
	form = cgi.FieldStorage() 

	# Get data from fields
	log = 'false'
	logged_in = form.getvalue('Login')
	#print logged_in

	if logged_in == None:
		#print "Logged in = " + logged_in

		showLoginButton(thisUser)


	#print firstUser.getuName() + " is a " + firstUser.getType() + "<br/>"
	#print secondUser.getuName() + " is a " + secondUser.getType() + "<br/>"
	#print guestUser.getuName() + " is a " + guestUser.getType() + "<br/>"

	#print "Current time = " + now.ctime() + "<br/>"
	#print "Cookie expires: " + expires.ctime() + "<br/>"
	#print "User ID  = %s<br/>" % user_id
	#print "Password = %s<br/>" % password

		showArticles(thisUser)
	else: # If user clicked "Login" Button
		showLoginPage()
	#showArticles(guestUser)
	#showArticles(firstUser)
	#showArticles(secondUser)

	#<form action="/cgi-bin/hello_get.py" method="get">
	#First Name: <input type="text" name="first_name">  <br />

	#Last Name: <input type="text" name="last_name" />
	#<input type="submit" value="Submit" />
	#</form>
	print "</BODY></HTML>"


# write out the HTML
#print "<HTML><HEAD><TITLE>NEW News Articles</TITLE><style>.butLink {display: inline-block;width: 25px;height: 6px;margin: 1em;}</style></HEAD>"
#print "<BODY><h2>Welcome Guest, you currently have Guest privileges</h2><FORM METHOD='GET' ACTION='http://lead2.poly.asu.edu:8080/NewNews/logger'><INPUT TYPE='submit' VALUE='Login'></FORM></BODY>"
#print "</HTML>"

try:   # NEW
    #print("Content-type: text/html\n\n")   # say generating html
    main() 
except:
    cgi.print_exception()                 # catch and print errors












