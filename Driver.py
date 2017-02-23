'''This class provides a terminal
interface for the WebCrawler.
 @author: Arlie Moore
 2/23/2017
'''
from WebCrawler import WebCrawler

def main():
    
    crawler = WebCrawler()
    
    test = False
    done = False
    
    if test:
        crawler.test()
    else:
        while(not done):
            print("Webcrawler Options")
            print("1. Crawl Web URL")
            print("2. Search Crawled Sites")
            print("3. View names of URL's Crawled")
            print("4. View words crawled")
            print("5. Delete databases")
            print("6. View Errors")
            print("7. View Stats")
            print("8. Exit")
            option = input("Select number: ")
            if(option == "1"):
                url = input("URL: ")
                depth = int(input("Depth: "))
                crawler.crawlURL(url, depth)
            elif(option == "2"):
                word = input("Search for links that contain the word: ")
                word = word.split()
                word = word[0]
                word = word.lower()
                crawler.searchWords(word)
            elif(option == "3"):
                crawler.printURLS()
            elif(option == "4"):
                crawler.printWords()
            elif(option == '5'):
                crawler.delete()
            elif(option == '6'):
                crawler.printErrors()
            elif(option == '7'):
                crawler.printStats()
            elif(option == '8'):
                print("Exiting WebCralwer, Goodbye...")
                exit()
            elif(option == "9"):
                crawler.printDoubles()
            else:
                print("Invalid Input, try again with a number.")
                
if __name__ == "__main__":
    main()