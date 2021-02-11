import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import pandas as pd
import numpy as np
import nltk

import jsonlines
import json
import csv


# Get all data we need to search the company from files

name = []
longName = []
ticker = []

with open('gvkey_salary_company_seeds.jsonl') as reader:
    for line in reader:
        company = json.loads(line)
        
        name.append(company['name'])
        longName.append(company['longname'])
        ticker.append(company['capiq-ticker'])       
        
# Process out the legal words from the 'long name' to get common names

common = pd.Series(longName)

with open('legal.csv', newline='') as legal:
    reader = csv.reader(legal)
    legalTerms = list(reader)[0][1:]
    
    
    #Special case for words with '(The)'
    common = common.apply(lambda x: 'The ' + x.replace('(The)', '') if '(The)' in x else x)
    
    for term in legalTerms:
        common = common.apply(lambda x: x.replace(term, '') if (type(x)==str and x.endswith(term)) else x)

#Now we begin the search for seeds. below are helper functions to help divide up the task.

def sign_in(browser, args):
    url = 'https://www.glassdoor.com/profile/login_input.htm'
    browser.get(url)
    time.sleep(.1)
    
    email_field = browser.find_element_by_name('username')
    password_field = browser.find_element_by_name('password')
    submit_btn = browser.find_element_by_xpath('//button[@type="submit"]')

    email_field.send_keys(args['username'])
    password_field.send_keys(args['password'])
    submit_btn.click()

    time.sleep(.5)
    browser.get(args['url'])

def search_word(browser, c):
    '''Accesses the search bar and inputs all information
    and submits the search.
    '''
    time.sleep(.1)
    keyword = browser.find_element(By.XPATH, '//*[@id="sc.keyword"]')
    keyword.clear()
    keyword.send_keys(c)
    time.sleep(.1)

    dropdown = browser.find_element(By.XPATH, '//*[@id="scBar"]/div/div[2]/div')
    dropdown.click()
    time.sleep(.1)

    selectCompany = browser.find_element(By.XPATH, '//*[@id="option_1"]')
    selectCompany.click()
    time.sleep(.1)

    #.clear() doesnt work so harcoded backspace
    location = browser.find_element(By.XPATH,'//*[@id="sc.location"]')
    for i in range(50):
        location.send_keys(Keys.BACK_SPACE)

    searchBtn = browser.find_element(By.XPATH,'//*[@id="scBar"]/div/button/span')
    searchBtn.click()
    time.sleep(.1)
    
    #Some times random pop ups come to block the scraper if the scraper goes too fast.
    #optionally uncomment below if this happens.

        #Test for the "Sign Up" prompt and get rid of it.
    # try:
    #     browser.find_element_by_class_name("selected").click()
    # except ElementClickInterceptedException:
    #     pass

    # time.sleep(.1)

    # try:
    #     browser.find_element_by_class_name("ModalStyle__xBtn___29PT9").click()  #clicking to the X.
    # except NoSuchElementException:
    #     pass

def find_match(browser, i, c):
    ''' finds company with name 'c' and returns link to most likely website of company 'c'
        
        Detail:
        searches through each result and checks how many times each result word matches
        with the ticker, longname, and company name. We choose the best candidates
        that match the most of these three, and determine the most likely legetimate
        site via heuristic getStat(<possible result>) and clicks on link. 
    '''
    results = browser.find_elements(By.CLASS_NAME,'single-company-result.module')

    similarNames = []
    similarStat = []
    matches = []
    
    # count matches
    for oneResult in results:
        resultName = oneResult.find_element(By.CLASS_NAME, 'col-9.pr-0')
        textLink = resultName.find_element(By.TAG_NAME, 'a')
        matchNum = checkAnyInLowerStrip(i, textLink.text)
        matches.append(matchNum)  
        
    matches = np.array(matches)
    if matches.size == 0:
        return ''
    maxMatch = max(matches)
    if maxMatch == 0:
        return ''
    else:
        # choose best stat out of best matches
        bestCandidates = np.where(matches == maxMatch)[0]
        for i in bestCandidates:
            candidate = results[i]
            oneOfBestName = candidate.find_element(By.CLASS_NAME, 'col-9.pr-0')
            textLink = oneOfBestName.find_element(By.TAG_NAME, 'a')
            similarNames.append(textLink)
            similarStat.append(getStat(candidate))
        similarNames[np.argmax(similarStat)].click()
        
        direct_name = browser.find_element(By.XPATH, '//*[@id="DivisionsDropdownComponent"]').text
        if check_public(browser, direct_name):
            time.sleep(.1)
            return browser.current_url
        else:
            return ''

