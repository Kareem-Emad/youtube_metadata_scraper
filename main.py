import tensorflow as tf
import requests
import os
import argparse
import json
from bs4 import BeautifulSoup
# from google.protobuf.json_format import MessageToJson

tf.get_logger().setLevel('ERROR')


def get_real_id(random_id: str) -> str:
    url = 'http://data.yt8m.org/2/j/i/{}/{}.js'.format(random_id[0:2],
                                                       random_id)
    response = requests.get(url)
    real_id = response.text
    return real_id[real_id.find(',') + 2:real_id.find(')') - 1]


def extract_video_metadata_from_tf_records(tf_records_directory):
    tf_records_files = os.listdir(tf_records_directory)

    print(f"processing tf records from {tf_records_directory}")
    current_file_idx = 0

    for tf_file in tf_records_files:
        path = os.path.join(tf_records_directory, tf_file)
        try:
            for example in tf.compat.v1.io.tf_record_iterator(path):
                example = tf.train.Example.FromString(example)

                vid = {}
                vid['video_id'] = get_real_id(example.features.feature['id'].bytes_list.value[0].decode(encoding='UTF-8'))
                vid['y8_labels'] = example.features.feature['labels']
                print(f'video #{current_file_idx} produced\r')
                current_file_idx += 1
                yield vid

        except Exception as e:
            print(f"Failed while processing {tf_file} due to: {e}")


def scrap_video_page_content(soup, vid):
    div_s = soup.findAll('div')

    title = div_s[1].find('span', class_='watch-title')

    title = title.text.strip()
    vid['video_title'] = title

    channel_name = div_s[1].find(
        'a', class_="yt-uix-sessionlink spf-link").text.strip()
    channel_link = ('www.youtube.com' + div_s[1].find(
        'a', class_="yt-uix-sessionlink spf-link").get('href'))
    subscribers = div_s[1].find(
        'span',
        class_="yt-subscription-button-subscriber-count-branded-horizontal yt-subscriber-count" # noqa
    ).text.strip()

    vid['video_channel'] = channel_name
    vid['channel_link'] = channel_link
    vid['Channel_subscribers'] = subscribers

    Sp = div_s[1].text.split(':')
    video_category = None
    for j in range(len(Sp)):
        if 'category' in Sp[j]:
            video_category = Sp[j + 1].split(',')[0]

    vid['Category'] = video_category

    view_count = div_s[1].find(class_='watch-view-count')
    view_count = view_count.text.strip().split()[0]
    vid['video_views'] = view_count

    likes = div_s[1].find(
        'button',
        class_="yt-uix-button yt-uix-button-size-default yt-uix-button-opacity yt-uix-button-has-icon no-icon-markup like-button-renderer-like-button like-button-renderer-like-button-unclicked yt-uix-clickcard-target yt-uix-tooltip"  # noqa
    ).text.strip()
    vid['video_likes'] = likes

    dislikes = div_s[1].find(
        'button',
        class_="yt-uix-button yt-uix-button-size-default yt-uix-button-opacity yt-uix-button-has-icon no-icon-markup like-button-renderer-dislike-button like-button-renderer-dislike-button-unclicked yt-uix-clickcard-target yt-uix-tooltip"  # noqa
    ).text.strip()
    vid['video_dislikes'] = dislikes

    related_videos = div_s[1].findAll(
        'a', class_='content-link spf-link yt-uix-sessionlink spf-link')
    title_Related = []
    link_related = []

    for related_video in related_videos:
        title_Related.append(related_video.get('title'))
        link_related.append(related_video.get('href'))

    related_dict = dict(zip(title_Related, link_related))
    vid['Related_vids'] = related_dict
    return vid


def scrap_metadata_from_youtube(videos):
    youtube_base_url = "https://youtube.com/watch?v="
    expanded_videos = []

    print("expanding data from youtube")
    current_video_idx = 0
    try:
        for vid in videos:
            print(f'Processing video #{current_video_idx} \r')
            current_video_idx += 1

            url = youtube_base_url + vid['video_id']
            vid['video_url'] = url
            print(f'Processing video #{current_video_idx}  @ {url}\r')

            source = requests.get(url).text
            soup = BeautifulSoup(source, 'html.parser')

            try:
                vid = scrap_video_page_content(soup, vid)
            except Exception as e:
                print(f"cannot parse video from url {url} due to: {e}")

            expanded_videos.append(vid)
    except Exception as e:
        print(f"processing all videos failed due to: {e}")

    return expanded_videos


parser = argparse.ArgumentParser()
parser.add_argument("y8m_data", help="Directory path of your tf-records from Youtube-8M")
args = parser.parse_args()

videos = extract_video_metadata_from_tf_records(args.y8m_data)

expanded_videos = scrap_metadata_from_youtube(videos)

with open("videos.json", "w") as f:
    json.dump(expanded_videos, f)
