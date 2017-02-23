'''
@author: Arlie Moore
2/23/2017

WebCrawler will crawl a url to a certain depth
and then add the information about these pages
into MongoDB. The web crawling is carried out
by threads which speed up execution time. 

Below are some timing results from testing with 
different thread counts. These times will vary
depending on network speeds and computer
specs. 

Testing times for custom test webpages at depth 4
threadCount --- executionTime --- pagesCrawled
          1 ---        10.263 ---           10 
          2 ---        6.292  ---           10  
          4 ---        5.281  ---           10  
          8 ---        5.295  ---           10  
         16 ---        5.304  ---           10  

Testing times for http://www.bbc.com/ at depth 1
threadCount --- executionTime --- pagesCrawled --- seconds per page
          1 ---       328.254 ---          175 ---            1.876     
          2 ---       185.147 ---          176 ---            1.052
          4 ---       146.978 ---          178 ---            0.826
          8 ---       139.558 ---          181 ---            0.784
         16 ---       148.613 ---          178 ---            0.835

Testing times for http://www.apple.com/ at depth 1
threadCount --- executionTime --- pagesCrawled --- seconds per page
          1 ---      1722.648 ---         1572 ---            1.100     
          2 ---       951.568 ---         1572 ---            0.605
          4 ---       706.204 ---         1572 ---            0.449
          8 ---       651.317 ---         1572 ---            0.414
         16 ---       630.067 ---         1571 ---            0.401


How to start MongoDB
Command: cd C:\Program Files\MongoDB\Server\3.4\bin
Command: mongod

'''
from WebScraper import WebScraper
from Link import Link
import threading
import queue
import pymongo
import time