def getStat(oneResult):
    '''gets a the mean of reviews, salaries, and interviews to determine how legitimite the company profile is.
    
    the mean is used since if there is only one metric that is strong (possibly due to spamming) then this is 
    discounted by taking the mean of all three values.
    '''
    
    stats = oneResult.find_elements(By.CLASS_NAME, 'num.h2')
    nums = []
    k = 1
    for s in stats:
        s = s.text.strip().replace('--', '0')
        if 'k' in s:
            s = s.replace('k', '')
            k = 1000 # we need to multiply by 1k = 1000
        numStat = float(s) * k
        nums.append(numStat)
        
    return np.mean(nums)
            
def check_redirect(browser, i, c):
    '''Occasioanlly the exact name of the comapany is entered, and we are taken to their page.
    In this case the company name may be different so we just check if either the display name
    is in what we're searching and vice versa.
    
    returns TRUE if there was a redirect
    '''
    try:
        direct_name = browser.find_element(By.XPATH, '//*[@id="DivisionsDropdownComponent"]').text
    except:
        return 'not redirect'

    # uncomment to track when a company is redirected
    # print('redirected to: ', direct_name, ' when searching: ', c)

    if direct_name and direct_name != ' ':
        if checkAnyInLowerStrip(i, direct_name):
            if check_public(browser, direct_name):
                return browser.current_url
    return 'fail'

# Logic for private words:
# - Non-profits may issue stock publicly in some states
# - Some franchises are publicly traded
# - Hospitals can be publicly traded
# - Contracting firms may be publicly traded
# - Subsidaries may be publicly traded
# - Other is ambiguous
    
#     Thus everything else in the list must be private

# https://www.glassdoor.com/mz-survey/start_input.htm?cr=&c=&showSurvey=Reviews

def check_public(browser, direct_name):
    '''all entries in JSONL files should be publicly traded.
    If any company is not publicly traded, return false
    else return true
    
    might need to adjust private words later.
    '''
    return True #many public companies are listed as private so turn off
    
    
    typeText = browser.find_element(By.XPATH, "//*[@data-test='employer-type']").text
    privateWords = ['Private', 'Government', 'College', 'School', 'Self']
    if any([p for p in privateWords if p in typeText]):
        print('Private Company found and ignored: ', direct_name)
        return ''
    else:
        return True

def get_seed_link(browser, i, c):
    '''gets the seed link of the 'i'th word, 'c'.
    if the link is found, appends it to seeds.
    otherwise appends ''.
    '''
    link_found = find_match(browser, i, c)
    if not link_found:
        return ''
    else:
        return link_found

def search(browser, i, c):
    '''searches the word in the search bar via search_word(c)
    then checks if there was a redirect via check_redirect
    finally gets seed link via get_seed_link
    '''
    try:
        search_word(browser, c)
        result = check_redirect(browser, i, c)
        if (result == 'not redirect'):
            return get_seed_link(browser, i, c)
        elif (result == 'fail'):
            return ''
        else:
            return result
        
    except Exception as e:
        return ''

def gather_seeds(browser, limit):
    '''iterates from entries at index start to end to search for the seed link
    appends '' if seed link not found.
    
    returns list of seed link
    '''
    
    
    reader = jsonlines.open('gvkey_salary_company_seeds.jsonl', mode='r')
    
    seed = ''
    taskOne = []
    taskTwo = []
    
    for index, company in enumerate(reader):
        if limit < 1:
            break
        seed = search(browser, index, longName[index])
        if not seed:
            seed = search(browser, index, common[index])
            #give up only after common name and long name does not work.
        company['gd-url'] = seed
        taskOne.append(company)
        
        if (seed != ''):
            collectTaskTwo(browser, taskTwo, company.copy())
            
        limit -= 1
        
    reader.close() 
    
    return taskOne, taskTwo


    ######## TOOLS @@@@@@@@@@@

def checkAnyInLowerStrip(i, word):
    ''' 
    checks if a the common name, long name, or ticker is in word, or vise versa when stripped 
    of spaces and punctuations and lower cased are contained in eachother.
    
    Note:
    After the first successfull pass, there were many instances where one search led to another
    version of the name popping up, but it was not caught as valid. This happened as redirects and
    normal searches.
    
    Additionally the cases of the words were messing with the accuracy so everything is in lower case.
    However, the search itself is in the original case because that tends to bring the most relavent to 
    the top. The punctuations are also removed.
    
    finally we get rid of spaces since some comapnies concatinate their company names on glass door.
    '''
    
    #strip all punctuation
    tokenizer = nltk.RegexpTokenizer(r"\w+")
    word = ''.join(tokenizer.tokenize(word)).lower()

    def normalizeAndCompare(c):
        c = ''.join(tokenizer.tokenize(c)).lower()
        return c in word or word in c
    
    check = [ticker[i], common[i], longName[i]]
    result = []
    
    for item in check:
        result.append(normalizeAndCompare(item))
        
    return sum(result)
    
