import warnings
warnings.filterwarnings('ignore')

import re
import time
import sqlite3
import requests
from pandas import DataFrame
from bs4 import BeautifulSoup
from multiprocessing import Pool

##########################################
# get the html code with given url       #
# param: url -> url of the web page      #
##########################################
def GetPageContent(url):
    res = requests.get(url)
    content = BeautifulSoup(res.text)
    return content

#########################################
# get all topics and save as a txt file #
# param: url -> url of the home page    #
#########################################
def GetAllTopic(url):
    content = GetPageContent(url)

    all_topic = content.find('div', {'id':'top-menu'}).findAll('li')
    all_topic = [each for each in all_topic if 'topiclist' in each.find('a')['href'] or 'waypointtopiclist' in each.find('a')['href']]
    
    file = open('topic_list.txt', 'w')
    topic_dict = dict()
    idx = 0
    for each in all_topic:
        topic_link = each.find('a')['href']
        topic_page = GetPageContent('https://www.mobile01.com/' + topic_link)
        nav = topic_page.findAll('p', {'class':'nav'})[0].text
        start = nav.find('»')
        topic_name = nav[start+1:].lstrip().rstrip()
        while ' » ' in topic_name:
            topic_name = topic_name.replace(' » ', '>')
        while ' ' in topic_name:
            topic_name = topic_name.replace(' ', '')

        topic_dict[str(idx)] = [topic_link, topic_name]
        file.write(str(idx) + ' ' + topic_link + ' ' + topic_name + '\n')
        idx += 1

    file.close()
    return topic_dict

#################################
# read topic list from txt file #
#################################
def ReadTopic():
    topic_dict = dict()
    file = open('topic_list.txt', 'r')
    for line in file:
        topic = line.replace('\n', '').split(' ')
        topic_dict[topic[0]] = [topic[1], topic[2]]
    file.close()
    return topic_dict

# 取得該分類文章總頁數
def GetTotalPageNum(url):
    content = GetPageContent('https://www.mobile01.com/' + url)
    pagination = content.findAll('div', {'class':'pagination'}) # "[1][2][3]...下一頁"這行
    if pagination:
        page_link = pagination[1].findAll('a')
        if page_link:
            last_page = page_link[-1]['href']           # 該行的最後一個按鈕就是最後一頁的網址
            replace = url+'&p='
            total_page = last_page.replace(replace, '') # 把前面的字串過濾掉，只要網址後面的數字 (頁數)
        else:
            total_page = 1
    else:
        total_page = -1
    return total_page

# 取得從第 1 頁到第 page_num 頁的所有文章網址
def GetPosts(page_num, url):
    posts = list()

    for i in range(1, 1 + page_num):
        content = GetPageContent('https://www.mobile01.com/' + url + '&p=' + str(i))

        table = content.find('table', {'summary':u'文章列表'})
        rows = table.findAll('tr')[1:]  # 每篇文章連結都是包在 table 的 tr 裡面
        
        for row in rows:
            meta = row.find('a', {'class':'topic_gen'})
            if meta:
                link = meta['href']     # 文章網址
                title = meta.text       # 文章標題
                reply = row.find('td', {'class':'reply'}).text  # 回覆量
                detail = row.find('td', {'class':'authur'})
                detail = detail.findAll('p')
                date = detail[0].text   # 文章發布日期
                author = detail[1].text # 文章作者
                
                posts.append({
                    'link': link,
                    'title': title,
                    'date': date,
                    'author': author,
                    'reply': reply
                })

    return posts

#################################
# get the article of the post   #
# param: url -> url of the post #
#################################
def ParseGetArticle(url):
    soup = GetPageContent('https://www.mobile01.com/' + url)
    origin = soup.find('div', {'class':'single-post-content'}) # 文章內文在 <div class="single-post-content"> 底下
    if origin:
        content = str(origin)
        # replace <br>, <br\> and '\n' with a whitespace########
        content = re.sub("<br\s*>", " ", content, flags=re.I)  #
        content = re.sub("<br\s*/>", " ", content, flags=re.I) #
        content = re.sub("\n+", " ", content, flags=re.I)      #
        ########################################################
        # remove hyperlink
        content = re.sub("<a\s+[^<>]+>(?P<aContent>[^<>]+?)</a>", "\g<aContent>", content, flags=re.I)
        content = BeautifulSoup(content)
        content = ' '.join(content.text.lstrip().rstrip().split())
    else:
        content = 'None'

    return content

##############################################
# get the articles of each post              #
# param: post_list -> mata data of all posts #
##############################################
def GetArticles(post_list):
    post_link = [entry['link'] for entry in post_list]

    articles = list()

    for i in range(len(post_list)):
        articles.append({
            'title': post_list[i]['title'], 
            'link': post_list[i]['link'], 
            'date': post_list[i]['date'],
            'author': post_list[i]['author'], 
            'reply': post_list[i]['reply'], 
            'content': ParseGetArticle(post_list[i]['link'])
        })

    return articles

##########################################
# save data into SQLite database         #
# param: db_name -> name of the database #
#        posts -> posts data             #
##########################################
def Save2DB(db_name, posts):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    create_table = """ CREATE TABLE IF NOT EXISTS table1(
                        ID integer PRIMARY KEY,
                        title text NOT NULL,
                        link text NOT NULL,
                        date text NOT NULL,
                        author text NOT NULL,
                        reply text NOT NULL,
                        content text NOT NULL
                        ); """
    cur.execute(create_table)
    for i in posts:
        cur.execute("insert into table1 (title, link, date, author, reply, content) values (?, ?, ?, ?, ?, ?)",
            (i['title'], i['link'], i['date'], i['author'], i['reply'], i['content']))
    conn.commit()
    conn.close()

##############################
# save data into excel       #
# param: posts -> posts data #
##############################
def Save2Excel(posts):
    titles = [entry['title'] for entry in posts]
    links = [entry['link'] for entry in posts]
    dates = [entry['date'] for entry in posts]
    authors = [entry['author'] for entry in posts]
    replies = [entry['reply'] for entry in posts]
    contents = [entry['content'] for entry in posts]
    df = DataFrame({
        'title':titles,
        'link':links,
        'date': dates,
        'author':authors,
        'reply': replies,
        'content': contents
        })
    df.to_excel('data.xlsx', sheet_name='sheet1', index=False, columns=['title', 'link', 'date', 'author', 'reply', 'content'])