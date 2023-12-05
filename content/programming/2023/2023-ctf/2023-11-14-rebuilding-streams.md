---
title: Rebuilding Streams with TShark
date: 2023-11-14
programming/topics:
- CTF
- Security
- Exfiltration
- Networking
- TShark
- Wireshark
series:
- 2023 CTF Hints
---
Another quick post in a list of CTF techniques: filtering streams with [tshark](https://www.wireshark.org/docs/man-pages/tshark.html). tshark is the command line half of the packet capture tool [Wireshark](https://www.wireshark.org/). The advantage here is it let's you do all manner of filtering on the command line.

<!--more-->

## Example 1: Re-assembling a bittorrent download

For the first case, we're given a packet capture that contains a file someone is downloading using the [bittorrent](https://www.bittorrent.com/) protocol. Building a viable bittorrent client is an interesting idea all in it's own, but for now, all we really need is to filter some data. 

First, to filter the the capture so that we only have `bittorrent` data that contains a `piece` and it's associated `data`, you can:

```bash
$ tshark -2 -R 'bittorrent.piece.data' -r record.pcap -T json > record.json
```

That will take `record.pcap`, filter out anything that doesn't have `bittorrent.piece.data` and write it back out to a single JSON file. In this case, we can then use a quick script to take those pieces and re-assemble them:

```python
import json

with open('record.json') as f:
    packets = json.load(f)
    
pieces = {}
for packet in packets:
    bt = packet['_source']['layers']['bittorrent']['bittorrent.msg']
    
    length = bt['bittorrent.msg.length']
    index = bt['bittorrent.piece.index']
    begin = bt['bittorrent.piece.begin']
    hex_data = bt['bittorrent.piece.data']
    data = bytes.fromhex(hex_data.replace(':', ''))
    print(f'got piece at {index=}, {begin=}, {length=}, {len(data)=}')
    pieces[(index, begin)] = data
    
with open('output.mp3', 'wb') as f:
    for index, data in sorted(pieces.items()):
        print(f'writing at {index=}')
        f.write(data)
```

We (theoretically) could have duplicate pieces, ergo storing it in a hash (indexed by the `index` (which piece it is) and `begin` (which bytes they are) (I miss [[wiki:S-Expression]]() based languages sometimes)). Then sort and shove them into a file, and all is well.

## Example 2: DNS Based exfiltration

What if instead of someone downloading an interesting file, we have an attacker already on a client trying to exfiltrate some data. In this case, they might be using DNS to hide their data (it's rarely blocked outright, since doing that tends to break the internet). 

The same as before, we can exfiltrate the data with:

```bash
$ tshark -2 -R 'dns' -r wildcard.pcapng -T json | jq -rc '.[]._source.layers.dns' > wildcard.jsonl
```

This time, I'm using [jq](https://jqlang.github.io/jq/manual/) to further filter the packets and extract just the DNS data. Assuming the exfiltration is done by making DNS requests of the form `{start}-{end}-{hex encoded data}.example.com`, you can rebuild it much the same way as before:

```python

import json

packets = []

with open('wildcard.jsonl') as f:
    for line in f:
        packets.append(json.loads(line))

chunks = {}
for packet in packets:
    if packet['dns.count.answers'] != "1": 
        continue

    answer = packet['Answers']
    query = list(answer.keys())[0]
    name = query.split(':')[0]
    subdomain = name.split('.')[0]
    start, end, data = subdomain.split('-')
    start = int(start)
    end = int(end)
    data = bytes.fromhex(data)
    chunks[(start, end)] = data

with open('output', 'wb') as f:
    for (start, end), data in sorted(chunks.items()):
        f.write(data)
```

## Further work

The nice thing about all this is that there are *loads* of other protocols that could be hiding data in a CTF. 

You might see `HTTP` (or just boring `TCP` traffic).

`Telnet`. 

`ICMP` pings. 

`SNMP` if you need to go from one device to another on the same network. 

Database traffic.

The sky is the limit! 

And the same sort of tshark techniques work for all of them!