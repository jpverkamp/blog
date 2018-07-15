---
title: Generating zone files from Route53
date: 2018-03-12
programming/languages:
- Python
programming/topics:
- AWS
- AWS Route53
- Boto3
- DNS
---
Recently I found myself wanting to do some analysis on all of our DNS entires stored in AWS's Route53 for security reasons (specifically to prevent subdomain takeover attacks, I'll probably write that up soon). In doing so, I realized that while Route53 has the ability to import a {{< wikipedia "zone file" >}}, it's not possible to export one.

To some extent, this makes sense. Since Route53 supports ALIAS records (which can automatically determine their values based on other AWS products, such as an ELB changing its public IP) and those aren't actually 'real' DNS entries, things will get confused. But I don't currently intend to re-import these zone files, just use them. So let's see what we can do.

<!--more-->

On one hand, this is made relatively easy by the use of [Boto3](https://boto3.readthedocs.io/en/latest/). On the other hand, the AWS API just doesn't have a way (so far as I've been able to tell) to fetch a Route53 zone by name (rather than by ID). So we have to iterate through them and skip any that we don't want. Inefficient, but what can you do...

```python
#!/usr/bin/env python3

import boto3
import sys

route53 = boto3.client('route53')

paginate_hosted_zones = route53.get_paginator('list_hosted_zones')
paginate_resource_record_sets = route53.get_paginator('list_resource_record_sets')

domains = [domain.lower().rstrip('.') for domain in sys.argv[1:]]

for zone_page in paginate_hosted_zones.paginate():
    for zone in zone_page['HostedZones']:
        if domains and not zone['Name'].lower().rstrip('.') in domains:
            continue

        for record_page in paginate_resource_record_sets.paginate(HostedZoneId = zone['Id']):
            for record in record_page['ResourceRecordSets']:
                if record.get('ResourceRecords'):
                    for target in record['ResourceRecords']:
                        print(record['Name'], record['TTL'], 'IN', record['Type'], target['Value'], sep = '\t')
                elif record.get('AliasTarget'):
                    print(record['Name'], 300, 'IN', record['Type'], record['AliasTarget']['DNSName'], '; ALIAS', sep = '\t')
                else:
                    raise Exception('Unknown record type: {}'.format(record))
```

The core of the code comes from the fact that there are two kinds of DNS entries that we want to export: `ResourceRecordSets` and `AliasTarget` (since they are structured differently). If you only want a true zone file, you would just remove the `elif` block.

And that's about it. Let's try a quick export:

```bash
$ python3 export-zone.py example.com

example.com.	300	IN	A	dualstack.www-example-123456789.us-west-2.elb.amazonaws.com.	; ALIAS
example.com.	172800	IN	NS	ns-495.awsdns-61.com.
example.com.	172800	IN	NS	ns-2010.awsdns-59.co.uk.
example.com.	172800	IN	NS	ns-789.awsdns-34.net.
example.com.	172800	IN	NS	ns-1311.awsdns-35.org.
example.com.	900	IN	SOA	ns-495.awsdns-61.com. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400
\052.example.com.	300	IN	CNAME	example.com
admin.example.com.	300	IN	A	dualstack.admin-example-123456789.us-west-2.elb.amazonaws.com.	; ALIAS
api.example.com.	300	IN	A	dualstack.api-example-123456789.us-west-2.elb.amazonaws.com.	; ALIAS
rdr.example.com.	300	IN	A	dualstack.rdr-example-123456789.us-west-2.elb.amazonaws.com.	; ALIAS
www.example.com.	300	IN	CNAME	example.com
```

And that's it. Onwards to actually digging through some 3000 DNS entries over 30 zones. Fun times.
