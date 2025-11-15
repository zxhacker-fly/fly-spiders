import os
import time

import requests
from parsel import Selector
from utils.random_headers import random_headers

# 拼接目标页码的URL
def make_url(page):
    """
    Target URLs:
    http://www.netbian.com/weimei/index_2.htm
    http://www.netbian.com/weimei/index_3.htm
    http://www.netbian.com/weimei/index_4.htm
    """
    base_url = 'http://www.netbian.com/weimei'
    if page == 1:
        return f'{base_url}/index.htm'
    else:
        return f'{base_url}/index_{page}.htm'

# 发起request请求，获取页面内容
def get_page_content(url):
    response = requests.get(url, headers=random_headers())
    response.encoding = 'gbk'  # 设置正确的编码格式
    return response.text

# 解析页面内容，提取图片列表
def parse_page(content):
    """
    Example detail URL:
        http://www.netbian.com/weimei/index.htm
        http://www.netbian.com/weimei/index_2.htm
    :param content:
    :return:
    """
    selector = Selector(text=content)
    items = selector.css('.list ul li')
    image_info_list = []
    for item in items:
        title = item.css('a::attr(title)').get()
        detail_url = 'http://www.netbian.com' + item.css('a::attr(href)').get()
        # 确保链接是以.htm结尾的壁纸详情页链接
        if title and detail_url and detail_url.strip().endswith('.htm'):
            image_info_list.append({'title': title.replace(" ","_"), 'detail_url': detail_url})
    return image_info_list


# 解析获取图片下载链接
def get_image_download_link(detail_url):
    """
    Example detail URL:
        http://www.netbian.com/desk/35457.htm
        http://www.netbian.com/desk/31116.htm
    :param detail_url: 壁纸详情页URL
    :return:
    """
    content = get_page_content(detail_url)
    selector = Selector(text=content)
    img_url = selector.css('.pic img::attr(src)').get()
    return img_url


# 下载图片
def down_image(img_url, title):
    """
    :param img_url: 图片下载链接
    :param title: 图片标题
    :return:
    """
    base_dir = 'images'
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    response = requests.get(img_url, headers=random_headers())
    with open(f'{base_dir}/{title}.jpg', 'wb') as f:
        f.write(response.content)
    print(f'Downloaded image: {title}')

# 主函数
def run(start_page=1, end_page=5):
    """
    :param start_page: 开始页码
    :param end_page: 结束页码
    :return:
    """
    for page in range(start_page,end_page):
        url = make_url(page)
        page_content = get_page_content(url)
        time.sleep(page) # 避免请求过于频繁
        print(f'Fetched page: {url}')
        images = parse_page(page_content)
        print(f'Fetched {len(images)} images')
        if not images:
            print("No images found, stop.")
            break
        for image in images:
            title = image['title']
            detail_url = image['detail_url']
            img_download_link = get_image_download_link(detail_url)
            print(img_download_link)
            down_image(img_download_link,title)
            
if __name__ == '__main__':
    run(65,68)