# Youtube Metadata Scraper

This repo serves as an expansion over youtube-8m dataset in terms of metadata, the project aims to
scrap more metadata about the videos itself rather than data, such as views count, comments, etc.

The program takes a directory of your tf records that you have downloaded from youtube-8m dataset from
[here](https://research.google.com/youtube8m/download.html), and decodes them to get video urls to scrap them for
more data

## Setup

you need to have the tf records (video level) downloaed from youtube-8m dataset

```shell
pip install -r requirements.txt
```

## Linting

```shell
flake8
```

## How to Run

```shell
python main.py y8m_tf_records_data_directory
```
