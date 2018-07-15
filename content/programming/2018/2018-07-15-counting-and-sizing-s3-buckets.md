---
title: Counting and Sizing S3 Buckets
date: 2018-07-15
programming/languages:
- Python
programming/topics:
- AWS
- AWS CloudWatch
- AWS S3
---
A long time ago in a galaxy far far away, I wrote up a script that I used to take an [AWS S3](https://aws.amazon.com/s3/) bucket and count how many objects there were in the bucket and calculate its total size. While you could get some of this information from billing reports, there just wasn't a good way to get it other than that at the time. The only way you could do it was to... iterate through the entire bucket, summing as you go. If you have buckets with millions (or more) objects, this could take a while.

Basically:

```python
conn = boto.connect_s3()
for bucket in sorted(conn.get_all_buckets()):
    try:
        total_count = 0
        total_size = 0
        start = datetime.datetime.now()

        for key in bucket.list_versions():
            # Skip deleted files
            if isinstance(key, boto.s3.deletemarker.DeleteMarker):
                continue

            size = key.size
            total_count += 1
            total_size += size

        print('-- {count} files, {size}, {time} to calculate'.format(
            count = total_count,
            size = humanize.naturalsize(total_size),
            time = humanize.naturaltime(datetime.datetime.now() - start).replace(' ago', '')
        ))
```

<!--more-->

Luckily, AWS later introduced [CloudWatch](https://aws.amazon.com/cloudwatch/) which has exactly the metrics I need to do this quickly. So rather than a script that takes days to run (and isn't exactly cheap, each access costs a fraction of a penny and I had to make a lot of them), we can make a handful of calls and have the entire output:

```python
#!/usr/bin/env python3

import boto3
import datetime

regions = ['us-east-1', 'us-west-2']
measurable_metrics = [
    ('BucketSizeBytes', 'StandardStorage'),
    ('NumberOfObjects', 'AllStorageTypes'),
]

s3 = boto3.resource('s3')

def cw(region, cws = {}):
    '''Caching Cloudwatch accessor by region.'''

    if region not in cws:
        cws[region] = boto3.client('cloudwatch', region_name = region)

    return cws[region]

def bucket_stats(name, date):
    '''Get the number object count and size of a bucket on a given date.'''

    results = {}

    for metric_name, storage_type in measurable_metrics:
        for region in regions:
            metrics = cw(region).get_metric_statistics(
                Namespace = 'AWS/S3',
                MetricName = metric_name,
                StartTime = date - datetime.timedelta(days = 365),
                EndTime = date,
                Period = 86400,
                Statistics = ['Average'],
                Dimensions = [
                    {'Name': 'BucketName', 'Value': name},
                    {'Name': 'StorageType', 'Value': storage_type},
                ],
            )

            if metrics['Datapoints']:
                results[metric_name] = sorted(metrics['Datapoints'], key = lambda row: row['Timestamp'])[-1]['Average']
                results['region'] = region
                continue

    return results

date = datetime.datetime.utcnow().replace(hour = 0, minute = 0, second = 0, microsecond = 0)

print('name', 'region', 'bytes', 'objects', sep = '\t')
for bucket in sorted(s3.buckets.all(), key = lambda bucket: bucket.name):
    results = bucket_stats(bucket.name, date)
    print(bucket.name, results.get('region'), int(results.get('BucketSizeBytes', 0)), int(results.get('NumberOfObjects', 0)), sep = '\t')
```

Even better, you can use this to get this information at any time or even over time, to find fast growing buckets. All of this information is directly available in the CloudWatch console, but some things are difficult to do in that particular interface (or were last I looked, it's been a few months), so it's always nice to be able to export your information.

The script also generalizes fairly well to other CloudWatch stats. It would require a bit of tweaking (for example changing the `Dimensions` parameter along with the `measurable_metrics` array), but it's entirely doable. Perhaps I'll post a few of the modifications I've made some day.
