# SI507_final_wiki
Scraping and Crawling Wikipedia

Data sources used:
  Scraping and crawling from Wikipedia search queries. Plots are drawn using Plotly,
  
  In order to use plotly:
    please refer to guidelines here: https://plot.ly/python/getting-started/

Code structure:
  Caching done in two phases: one for Wiki results and one for wiki edit page results
  Crawling done through edit pages using "next link" and recursive function named "crawl_to_next"
  Class 'SearchedWord" is listed in a list
  Class contains: keyword, word count list, edit dict
  Database created by collected web data
    Keyword ID (kw_id) is related to other database tables via foreign key
    
User guide:
  Please refer to typing '*help' after running the code. You can search by keyword, look up charts made from data from WIKI search and edit data, and view searched keyword history.
  
