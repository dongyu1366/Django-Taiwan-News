import json, requests, threading
from bs4 import BeautifulSoup
from datetime import datetime
from queue import Queue
from taiwan_news.models import News


class RequestHandler:

    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    }

    @classmethod
    def get_request(cls, url):
        res = None
        try:
            for i in range(3):
                res = requests.get(url=url, headers=cls.headers)
                res.raise_for_status()
                break
        except Exception as e:
            print(e)

        return res

    @classmethod
    def post_request(cls, url, data=None):
        res = None
        try:
            for i in range(3):
                res = requests.post(url=url, data=data, headers=cls.headers)
                res.raise_for_status()
                break
        except Exception as e:
            print(e)

        return res


class NewsCrawler:
    """
    1. Use API of focustaiwan to fetch list of news.
    2. The response, list of news contain title, abstract ,category etc.
    3. The most important is that it contain url link of the article page.
    4. Use each url to fetch the content of the news, then extract it.
    """

    NEWS_API = 'https://focustaiwan.tw/cna2019api/cna/FTNewsList/'
    CATEGORY = ('politics', 'cross-strait', 'business', 'society', 'sports', 'sci-tech', 'culture', 'ad')

    @classmethod
    def fetch_news(cls, category):
        payload = {'action': 4, 'category': category, 'pagesize': 100}

        res = RequestHandler.post_request(url=cls.NEWS_API, data=payload)
        if res.status_code == 200:
            data = json.loads(res.text)
            if data['Result'] == 'Y':
                news = data['ResultData']['Items']
                return news

    @staticmethod
    def modify_field_name(news_data):
        """
        Modify name of key to match the field name of models.
        Also remove unused key-value.
        """

        news_list = list()

        for item in news_data:
            item['token'] = item.pop('Id')
            item['category'] = item.pop('ClassName')
            item['title'] = item.pop('HeadLine')
            item['abstract'] = item.pop('Abstract')
            item['date'] = item.pop('CreateTime')
            item['image_url'] = item.pop('Image')
            item['page_url'] = item.pop('PageUrl')
            item.pop('Idx')
            item.pop('NewsTopicName')

            news_list.append(item)

        return news_list

    @staticmethod
    def insert_news_to_db(news_list):
        """
        The data is from list of news, so it does not cotain content.
        """

        bulk_list = list()

        for item in news_list:
            news = News.objects.filter(token=item.get('token'))
            if news:
                news.update(**item)
            else:
                obj = News(**item)
                bulk_list.append(obj)

        News.objects.bulk_create(bulk_list)

    @staticmethod
    def fetch_news_content(token, url, q, sema):
        """
        Get the url and make request to fetch content of news.
        Useing threads to make mutiple requests in the same time.
        But also use sema(threading.Semaphore) to limit amounts of requests.
        """

        sema.acquire()
        try:
            content = {'token': token, 'author': "", 'content': ""}
            res = requests.get(url=url)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                div_area = soup.find('div', class_='PrimarySide')
                paragraph = div_area.find('div', class_='paragraph')

                author_area = paragraph.find('div', class_='author')
                if author_area:
                    author_p = author_area.find_all('p')
                    for index, item in enumerate(author_p):
                        if index != 0:    
                            content['author'] += f"\n{item.text}"
                        else:
                            content['author'] += f"{item.text}"

                content_area = paragraph.find_all('p', recursive=False)
                if content_area:
                    for index, item in enumerate(content_area):
                        if index != 0:
                            content['content'] += f"\n{item.text}"
                        else:
                            content['content'] += f"{item.text}"

                q.put(content)
        except AttributeError as e:
            print(e, 'URL:', url)

        sema.release()

    @staticmethod
    def insert_news_content_to_db(content_list):
        """
        Generally, the news is already existed in the database.
        But it does not contain content, we update it now.
        """

        for item in content_list:
            token = item.get('token')
            author = item.get('author')
            content = item.get('content')
            news = News.objects.get(token=token)
            if news:
                try:
                    news.author = author
                    news.content = content
                    news.save()
                except Exception as e:
                    print(e)

    @classmethod
    def get_news(cls, category):
        news_data = cls.fetch_news(category=category)
        news_list = cls.modify_field_name(news_data=news_data)
        cls.insert_news_to_db(news_list=news_list)

        number = len(news_list)
        current_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        print(f"{current_time} - News List: Get {number} news from {category}")

    @classmethod
    def get_news_content(cls):

        # Query News that do not have content yet. 
        url_list = News.objects.filter(content__exact='').values_list('token', 'page_url')

        threads_list = list()
        sema = threading.Semaphore(value=30)
        q = Queue()

        for token, url in url_list:
            thread = threading.Thread(target=cls.fetch_news_content, args=(token, url, q, sema,))
            thread.start()
            threads_list.append(thread)

        for thread in threads_list:
            thread.join()

        # Get back news content from queue, then append to the news_content_list
        news_content_list = list()
        while not q.empty():
            news_content = q.get()
            news_content_list.append(news_content)

        cls.insert_news_content_to_db(content_list=news_content_list)

    @classmethod
    def run(cls):
        for item in cls.CATEGORY:
            cls.get_news(category=item)

        cls.get_news_content()
