# Multi-Threaded-WebCrawler\n

Created by: Arlie Moore

WebCrawler will crawl a url to a certain depth
and then add the information about these pages
into MongoDB. The web crawling is carried out
by threads which speed up execution time.


Requirments:

1. Python 3.4.3
2. MongoDB 3.4
4. pyMongo
3. Beautiful Soup 4


Below are some timing results from testing with 
different thread counts. These times will vary
depending on network speeds and computer
specs. 

1. Testing times for 10 custom test webpages at depth 4

| Threads Count | executionTime | pagesCrawled | seconds/page |
|--------------:|--------------:|-------------:|-------------:|
|              1|         10.263|            10|         1.026|
|              2|          6.292|            10|         0.629|
|              4|          5.281|            10|         0.528|
|              8|          5.295|            10|         0.510|
|             16|          5.304|            10|         0.530|

2. Testing times for http://www.bbc.com/ at depth 1

| Threads Count | executionTime | pagesCrawled | seconds/page |
|--------------:|--------------:|-------------:|-------------:|
|              1|        328.254|           175|         1.876|
|              2|        185.147|           176|         1.052|
|              4|        146.978|           178|         0.826|
|              8|        139.558|           181|         0.784|
|             16|        148.613|           178|         0.835|

3. Testing times for http://www.apple.com/ at depth 1

| Threads Count | executionTime | pagesCrawled | seconds/page |
|--------------:|--------------:|-------------:|-------------:|
|              1|       1722.648|          1572|         1.100|
|              2|        951.568|          1572|         0.605|
|              4|        706.204|          1572|         0.449|
|              8|        651.317|          1572|         0.414|
|             16|        630.067|          1571|         0.401|
