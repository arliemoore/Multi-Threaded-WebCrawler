'''
@author: Arlie Moore
2/23/2017

WebScraper is an object that takes in a url. This
url is then sent a request and a response is recieved.
If this response has a Content-Type of "text/html" then
no errors will be thrown and the page can have its
links and text crawled and returned in a list. 
'''
from bs4 import BeautifulSoup
import urllib.request
import re
import gzip

class WebScraper(object):
    
    def __init__(self, url):
        '''This constructor takes in a url, creates a 
        request and gets back a response for that url. 
        This response is checked to make sure it can 
        be parsed correctly and if everything works
        then self.error is False. 
        '''
        
        self.url = url
        self.words = []
        self.links = []
        
        try:
            #Create the request
            req = urllib.request.Request(self.url, headers = {'User-Agent': 'Mozilla/5.0'})
            #Send the request, and get back a response
            response = urllib.request.urlopen(req, timeout=10)
            info = response.info()
            #if the responses content-type is not text/html, raise exception
            if str(info.get_content_type()) != "text/html":
                raise Exception("URL is of Content-Type", info.get_content_type())
            #Decode the response
            self.html = self.decode(response)
            #parse the text/html
            self.soup = BeautifulSoup(self.html, "html.parser")
            self.error = False
        except Exception as e:
            #print("Error " + str(httperror))
            self.error = True
            self.errorMessage = str(e)
    
    
    def decode(self, response):
        '''Decode responses from webservers. These
        responses need to be text/html to get to this stage, 
        and are decoded according to the the Content-Encoding
        of the response. This method will raise an error
        if the content-encoding is neither 'None' or 'gzip/x-zip'. 
        
        Args:
            response(urllib.request.urlopen): response from a request to a server
        '''
        encoding = response.getheader("Content-Encoding")
        if encoding == None:
            html = response
        elif encoding == 'gzip' or encoding == "x-gzip":
            html = gzip.decompress(response.read())
        else:
            raise Exception("Decoding Error: Can not decode %s response" % encoding)            
        return html
    
    
    def crawlLinks(self):
        '''This method gets all of the links
        that appear in the url given and then return
        them in a python list. 
        '''
        if self.error:
            return
        #Gets all the links and puts them into list
        for link in self.soup.find_all('a'):
            a = link.get('href')
            #print(a, " --- ", a[:1])
            if a is None:
                pass
            elif "http" in a:
                self.links.append(a)
            else:
                holder = urllib.parse.urljoin(self.url, a)
                self.links.append(holder.strip())
        return self.links
    
    def crawlText(self):
        '''This method gets all of the text
        that appears in the url given and then
        returns them in a python list.
        '''
        if self.error:
            return
        # kill all script and style elements
        for script in self.soup(["script", "style"]):
            script.extract()    # rip it out
            # get text
            text = self.soup.get_text()
            # break into lines and remove leading and trailing space on each
            
            lines = (line.strip() for line in text.splitlines())
            # break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            #replace all \n with spaces
            text = text.replace("\n", " ")
            #Remove all non-Alphanumeric chars
            text = re.sub("[^0-9a-zA-Z ]+", "", text)
            text = text.lower()
            self.words = text.split()
            #print(text)
            #print(text.encode(encoding='utf_8'))
        return self.words
    
    def getErrorMessage(self):
        '''This method returns
        the error message recorded
        if an error occurs.
        '''
        return self.errorMessage
    
