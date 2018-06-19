import Mobile01Crawler as MCrawler

def main():
    #topic_list = get_all_topic('https://www.mobile01.com/index.php')
    '''
    for each in topic_list:
        print(each)
        print(get_total_page_num(each[0]))'''
    print(GetTotalPageNum('topiclist.php?f=749'))

    page = 1

    posts = GetPosts(page, 'topiclist.php?f=749')

    print(len(posts))

    all_post_content = GetArticles(posts)
    
    print(len(all_post_content))
    
    print('==============')

if __name__ == '__main__':
    main()