class WebCrawler(object):
    
    NUM_THREADS = 4

    def __init__(self):
        
        #Set up mongo db client
        self.client = pymongo.MongoClient()
        self.db = self.client.db
        #Connect to the mongo db's
        self.words = self.db.db
        self.urlsCrawled = self.db.db2
        self.errors = self.db.db3
        self.stats = self.db.db4
        
        self.waitingThreads = 0
        self.crawlCount = 0
        self.running_threads = []
        self.dontCrawl = {}
        self.q = queue.Queue(maxsize=0)
    
    def workers(self, id, sema, sema2, cv, barrier):
        """workers are threads spawned by crawlURL.
        
        These workers will crawl a starting link
        to a certain depth, then end. While crawling,
        it will add data about these webpages to a 
        MongoDB database. 
        
        Args:
        
            id(int): Thread identifier
            sema(threading.Semaphore): guards crawlCount and waitingThreads
            sema2(threading.Semaphore): guards dontCrawl
            cv(threading.Condition): allowed threads to wait and be notified
            barrier(threading.Barrier): creates a barrier for threads
            
        """
        #make local connections for each thread
        client = pymongo.MongoClient()
        db = client.db
        words = db.db
        urlsCrawled = db.db2
        errors = db.db3
        
        done = False
        crawled = 0
        
        if id is 1:
            self.waitingThreads = 0
            self.crawlCount = 0
            self.dontCrawl = {}
            
        barrier.wait()
        while not done:
            try:
                # If `False`, the program is not blocked, it will throw the Queue.Empty exception.
                link = self.q.get(True, .1)
                url = link.getURL()
                depth = link.getDepth()
                #print("STARTED crawling url ", url)
                #if the url has not been crawled 
                #during this function call
                #then continue with crawl
                if not self.alreadyCrawled(url, sema2):
                    #create our scraper object
                    scraper = WebScraper(url)
                    if not scraper.error:
                        #print("No Scraper Error --- crawling url ", url)
                        if depth > 0:
                            #Put all links into a Python Set to remove duplicates
                            links = set(scraper.crawlLinks())
                            #Add all links to queue
                            for link in links:
                                queuedLink = Link(link, depth - 1)
                                self.q.put(queuedLink)
                        
                        #Notify other threads to check the queue again for links
                        #if they are currently waiting. 
                        sema.acquire()
                        self.waitingThreads = 0
                        cv.acquire()
                        cv.notify_all()
                        #print("Thread ", id, " NOTIFYING")
                        cv.release()
                        sema.release()
                        #Insert url into urlsCrawled
                        try:
                            urlsCrawled.insert({"url": url, "count": 1})
                            inserted = True
                        #If url has already been inserted, then just increment count
                        except pymongo.errors.DuplicateKeyError:
                            urlsCrawled.update_one({"url": url},{"$inc": {"count": 1}})
                            inserted = False
                        #If inserted, then the url's text needs to be added too. 
                        if inserted:
                            #Put all text into a Python Set to remove duplicate words
                            text = set(scraper.crawlText())
                            for word in text:
                                #Insert word into words
                                try:
                                    words.insert({"word":word, "urls":[url]})
                                #if word has already been inserted, then update urls. 
                                except pymongo.errors.DuplicateKeyError:
                                    words.update_one({"word": word}, {'$push': {"urls": url}})
                        #print("FINISHED Crawling url ", url)
                        crawled = crawled + 1
                    else:
                        #Insert error
                        errorMessage = scraper.getErrorMessage()
                        self.insertError(url, errorMessage, errors)
            #if the queue is empty, then have the threads
            #wait. If all the threads but one are waiting, then
            #no more urls need to be crawled and the workers are done.
            except queue.Empty:
                sema.acquire()
                if self.waitingThreads < self.NUM_THREADS - 1:
                    self.waitingThreads = self.waitingThreads + 1
                    #print("Thread ", id, " is waiting. Waiting Thread Count: ", self.waitingThreads)
                    sema.release()
                    with cv:
                        cv.wait()
                        #print("Thread ", id, " woken up.")
                else:
                    sema.release()
                    done = True
                    cv.acquire()
                    cv.notify_all()
                    cv.release()
        print("Thread ", id, " crawled ", crawled, " webpages.")
        sema.acquire()
        self.crawlCount = self.crawlCount + crawled
        sema.release()
        return
        

    def crawlURL(self, url, depth):
        """crawlURL spawns worker threads
        that will crawl a given url to a certain depth.
        
        Args:
        
            url(str): starting url to crawl
            depth(int): depth at which to stop crawling, MAX = 4
            
        """
        if depth > 4:
            depth = 4
        if(depth is 0) and (self.urlsCrawled.count({"url": url}) is not 0):
            return
        #start time for stats of crawl
        start = time.time()
        #add url and depth to the queue
        queuedLink = Link(url, depth)
        self.q.put(queuedLink)
        
        sema = threading.Semaphore()
        sema2 = threading.Semaphore()
        cv = threading.Condition()
        barrier = threading.Barrier(self.NUM_THREADS)
        
        for i in range(self.NUM_THREADS):
            t = threading.Thread(target=self.workers, args=(i + 1, sema, sema2, cv, barrier,))
            # t.setDaemon(True) # we are not setting the damenon flag
            t.start()

            self.running_threads.append(t)
        # joining threads (we need this if the daemon flag is false)
        for t in self.running_threads:
            t.join()
        
        crawlTime = round(time.time() - start, 3)
        print("Execution Time:", crawlTime)
        print("Crawled Count:", self.crawlCount)
        print("Error Count:", self.errors.find().count())
        self.stats.insert({"type": "crawl", 
                           "threadCount": self.NUM_THREADS,
                           "crawlCount": self.crawlCount, 
                           "executionTime": crawlTime,
                           "time": time.strftime("%I:%M:%S"), 
                           "date": time.strftime("%d/%m/%Y")})
        return
    
    
    def alreadyCrawled(self, url, sema2):
        """This method checks to see if the current
        url that is being crawled was already crawled 
        during this round of crawling. IT DOES NOT
        check if this url is in MongoDB, which holds
        records of ALL the rounds of crawling. 
        
        Args:
            url(str): The url that needs to checked
            sema2(threading.Semaphore): Semaphore to guard the 
                shared resource self.dontCrawl
        """        
        sema2.acquire()
        if url in self.dontCrawl:
            crawled = True
        else:
            self.dontCrawl[url] = 1
            crawled = False
        sema2.release()
        return crawled
    
    
    def insertError(self, url, errorMessage, errors):
        """This method will insert a error record
        into MongoDB. 
        
        Args:
            url(str): The url that the error appeared during
            errorMessage(str): The message that was created for the error
            errors: MongoDB connection that the error message is inserted into
        """
        crawlTime = str(time.strftime("%I:%M:%S"))
        crawlDate = str(time.strftime("%d/%m/%Y"))
        errors.insert({"type": "crawl",
                            "url": url, 
                            "errorMessage": errorMessage,
                            "time": crawlTime,
                            "date": crawlDate})
    
    
    def searchWords(self, word):
        """Searchs for a word in MongoDB, 
        and if that word exists then all
        of the url's that the word appears
        in will be printed.
        
        Args:
            word(str): Must be a single word without spacing
        """
        print("Here are all the url's that have '%s' in it." % word)
        for post in self.words.find({"word" : word}):
            for url in post['urls']:
                print(url)
        print('')
        return
    
    
    def delete(self):
        """delete will drop all MongoDB
        databases that were used for crawling
        """        
        self.client.drop_database(self.db)
        self.words.create_index([("word", pymongo.ASCENDING)], unique = True)
        self.urlsCrawled.create_index([("url", pymongo.ASCENDING)], unique = True)
        print("\nDatabases Deleted\n")
    
    
    def printWords(self):
        """printWords will print all words
        and the url's that word was found one
        """        
        print("---Printing Words---")
        for post in self.words.find().sort("word", pymongo.ASCENDING):
            urls = list(post['urls'])
            print(post['word'], "---urls--->", urls)
        print("---Done Printing Words---")
        
        
    def printURLS(self):
        """printURLS will print all url's
        and the count of how many times it has been crawled
        """        
        print("---Printing URLS---")
        for post in self.urlsCrawled.find():
            print(post['url'], ", ", post['count'])
        print("---Done printing URLS---")
    
    
    def printErrors(self):
        """printErrors will print all the errors
        that have been recorded
        """        
        print("---Printing Errors---")
        print("Format = 'errorMessage', 'url', 'time', 'date'")
        for post in self.errors.find():
            print(post['errorMessage'], ", ", post['url'], ", ", post['time'], ", ", post['date'])
        print("---Done printing Errors---")
        
        
    def printStats(self):
        """printStats will print the stats that
        have been recorded
        """        
        print("---Printing Stats---")
        print("Format = 'threadCount', 'urlsCrawled', 'executionTime', 'time', 'date'")
        for post in self.stats.find():
            print(post['threadCount'], ", ", post['crawlCount'], ", ", post['executionTime'], ", ", post['time'], ", ", post['date'])
        print("---Done printing Stats---")
        
    def test(self):
        url = "http://www.bbc.com/"
        #url = "http://www.apple.com/jobs/"
        #url = "http://images.apple.com/media/us/macbook-pro/2016/b4a9efaa_6fe5_4075_a9d0_8e4592d6146c/films/qwerty/macbook-pro-qwerty-cc-us-20161107_1280x720h.mp4"
        print("Creating Scraper")
        scraper = WebScraper(url)
        if scraper.error:
            print("Error Message", scraper.getErrorMessage())
        else:
            print("Crawling Text")
            text = scraper.crawlText()
            print(text)
