import os
import urllib
import json

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2


JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)

f = open("abbreviationSynonym.json")
synonym_dic = json.loads(f.read())
f.close()	
	
#verify if a term is in our vocabulary
def isTermInVocab(term):
	if term in synonym_dic:
		return synonym_dic[term]   #return a list of its normalization forms
	else:
		return False      #no finding the term
	
#write the backend data into the html templates
def writeTemplate(self, template_values, templateFile):
	template = JINJA_ENVIRONMENT.get_template(templateFile)
	self.response.write(template.render(template_values))


#get the records of the term from our database	
def getTermDic(term):
	
	f = open("finalDictionaryMoreLink.json")
	wholeDic_dic = json.loads(f.read())    #get the whole dictionary
	f.close()
	
	if term in wholeDic_dic:
		finding_dic = {"name":term}                           #the normalization style
		finding_dic["abbreviation"] = wholeDic_dic[term][0]   #the abbreviation/full name of the given term
		finding_dic["synonym"] = wholeDic_dic[term][1]       #the synonyms of the given term		
		finding_dic["relevantWords"] = []
		for item in wholeDic_dic[term][2]:
			if item in synonym_dic:    #it is in our database
				finding_dic["relevantWords"].append((item, 1))
			else:
				finding_dic["relevantWords"].append((item, 0))
		finding_dic["wikiLink"] = wholeDic_dic[term][3]          #the wikipedia/tagWiki/github link list for parsing intro
		finding_dic["relevantLinks"] = wholeDic_dic[term][4]     #the relevant link list
		metaData =  ", ".join(wholeDic_dic[term][2]).replace("_", " ")
		return metaData, finding_dic
	
#get multiple candidates with its definition
def getMultipleCandidates(normalization_list):
	f = open("definition.json")
	definition_dic = json.loads(f.read())    #get the whole dictionary
	f.close()
	
	termDefine_dic = {}       #for each term, store its definition link
	for term in normalization_list:
		if term in definition_dic:
			termDefine_dic[term] = definition_dic[term]
		else:               #if no wiki links, still store the empty list
			termDefine_dic[term] = []
	return termDefine_dic
	
#fill in the template file to show our results		
class TermDic(webapp2.RequestHandler):
	def get(self):
		term = self.request.path_info.replace('/term/', '').replace("%23", "#").replace("_", " ").lower()
		normalization_list = isTermInVocab(term)   #a list of normalization forms or 
		if normalization_list is False:       #the term is not in our database
			template_values = {"name":  term}
			writeTemplate(self, template_values, 'template_error.html')
		else:
			if len(normalization_list) == 1:    #only one normalization form
				metaData, finding_dic = getTermDic(normalization_list[0])  
				template_values = {"name": finding_dic["name"], "finding_dic":  json.dumps(finding_dic), "metaData": metaData}
				writeTemplate(self, template_values, 'template.html')
			else:       #there are more than one normalization forms
				termDefine_dic = getMultipleCandidates(normalization_list)     #get all its potential full names with its wiki link
				template_values = {"name": term, "termDefine_dic":  termDefine_dic}
				writeTemplate(self, template_values, 'template_multiple.html')
					
		
		
#Give data to the broswer extension or someone who wants to use it		
class Post_json(webapp2.RequestHandler):
	def get(self):
		self.response.headers.add_header("Access-Control-Allow-Origin", "*")  #Allow access. refer to http://enable-cors.org/server_appengine.html
		term = self.request.path_info.replace('/api/', '').replace("%23", "#").replace("_", " ").lower()
		normalization_list = isTermInVocab(term)    #
		if normalization_list is False:   #the term is not in our database
			finding_dic = {"name": [term], "wikiLink":[], "relevantWords":[]}
		else:
			f = open("APIdata.json")
			wholeDic_dic = json.loads(f.read())    #get the whole dictionary
			f.close()
			finding_dic = wholeDic_dic[normalization_list[0]]
			finding_dic["name"] = normalization_list
		self.response.write(json.dumps(finding_dic))		
		

application = webapp2.WSGIApplication([
	('/term/.*', TermDic),
	("/api/.*", Post_json),
], debug=True)