### Now we input the URLs into the jsonl file
def writeToJson(writeList, dest):
    ''' Write writeList into dest.json as json object
    '''
    jsonObject = json.dumps(writeList, indent = 4)
    with open(dest + ".json", "w") as outfile: 
        outfile.write(jsonObject) 

def collectTaskTwo(browser, taskTwo, company):
    ''' Given output list taskTwo and a dict company
    to input information, collect Overview and Top bar 
    data into the comapny dict, then append to
    taskTwo list
    '''
    collectOverview(browser, company)
    collectTopBar(browser, company)
    taskTwo.append(company)

def collectOverview(browser, company):
    ''' Collect all information from the Overview pane on glassdoor.com
    '''
    infoSquare = browser.find_element(By.CLASS_NAME, 'css-155za0w.row.px-0.m-0')
    rows = infoSquare.find_elements(By.TAG_NAME, 'li')
    overview = {}
    
    # link formatted differently
    overview['website'] = rows[0].find_element(By.TAG_NAME, 'a').text 
    
    for info in rows[1:]:
        label = info.find_element(By.TAG_NAME, 'label').text 
        data = info.find_element(By.TAG_NAME, 'div').text 
        overview[label] = data
        
    company['Overview Data'] = overview

def collectTopBar(browser, company):
    ''' Collect all information on the top bar pane of glassdoor.com
    then , enter information into company dict
    '''
    name =''
    topBarData = {}
    
    infoBar = browser.find_element(By.ID, 'EIProductHeaders')
    links = infoBar.find_elements(By.TAG_NAME, 'a')
    
    # skip first link = overview page
    overview = links[0].get_attribute("href")
    for data in links[1:]:
        link = data.get_attribute("href")
        
        if 'Reviews' in link:
            review = link
        
        if 'FAQ' in link:
            name = 'FAQ'
        elif 'Location' in link:
            name = 'Location'
        elif 'Affiliated' in link:
            name = 'Affiliated'
        else:
            textData = data.find_elements(By.TAG_NAME, 'span')
            value = textData[0].text
            name = textData[1].text
            topBarData['Number of ' +name+ ' Posted'] = value
            
        topBarData[name + ' Link'] = link
        
    reviewCase(browser, company, review)

    company['Top bar Data'] = topBarData

def reviewCase(browser, company, link):
    ''' Go to the reviews page at link, and collect some simple statistics.
    Add this information into company
    '''
    reviews = {'Star score':'', 'Ceo Approval Rate':'', 'Recommend to Friend Rate':'', 'CEO Name':''}
    browser.get(link)
    try:
        starScore = browser.find_element(By.XPATH, '//*[@id="EmpStats"]/div/div[1]/div/div/div').text

        reviews['Star score'] = starScore
    except:
        #uncomment to be notified of a company without a star score
        #print(company['name'], ' does not have star score')
    try:
        ceo = browser.find_element(By.XPATH, '//*[@id="EmpStats"]/div/div[2]/div[3]/div/div[2]/div[1]').text
        reviews['CEO Name'] = ceo

        ratings = browser.find_elements(By.CLASS_NAME, 'donut__DonutStyle__donutchart_text_val')

        recommendToFriend = ratings[0].text
        reviews['Recommend to Friend Rate'] = recommendToFriend

        approveOfCeo = ratings[1].text
        reviews['Ceo Approval Rate'] = approveOfCeo
    except Exception as e:
        #uncomment to print comapnies without a donut value
        #print(company['name'], ' does not have donut values')
        
    company['Review Section Details'] = reviews

def main():
    browser = webdriver.Chrome(executable_path="/usr/local/bin/chromedriver")

    #enter username and password 
    args = {'username':'', 
            'password':'', 
            'url':'https://www.glassdoor.com/member/home/index.htm'}

    sign_in(browser, args)
    taskOne, taskTwo = gather_seeds(browser, 8000)
    writeToJson(taskOne, 'taskOne')
    writeToJson(taskTwo, 'taskTwo')
    browser.quit()

if __name__ == "__main__":
    main()