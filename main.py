import Mobile01Crawler as MCrawler
import time

def main():
    # topic_dict = MCrawler.GetAllTopic('https://www.mobile01.com/index.php')
    topic_dict = MCrawler.ReadTopic()

    print(u'Which topic would you want to crawl?')
    idx = input('Input the number in front of the topic (see topic_list.txt):').lstrip().rstrip()
    total_page_num = int(MCrawler.GetTotalPageNum(topic_dict[idx][0]))

    print(u'Topic {{ {} }} has {} pages in total.'.format(topic_dict[idx][1], total_page_num))
    page_want_to_crawl = input(u'How many pages do you want to crawl? ').lstrip().rstrip()
    if page_want_to_crawl == '' or not page_want_to_crawl.isdigit() or int(page_want_to_crawl) <= 0:
            print(u'EXIT')
    else:
        page_want_to_crawl = min(int(page_want_to_crawl), total_page_num)

        start = time.time()

        posts = MCrawler.GetPosts(page_want_to_crawl, topic_dict[idx][0])
        print(u'{} posts in total.'.format(len(posts)))

        posts_data = MCrawler.GetArticles(posts)

        print(u'Finish. Spend {} seconds on crawling.'.format(time.time()-start))

        ans = input('Save to database? [yes/no]:')
        if ans.lower() == 'yes':
            MCrawler.Save2DB('data.db', posts_data)
        ans = input('Save to excel? [yes/no]:')
        if ans.lower() == 'yes':
            MCrawler.Save2Excel(posts_data)
            

if __name__ == '__main__':
    main()