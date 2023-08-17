from selenium import webdriver
from bs4 import BeautifulSoup


driver = webdriver.Firefox()
def get_start_url(server, start=2020, end=2023) -> list:
    urls = list()
    for i in range(start, end+1):
        urls.append(f'{server}/loi/14698137/year/{i}')
    return urls


def main():
    server = 'https://nph.onlinelibrary.wiley.com'
    urls = get_start_url(server)
    headers = {"User-Agent":
               "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0"}
    for start_url in urls:
        driver.get(start_url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        print(soup.prettify())
        for a in soup.find_all('a'):
            if 'title' in a.attrs and a.attrs['title'].startswith('go to New Phytologist Volume'):
                print(server+a.href)


if __name__ == '__main__':
    main()