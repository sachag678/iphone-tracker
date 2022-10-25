# iphone-tracker

Contains the UI, Data Gathering and Data Processing code for the project.

Here is a blog post detailing the design and engineering process: [Blog](https://medium.com/@truble678/how-i-found-the-best-used-iphone-on-kijiji-ac8de854afa4)

Here is the link to active dashboard that is being updated everyday: [Dashboard](http://165.22.10.40:8080/)

## Data Gathering

Gets and saves html pages from kijiji based on the search term. Saves the pages in folders sorted by search term and date.

## Data Processing

Read the saved html pages, cleans them, extracts useful attributes for determining a good phone and saves them to a csv file. 

## UI

Analyses the processed csv files and displays average price over time, the percent difference from the actual retail price, the top 5 best phones
based on scores given to each phone based on a custom scoring calculation.
