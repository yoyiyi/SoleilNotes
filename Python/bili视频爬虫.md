```python
import requests, threading, re, json, os, time
from lxml import etree
from queue import Queue

headers = {
    'Connection': 'keep-alive',
    'Referer': 'https://www.bilibili.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'}

video_queue = Queue(100)


def single_data(url):
    resp = requests.get(url, headers=headers)
    html = etree.HTML(resp.text)
    title = html.xpath('//div[@id="viewbox_report"]/h1/@title')[0]
    print('下载：', title)

    data = re.search(r'__playinfo__=(.*?)</script><script>', resp.text).group(1)
    data = json.loads(data)
    try:
        time = data['data']['dash']['duration']
        minute = int(time) // 60
        second = int(time) % 60
        video_url = data['data']['dash']['video'][0]['baseUrl']
        audio_url = data['data']['dash']['audio'][0]['baseUrl']
        video_queue.put([video_url, audio_url, title])
    except KeyError:
        time = data['data']['timelength'] // 1000 
        minute = int(time) // 60  
        second = int(time) % 60
        video_url = data['data']['durl'][0]['url']
        video_queue.put([video_url, title])
    print('视频时长{}分{}秒'.format(minute, second))


# 定义下载函数(调用video_audio_merge合并生成的 音频+视频 文件)
def download():
    while not video_queue.empty():
        data = video_queue.get()
        if len(data) == 3:
            print('%s   开始下载' % data[2])
            data[2] = re.sub(r'[\\/:\*\?<>\|"]', '', data[2])
            with open('%s_video.mp4' % data[2], 'wb') as f:  # 视频部分
                resp = requests.get(data[0], headers=headers)
                f.write(resp.content)
            with open('%s_audio.mp4' % data[2], 'wb') as f:  # 音频部分
                resp = requests.get(data[1], headers=headers)
                f.write(resp.content)
            video_audio_merge(data[2])
        else:
            data[1] = re.sub(r'[\\/:\*\?<>\|"]', '', data[1])
            with open('%s_video.mp4' % data[1], 'wb') as f:  # 只有视频部分
                resp = requests.get(data[0], headers=headers)
                f.write(resp.content)
                f.close()
                print('%s下载完成' % data[1])

        os.remove("%s_video.mp4" % data[2])
        os.remove("%s_audio.mp4" % data[2])


# 定义将视频和音频合并的函数(需要调用ffmpeg程序)
def video_audio_merge(video_name):
    print("视频合成开始：%s" % video_name)
    import subprocess
    command = 'ffmpeg -i "%s_video.mp4" -i "%s_audio.mp4" -c copy "%s.mp4" -y -loglevel quiet' % (
        video_name, video_name, video_name)
    dd = subprocess.Popen(command)
    if dd.wait() == 1:
        print("视频合成结束：%s" % video_name)
    # os.remove("%s_video.mp4" % video_name)
    # os.remove("%s_audio.mp4" % video_name)


# 定义主函数
def main():
    url = input('输入下载链接（例如：https://www.bilibili.com/video/av91748877?p=1,https://www.bilibili.com/video/av91748877?p=2)多视频请用英文逗号分隔:\n')
    urls = url.split(',')
    for each in urls:
        single_data(each)  # 调用single_data函数
        time.sleep(1)
    for x in range(3):
        th = threading.Thread(target=download)  # 调用download函数(进一步调用video_audio_merge子程序)
        th.start()


if __name__ == '__main__':
    main()
```

