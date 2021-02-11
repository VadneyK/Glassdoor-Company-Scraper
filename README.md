# Disclaimer

This scraper is provided as a public service because Glasdoor doesn't have a public API for searching overviews and collecting data. Glassdoor TOS prohibits scraping and I make no representation that your account won't be banned if you use this program. Furthermore, should I be contacted by Glassdoor with a request to remove this repo, I will do so immediately.

Additionally the program uses a manually designed heuristic to determine the legetimacy and closeness of the result to the search. Please view developer notes in the jupyter notebook for more detail. Use at your own descretion and feel free to fork and improve the code.

# Introduction

Have you ever wanted to scrape company information from a list of company names on Glassdoor, but bemoaned the site's lack of a public API? Worry no more! This script will go through pages and pages of company profiles and scrape lots of data into a tidy JSON file. Pass it a jsonlist as formatted in the example, and set a limit to scrape the 25 most conveniently available reviews!

It took about 11 seconds to find and collect information per company on average. So it will take about 3 hours to scrape 1,000 reviews during the day. However, I was blocked at search #650 so be careful. After restarting and entering the captcha and running the scraper through 12AM to 8AM, about 5000 entries were checked. This script's speed depends on the wifi network and requires patience. 😁

# Use Cases

You could defenitely use this for social science research using data from companies in glassdoor! (**hint hint university researchers**)

# Why Selenium

Alternatives like Scrapy and BeautifulSoup aren't able to interact with AJAX requests like typing in values and clicking buttons. For the sake of simplicity Selenium was used for all scraping. However utilizing a seperate library for purely scraping from the collected links and using parallelization may speed up the scraper.

# Installation

First, make sure that you're using Python 3.

1. Clone or download this repository.
2. Install virtualenv to set up a virtual environment if necessary with:

   `pip install virtualenv`

   Setting up a virtual environment ensures dependencies for this program don't mess with dependencies of other programs you may have. You could run this program withou steps 2 and 3 but it is not recommended.

3. Set up and activate a virtual environment by opening terminal to this file directory, then enter:
   1. `python3 -m venv env`
   2. `source env/bin/activate`
4. Run `pip3 install -r requirements.txt` inside this repo.
5. Use [this](https://www.edureka.co/community/52315/how-to-setup-chrome-driver-with-selenium-on-macos) or [this](https://zwbetz.com/download-chromedriver-binary-and-add-to-your-path-for-automated-functional-testing/) tutorial to Install [Chromedriver](http://chromedriver.chromium.org/) in to your PATH.
6. Go to the bottom of 'glassdoorScraper.py' and enter your glassdoor user name one line 426, replaceing the '' after 'username': in the JSON object, and enter your password in the quotes ('') after 'password': in the JSON object.
7. If you are using the jupyter notebook enter your glassdoor account username and password in the same manner in cell 39. I HIGHLY recommend you make a dummy glassdoor account as you may be blocked.
8. If using the jupyter notebook, run all cells.
9. if using the .py file, type `python3 glassdoorScraper.py` into the command line in this directory.

## Setting up the input data:

Now you need to format the input data, which is a list of the names of the companies you want to find. look at 'gvkey_salary_company.jsonl' for an example of how to set this up.

Enter your data on each line as a JSON object in the following format:
`{"name":"AAR CORP","longname":"AAR Corp","gvkey":"001004","capiq-ticker":"AIR"}`

if you dont have the company identified gvkey, you can exclude it, but you must enter all other values or this function will not run.

## Output

taskOne.json - Contains the JSON object of the jsonl object you inputted in 'gvkey_salary_company.jsonl' with the link to the glassdoor overview page of that company.

taskTwo.json - Contains the JSON object of the jsonl object you inputted in 'gvkey_salary_company.jsonl' with the link to the glassdoor overview page of that company, as well as scraped information from that page.

# Note

1. The .py and jupyter notebook contain my dummy account username and passwords. Please do delete my dummy user information if distributing this program to other users.
2. You may need to raise your 'JSON: Max Items Computed' settings to 999999 if viewing the output file in VSCode. The setting controls the maximum number of outline symbols and folding regions computed (limited for performance reasons).
3. Most functions are used statically and this project is small, so in the pythonic spirit all functions are simply defined by itself without class wrappers

# Time Taken

Task 1 - total 18 hours

- 3 hour: developing the interactive portion & cleaning data.
- 15 hours: developing and testing the heuristic for legitimacy (debugging and testing required watching scraper choose links, which was very slow and took a while to find many cases).

Task 2 - total 4 hours

- 4 hours: implementing the task data collection and json input/outputs.

# Next Steps

1. The 'check_public' method was made to check if a company is public, but too many publicly tradedd companies are falsely labeled on glassdoor so this function is turned off. Perhaps I could determine if the company is public some other way.
2. If there are cases where sketchy pages with few reviews and no images are found, perhaps we can avoid these by setting a minimum score to accept an input only above a certrain ligitimacy level.
3. Having a non-default image for the company profile could be used as a factor of determining the company page ligitimacy heuristic.
4. Perhaps we could tokenize the words that make up the company and classify the name into a theme (like 'airplane company' for 'ASA airlines') then also classify the profile image to ensure the most similar result is found.
