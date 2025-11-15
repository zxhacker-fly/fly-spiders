from fake_useragent import UserAgent

ua = UserAgent()

# 随机生成UA请求头
def random_headers():
    return {
        'User-Agent': ua.random
    }
