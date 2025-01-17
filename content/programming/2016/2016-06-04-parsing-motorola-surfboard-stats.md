---
title: Parsing Motorola Surfboard stats
date: 2016-06-04
programming/languages:
- Python
---
A few weeks ago, I was having some pretty bad problems with my internet randomly hanging. Given that I'm now working from home, that wasn't exactly the most optimal of situations to find myself in, so I decided to dig a bit deeper. After a bit of looking, I found myself at my cable modem's built in web page:

{{< figure src="/embeds/2016/downstream.png" >}}

(This is after I fixed my problem. The values aren't perfect but they're much better.)

<!--more-->

There are three numbers here that are particularly interesting:


* `Signal to Noise Ratio` - >30 dB, although theoretically it can work as low as 25 dB at times; this one is fine
* `Downstream Power Level` - ±15 dbmV is supposed to be acceptable, but you really want no more than ±8 dbmV (that's why I said it's not great at the moment); I was getting -15 dbmV or worse consistently
* `Upstream Power Level` (not shown) - 37-55 dbmV, lower is generally better; I'm getting 47 dbmV, so once again fine


The nice thing about all of these numbers is that they are relatively easy to parse. All of the pages are a series of HTML tables, so I should be able to parse them relatively quickly with a combination of <a href="http://docs.python-requests.org/en/master/">Requests</a> to pull down the pages and <a href="https://www.crummy.com/software/BeautifulSoup/">Beautiful Soup</a> to parse them.

First, let's write a helper that can parse an table into a Python list of lists:

```python
def parse_table(table):
    '''Given soup <table>, extract the rows'''

    rows = []

    for tr in table.find_all('tr'):
        if not tr.find_all('td'):
            continue

        rows.append([
            td.text.strip()
            for td in tr.find_all('td')
            if td.text.strip()
        ])

    return rows
```

Then furthermore, let's assume the first row is a header row and turn them into a list of dictionaries:

```python
def lol_to_lod(table, transpose = False):
    '''Convert a list of lists with headers into a list of dicts.'''

    if transpose:
        table = list(zip(*table))

    headers = table[0]

    return [
        dict(zip(headers, row))
        for row in table[1:]
    ]
```

There's some magic going on there, `zip`ping the `headers` and `row` together to make a `dict` and transposing arrays via `list(zip(*table))`. It's perhaps not the most readable code ever, but it's amusing and compact. 

After that, it's just a matter of downloading each of the pages and doing a little bit of massaging the data to get it into a consistent form:

```python
def tables_for(endpoint):
    response = requests.get('http://192.168.100.1' + endpoint)
    soup = bs4.BeautifulSoup(response.text, 'lxml')
    return [parse_table(table) for table in soup.find_all('table')]


def status_page():
    tables = tables_for('/indexData.htm')

    result = {}
    result.update(lol_to_lod(tables[0], transpose = True)[0])
    result.update(lol_to_lod(tables[1], transpose = True)[0])
    return result

def signal_page():
    tables = tables_for('/cmSignalData.htm')
    tables[0][4][0] = 'Power Level'
    del tables[0][-1]
    del tables[0][-1][1]

    return {
        'downstream': lol_to_lod(tables[0], transpose = True),
        'upstream': lol_to_lod(tables[2], transpose = True),
        'codewords': lol_to_lod(tables[3], transpose = True),
    }

def addresses_page():
    tables = tables_for('/cmAddressData.htm')
    tables[1].insert(0, ['Index', 'MAC Address', 'Status'])

    result = lol_to_lod(tables[0], transpose = True)[0]
    result['clients'] = lol_to_lod(tables[1])

    return result

def configuration_page():
    tables = tables_for('/cmConfigData.htm')
    return lol_to_lod(tables[0][:-1], transpose = True)

def logs_page():
    tables = tables_for('/cmLogsData.htm')
    tables[0].insert(0, ['Time', 'Priority', 'Code', 'Message'])
    return lol_to_lod(tables[0])
```

It's a bit odd since each of the pages is actually one page containing another as an `iframe`, but a quick look into the source gets me all of the names. It's far more data than you probably actually need (and a good bit of it never changes), but you can always filter it after or compress the heck out of it (lines of mostly the same JSON compress very well; 90%+)

Combine everything into one more layer of Python `dict` and dump the whole thing as a JSON object.

```python
results = {
    'status': status_page(),
    'signal': signal_page(),
    'addresses': addresses_page(),
    'configuration': configuration_page(),
    'logs': logs_page(),
}

print(json.dumps(results))
```

Combined with the excellent <a href="https://stedolan.github.io/jq/">jq</a> to make it pretty:

```bash
$ modem-stats | jq '.'

{
  "signal": {
    "upstream": [
      {
        "Upstream Modulation": "[3] QPSK\n[3] 64QAM",
        "Ranging Status": "Success",
        "Channel ID": "79",
        "Symbol Rate": "5.120 Msym/sec",
        "Frequency": "21000000 Hz",
        "Ranging Service ID": "15160",
        "Power Level": "47 dBmV"
      },
      ...
    ],
    "codewords": [
      {
        "Total Unerrored Codewords": "9570874877",
        "Channel ID": "10",
        "Total Uncorrectable Codewords": "19826",
        "Total Correctable Codewords": "4667"
      },
      ...
    ],
    "downstream": [
      {
        "Signal to Noise Ratio": "36 dB",
        "Downstream Modulation": "QAM256",
        "Frequency": "663000000 Hz",
        "Power Level": "-9 dBmV",
        "Channel ID": "10"
      },
      ...
    ]
  },
  "addresses": {
    "Serial Number": "{redacted}",
    "clients": [
      {
        "Index": "1",
        "MAC Address": "{redacted}",
        "Status": "Dynamic"
      }
    ],
    "Ethernet MAC Address": "{redacted}",
    "HFC MAC Address": "{redacted}",
    "Ethernet IP Address": "192.168.100.1"
  },
  "status": {
    "Current Time and Date": "Jun 03 2016 23:25:32",
    "System Up Time": "2 days 10h:30m:54s",
    "DOCSIS Downstream Channel Acquisition": "Done",
    "Establish IP Connectivity using DHCP": "Done",
    "Initialize Baseline Privacy": "Done",
    "DOCSIS Ranging": "Done",
    "Register Connection": "Done",
    "Establish Time Of Day": "Done",
    "Transfer Operational Parameters through TFTP": "Done",
    "Cable Modem Status": "Operational"
  },
  "configuration": [
    {
      "Frequency Plan:": "North American Standard/HRC/IRC",
      "Upstream Channel ID:": "79",
      "Favorite Frequency (Hz)": "663000000",
      "Modem's IP Mode": "IPv6 Only",
      "Custom Frequency Ordering:": "Default",
      "DOCSIS MIMO": "Honor MDD IP Mode"
    }
  ],
  "logs": [
    ...
  ]
}
```

You can also use a bit of shell-fu to combine everything to get an average downstream power level at any given point in time:

```bash
$ modem-stats \
    | jq '.signal.downstream[]."Power Level"' \
    | tr -d '"' \
    | awk '{ sum += $1; count += 1 } END { print sum/count }'

-8.25
```

Combine that with a minutely cronjob and you can even detect when certain stats get particularly bad.

In the end, it was mostly a hardware issue. The coaxial cable I was using between the wall and my modem had a few kinks in it. I replaced with a newer, slightly shorter cable and all was well.

But still, it's interesting to have such statistics.

If you'd like to download the entire script, it's in my <a href="https://github.com/jpverkamp/dotfiles/">dotfiles</a>: <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/modem-stats">modem-stats</a>.
