import requests
import json
from bs4 import BeautifulSoup
import os
from tqdm import tqdm


def read_config():
    with open('config.json', 'r', encoding='utf-8') as file:
        # 读取JSON文件内容
        CONFIG = json.load(file)
    return CONFIG


def connect_class_main_web(class_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76",
        "Cookie": CONFIG["cookie"]
    }
    response = requests.get(class_url, headers=headers)
    if response.status_code == 200:
        return response


def get_class_list(class_main_web_response):
    response = class_main_web_response.json()
    print(response)
    print(len(response["activities"]))
    class_list = []
    for activity in response["activities"]:
        class_list.append(activity["id"])
    return class_list


def get_video_url(class_id):
    # step1. 拿到file_url
    print(class_id)
    activity_url = CONFIG["activity_url"].format(class_id)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76",
        "Cookie": CONFIG["cookie"]
    }
    response = requests.get(activity_url, headers=headers)
    if response.status_code == 200:
        video_json = response.json()
        video_url = video_json["video_suite"]["videos"][0]["file_url"]
        title = video_json["title"]
        return video_url, title


def download_video(url, filename):
    """
    从给定的URL下载视频并将其保存为本地文件。

    :param url: 视频的URL
    :param filename: 保存视频的本地文件名
    """
    response = requests.get(url, stream=True)
    if os.path.exists(filename):
        local_file_size = os.path.getsize(filename)
        remote_file_size = int(response.headers.get('content-length', 0))
        if local_file_size == remote_file_size:
            print("文件已存在且大小一致，无需下载。")
            response.close()
            return

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    print(url)
    # 检查请求是否成功
    if response.status_code == 200:
        total_size = int(response.headers.get('content-length', 0))
        chunk_size = 1024 * 1024  # 1MB per chunk
        with open(filename, 'wb') as file, tqdm(
                total=total_size / (1024 * 1024),
                unit='MB',
                unit_scale=True,
                unit_divisor=1024 * 1024,
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} MB [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
        ) as bar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                # 过滤掉保持连接的新的块
                if chunk:
                    file.write(chunk)
                    bar.update(len(chunk) / (1024 * 1024))
    else:
        print(f"请求失败，状态码：{response.status_code}")


def download_class_videos(class_list):
    for class_id in class_list:
        video_url, title = get_video_url(class_id)
        print(title)
        title = title.replace(':', '-')
        folder = title.split()[0]
        file_path = os.path.join(CONFIG["download_path"], folder, title + '.mp4')
        download_video(video_url, file_path)
        print(f'{title} done!')
        print('=' * 40)


if __name__ == '__main__':
    # learning-activity#/2158727
    CONFIG = read_config()
    url = CONFIG["url"]
    url = url.format(CONFIG["course_id"], CONFIG["page_size"])
    response = connect_class_main_web(url)
    class_list = get_class_list(class_main_web_response=response)
    download_class_videos(class_list)
