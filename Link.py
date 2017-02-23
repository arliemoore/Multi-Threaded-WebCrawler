'''
@author: Arlie Moore
2/23/2017

Link objects are created and then placed into a 
queue that the threads will retrieve and then crawl.
'''

class Link(object):
    def __init__(self, url, depth):
        self._url = url
        self._depth = depth
    
    def __str__(self):
        return self._url + ", " + str(self._depth)
    
    def getURL(self):
        return self._url
    
    def getDepth(self):
        return int(self._depth)