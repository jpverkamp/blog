---
title: Determining country by IP
date: 2012-10-24 14:00:51
programming/languages:
- Python
---
In my line of research, it's often useful to be able to identify where a country is using just it's IP address. I've done it a few different ways over the years, but the simplest I've found is using the <a href="http://www.maxmind.com/en/geolite" title="MaxMind GeoLite Country">MaxMind GeoLite Country database</a> directly. To speed such lookups, I've written a simple Python script that can run a whole series of such queries for you.

<!--more-->

Basically, the MaxMind "database" is a CSV file that contains the first and last IP in each range, those same IPs as an integer value, and then country code and country containing that IP range. So it's a simple matter to load all of the IPs into a list containing (first, last, country) tuples (using the integer versions to make comparisons quicker):

```python
ipdb = []
with open(ip_file, 'r') as fin:
    for line in fin:
        parts = [part.strip('"') for part in line.strip().split(',')]
        if len(parts) == 6:
            from_ip, to_ip, from_int, to_int, cc, country = parts
            ipdb.append((itn(from_int), int(to_int), country))
```

After that, it's a simple matter of scanning through input files. I added the ability to read stdin as a file as well by specifying the file '-' to match other Unix scripts.

```python
for file in files:
    if file == '-':
        fin = sys.stdin
    else:
        fin = open(file, 'r')

    for line in fin:
        ip = line.strip()
        if not ip: continue

        ip_int = ip_to_int(ip)
        answer = None
        for from_int, to_int, country in ipdb:
            if from_int <= ip_int <= to_int:
                answer = country
                break

        if not batch_mode:
            print('%s,%s' % (ip, answer))

        countries[answer] += 1

    fin.close()
```

And that's it. I could use a more intelligent data structure for the IP ranges, but honestly, it runs quickly enough. Perhaps sometime in the future. 

Here are a few cases of the script in action (using the default 'GeoIPCountryWhois.csv' in the same directory, using randomly generated IPs):

```python
~ ./country-by-ip.py ips.txt

242.73.117.31,None
148.132.51.11,United States
187.59.146.126,Brazil
155.152.27.52,United States
108.110.155.43,United States
175.147.205.217,China
222.68.15.191,China
35.184.64.198,United States
207.141.97.197,United States
154.254.107.40,None

~ ./country-by-ip.py --batch ips.txt

None,2
Brazil,1
China,2
United States,5
```

And that's all there is to it. Hope someone out there finds it useful, I sure did. 

If you'd like to download the entire source (with the setup and command line processing included), you can do so here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/country-by-ip.py" title="Country by IP source">country-by-ip source</a>.