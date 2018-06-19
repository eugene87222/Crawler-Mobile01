import warnings
warnings.filterwarnings('ignore')

import re
import time
import requests
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

# 取得所有文章分類
def GetAllTopic(url):
	content = GetPageContent(url)

	all_topic = content.find('div', {'id':'top-menu'}).findAll('li')
	all_topic = [each for each in all_topic if 'topiclist' in each.find('a')['href'] or 'waypointtopiclist' in each.find('a')['href']]
	# ↑ 取得所有討論群組 (不包含綜合討論區)
	
	topic_list = list()
	for each in all_topic:
		topic_list.append((each.find('a')['href'], each.find('a').text))
	
	return topic_list

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
		# replace <br>, <br\> as a blank line ##################
		content = re.sub("<br\s*>", "§", content, flags=re.I)  #
		content = re.sub("<br\s*/>", "§", content, flags=re.I) #
		content = re.sub("\n+", "§", content, flags=re.I)      #
		content = re.sub("§+", "\n", content, flags=re.I)      #
		########################################################
		content = re.sub("<a\s+[^<>]+>(?P<aContent>[^<>]+?)</a>", "\g<aContent>", content, flags=re.I) # remove hyperlink
		content = BeautifulSoup(content)
		div = content.find('div')
		div.replace_with(div.text)
		content = content.text.lstrip().rstrip() # 把文章頭尾的空白都移除
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
