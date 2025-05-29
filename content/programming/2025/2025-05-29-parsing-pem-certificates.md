---
title: "Parsing PEM Certificates & ASN.1 in Javascript"
date: 2025-05-29
programming/languages:
- JavaScript
programming/topics:
- Cryptography
- HMAC
- SHA-256
- Signing
- Certificates
- Parsing
- ASN.1
- PEM
series:
- Coding Quick Tips
---
I recently had a conversation about parsing HTTPS/TLS/etc certificates client side (so that various values could be compared). There are, of course, [libraries](https://asn1js.org/) for that, but where's the fun in that? Let's dig in ourselves!

I thought of course it would be a well specified format and it wouldn't take more than a few minutes to parse... right?

Right?

{{<toc>}}

- - - 

<!--more-->

## Parsing

Okay, it's not as bad as all that. The outermost format we're dealing with is [[wiki:PEM|PEM]]. Those `-----BEGIN THING----` things. Inside of that, we have binary data that has been [[wiki:base64]]() encoded. 

So first, let's get the base64 decoding out of the way:

```javascript
// Parses a PEM-encoded certificate or key and returns an array of objects
function parsePEM(pem) {
  const pemRegex = /-----BEGIN ([A-Z ]+)-----([\s\S]+?)-----END \1-----/g;
  const matches = [...pem.matchAll(pemRegex)];
  return matches.map((match) => {
    const type = match[1];
    const base64 = match[2].replace(/\s+/g, "");
    const der = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
    return { type, der };
  });
}
```

This will find each certificate in a file ([[wiki:regex]]()!), pull out all whitespace, and then convert it to an array of bytes (`Uint8Array`). 

Now things get interesting. The binary is in the [[wiki:ASN.1]]() format, which is a tree structure packed into the binary. At each level, fields are encoded as `[Tag, Length, Value]`. 

The `Tag` is fairly well defined, see the [the constants](#constants) later. The first two bits define the 'class' of teh tag: universal, application, context-specific, or private. The next bit defines what kind it is: primitive (basic values like numbers) or constructed (a value that can have children, like sets and sequences). The rest is the actual tag itself. 

The `Length` field can either be a single byte (if < 127, thus the first bit is 0) or a multibyte encoding wherein the first bit is 0, the rest of the byte is how many bytes the full length takes up. There's also technically an 'indefinite form' (where you don't know the length), but for our cases here, we don't need that. 

And finally, the `Value`. For primitive types, this is just whatever bytes are stored in the next `Length` decoded in a variety of ways (see [decoding](#decoding-some-datatypes) later). 

For For some kinds of data (`constructed`), the `Value` is actually some number of child nodes. To parse those, we basically recursively parse the next object from our stream of bytes... up until we've used up `Value` of them total. We have no idea how many children we'll see or how deep it nests until we've done it. Interesting that. 

So to turn that all into code:

```javascript
// Reads an ASN.1 structure from a byte array and returns an object representation
// https://www.oss.com/asn1/resources/asn1-made-simple/asn1-quick-reference/basic-encoding-rules.html
function readASN1(data, offset = 0) {
  const start = offset;
  const tag = data[offset++];
  const lengthByte = data[offset++];
  let length;

  // Lengths > 127 are encoded as a multi-byte length
  if (lengthByte & 0x80) {
    const numBytes = lengthByte & 0x7f;
    length = 0;
    for (let i = 0; i < numBytes; i++) {
      length = (length << 8) | data[offset++];
    }
  } else {
    length = lengthByte;
  }

  const value = data.slice(offset, offset + length);

  // Tag classes are encoded in the high bits of the tag byte
  const tagClass = tag & 0x1f;

  // 'Constructed' tags have children (SET/SEQUENCE/etc)
  const isConstructed = (tag & 0x20) !== 0;
  let children = [];
  if (isConstructed) {
    let childOffset = 0;
    while (childOffset < value.length) {
      const child = readASN1(value, childOffset);
      children.push(child);
      childOffset += child.totalLength;
    }
  }

  return {
    tag,
    tagClass,
    isConstructed,
    length,
    totalLength: offset + length - start,
    value,
    children,
  };
}
```

It's kind of amazing how relatively 'complicated' of a file format can be packed like this. 

Now, this doesn't *by itself* give us enough information to decode a PEM, so...

## Decoding some datatypes

The next thing we'll want to do is write decoders for a few specific kinds of primitive `Value`. 

### Object Identifiers -- OIDs

First (and perhaps most important for PEMs), we have object identifiers. These are defined as their own hierarchical list of values, for example:

- `2 5 29 14` - `subjectKeyIdentifier`
- `2 5 29 15` - `keyUsage`
- `2 5 29 17` - `subjectAltName`
- `2 5 29 19` - `basicConstraints`
- `2 5 29 31` - `cRLDistributionPoints`
- `2 5 29 32` - `certificatePolicies`
- `2 5 29 35` - `authorityKeyIdentifier`
- `2 5 29 37` - `extKeyUsage`
- `2 5 4 10` - `organizationName`
- `2 5 4 11` - `organizationalUnitName`
- `2 5 4 3` - `commonName`
- `2 5 4 6` - `countryName`
- `2 5 4 7` - `localityName`
- `2 5 4 8` - `stateOrProvinceName`

So `2 5 29` is the general PEM stuff with specific values for specific keys. It's kind of handy that they can encode these as numeric values (rather than say, strings as JSON would do). Somewhat more compact. But because the actual *names* of these values aren't stored in the ASN.1 data itself... well, you just have to find a list. [Here is one](https://www.cs.auckland.ac.nz/~pgut001/dumpasn1.cfg) that I found useful for this project. 

So how do we decode OIDs?

```javascript
// Decodes an OID from a byte array and returns it as a string
function decodeOID(bytes) {
  const values = [];
  let value = 0;
  let first = true;

  for (let byte of bytes) {
    if (first) {
      values.push(Math.floor(byte / 40));
      values.push(byte % 40);
      first = false;
      continue;
    }
    value = (value << 7) | (byte & 0x7f);
    if ((byte & 0x80) === 0) {
      values.push(value);
      value = 0;
    }
  }

  return values.join(" ");
}
```

### Numbers

Next up, numeric values. The interesting one here is serial number in the certificate... which I don't seem to have decoded correctly. Because it's bigger then the integer size I'm using here, I expect. But I didn't really need this, so :shrug:. 

```javascript
// Decodes an integer from a byte array and returns it as a number
// TODO: This doesn't seem to be handling large values correctly
function decodeInteger(bytes) {
  let result = 0;
  for (let i = 0; i < bytes.length; i++) {
    result = (result << 8) | bytes[i];
  }
  return result;
}
```

### Dates

Next, we have dates: `UTCTime` and `GeneralizedTime`. The problem here is that the older `UTCTime` does this screwy thing where the year is only encoded as two bytes. If it's < 50, it's 20**, but more than and it's 19**. So of course `GeneralizedTime` properly uses 4 digits for the year. :smile:

It's interesting that they didn't just use [[wiki:Unix timestamps]]() for this, but so it goes. 

```javascript
// Decode datetime from a byte array
function decodeUTCTime(bytes) {
  const text = new TextDecoder().decode(bytes);
  const match = /^(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})?Z$/.exec(text);
  if (!match) {
    return `Invalid UTCTime: "${text}"`;
  }

  let [, yy, mm, dd, hh, min, ss = "00"] = match;

  // Handle 2-digit year
  const year =
    parseInt(yy, 10) < 50 ? 2000 + parseInt(yy, 10) : 1900 + parseInt(yy, 10);

  const date = new Date(
    Date.UTC(
      year,
      parseInt(mm, 10) - 1,
      parseInt(dd, 10),
      parseInt(hh, 10),
      parseInt(min, 10),
      parseInt(ss, 10)
    )
  );

  return date;
}

// Decode generalized time from a byte array
function decodeGeneralizedTime(bytes) {
  const text = new TextDecoder().decode(bytes);

  // Regex to parse: YYYYMMDDHHMMSS(.sss)?(Z|+hhmm|-hhmm)
  const regex =
    /^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\.\d+)?(Z|([+\-])(\d{2})(\d{2}))?$/;
  const match = regex.exec(text);
  if (!match) {
    return `Invalid GeneralizedTime: "${text}"`;
  }

  const [
    ,
    year,
    month,
    day,
    hour,
    minute,
    second,
    fraction = "",
    tz,
    tzSign,
    tzHour,
    tzMinute,
  ] = match;

  // Build date string for ISO 8601 parsing
  let iso = `${year}-${month}-${day}T${hour}:${minute}:${second}`;
  if (fraction) {
    iso += fraction;
  }

  if (!tz || tz === "Z") {
    iso += "Z";
  } else {
    iso += tzSign + tzHour + ":" + tzMinute;
  }

  const date = new Date(iso);

  if (isNaN(date)) {
    return `Invalid GeneralizedTime date: "${text}"`;
  }

  return date;
}
```

## Printing results

Okay, we have the data encoded as a giant nested Javascript object and some decoders in place, let's write a function that can actually print these things out for us:

```javascript
// Recursively prints an ASN.1 structure in a human-readable format
function printASN1(node, depth = 0) {
  const indent = "  ".repeat(depth);
  const tagNumber = node.tag & 0x1f;
  const tagName = ASN1_UNIVERSAL_TAGS[tagNumber] || `Tag(${tagNumber})`;

  let output = `${indent}- ${tagName}`;

  if (!node.isConstructed) {
    // Dump as hex, but truncate if too long
    const hex = [...node.value]
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
    const shortHex =
      hex.length > 32 ? hex.slice(0, 32) + "… (" + hex.length + " bytes)" : hex;
    if (shortHex.length > 0) {
      output += ` | Hex: ${shortHex}`;
    }

    // Attempt to decode as UTF-8 if possible
    let utf8 = null;
    try {
      utf8 = new TextDecoder().decode(node.value);
    } catch {}
    if (utf8 && /^[\x20-\x7E]*$/.test(utf8)) {
      output += ` | UTF-8: "${utf8}"`;
    }

    if (tagNumber === 0x02) {
      // INTEGER
      output += ` | Int: ${decodeInteger(node.value)}`;
    }

    if (tagNumber === 0x17) {
      // UTCTime
      const date = decodeUTCTime(node.value);
      output += ` | Date: ${date.toISOString()}`;
    }

    if (tagNumber === 0x18) {
      // GeneralizedTime
      const date = decodeGeneralizedTime(node.value);
      output += ` | Date: ${date.toISOString()}`;
    }

    if (tagNumber === 0x06) {
      // OBJECT IDENTIFIER
      let oid_value = decodeOID(node.value);
      if (KNOWN_OID_VALUES[oid_value]) {
        output += ` | OID: ${oid_value} (${KNOWN_OID_VALUES[oid_value]})`;
      } else {
        UNKNOWN_OID_VALUES[oid_value] = true;
        output += ` | OID: ${oid_value}`;
      }
    }
  }

  console.log(output);

  node.children.forEach((child) => printASN1(child, depth + 1));
}
```

The goal here is to keep track of what depth we're at recursively (so we can indent), then print out the tag type (see [constants](#constants)) and the data in as useful a form as we can. That takes the form of:

* Always include the hex value, but only up to the first 32 characters of it
* If we can successfully decode it as UTF8, print that (we could just process ones that have tag = `PrintableString` or something like that, but :shrug:)
* If it's one of a few known types, parse those and print them
* For values with children, recur into the children (one level depth'er)!

And... that's actually it!

Here's a wrapper to print any given variable `pem`:

```javascript
// Read certificate(s) from stdin
let fs = require("fs");
let pem = fs.readFileSync(0, "utf-8");

// Unknown OIDs will be collected here so we can add them to the above list later
let UNKNOWN_OID_VALUES = {};

// There might be multiple PEM in a file, collect them all
let blocks = parsePEM(pem);
for (const block of blocks) {
  console.log(`\n${block.type}`);
  const root = readASN1(block.der);

  // Print the ASN.1 structure in a (more or less) human-readable format
  printASN1(root);
}

// If we had any unknown OIDs, print them out
if (Object.keys(UNKNOWN_OID_VALUES).length > 0) {
  console.log("\nUnknown OIDs:");
  for (const oid of Object.keys(UNKNOWN_OID_VALUES)) {
    console.log(`- ${oid}`);
  }
}
```

## An example

So... let's actually do this thing. You can use `openssl` to download the certificate for any site and shove that into our decoder:

```bash
$ openssl s_client -connect www.google.com:443 -showcerts </dev/null | node decode-pem.js

CERTIFICATE
- SEQUENCE
  - SEQUENCE
    - Tag(0)
      - INTEGER | Hex: 02 | Int: 2
    - INTEGER | Hex: 00a3988120eb296bbf0a49e3e78d6a0d… (34 bytes) | Int: -1922429585
    - SEQUENCE
      - OBJECT IDENTIFIER | Hex: 2a864886f70d01010b | OID: 1 2 840 113549 1 1 11 (sha256WithRSAEncryption)
      - NULL
    - SEQUENCE
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 550406 | OID: 2 5 4 6 (countryName)
          - PrintableString | Hex: 5553 | UTF-8: "US"
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 55040a | OID: 2 5 4 10 (organizationName)
          - PrintableString | Hex: 476f6f676c6520547275737420536572… (42 bytes) | UTF-8: "Google Trust Services"
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 550403 | OID: 2 5 4 3 (commonName)
          - PrintableString | Hex: 575232 | UTF-8: "WR2"
    - SEQUENCE
      - UTCTime | Hex: 3235303432393139333030345a | UTF-8: "250429193004Z" | Date: 2025-04-29T19:30:04.000Z
      - UTCTime | Hex: 3235303732323139333030335a | UTF-8: "250722193003Z" | Date: 2025-07-22T19:30:03.000Z
    - SEQUENCE
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 550403 | OID: 2 5 4 3 (commonName)
          - PrintableString | Hex: 7777772e676f6f676c652e636f6d | UTF-8: "www.google.com"
    - SEQUENCE
      - SEQUENCE
        - OBJECT IDENTIFIER | Hex: 2a8648ce3d0201 | OID: 1 2 840 10045 2 1 (ecPublicKey)
        - OBJECT IDENTIFIER | Hex: 2a8648ce3d030107 | OID: 1 2 840 10045 3 1 7 (c2tnb191v3)
      - BIT STRING | Hex: 0004a86f2c5232a1076f7be91d3e208a… (132 bytes)
    - BIT STRING
      - SEQUENCE
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d0f | OID: 2 5 29 15 (keyUsage)
          - BOOLEAN | Hex: ff
          - OCTET STRING | Hex: 03020780
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d25 | OID: 2 5 29 37 (extKeyUsage)
          - OCTET STRING | Hex: 300a06082b06010505070301
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d13 | OID: 2 5 29 19 (basicConstraints)
          - BOOLEAN | Hex: ff
          - OCTET STRING | Hex: 3000
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d0e | OID: 2 5 29 14 (subjectKeyIdentifier)
          - OCTET STRING | Hex: 04144bc0c4f4b90afe972101a274c6c8… (44 bytes)
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d23 | OID: 2 5 29 35 (authorityKeyIdentifier)
          - OCTET STRING | Hex: 30168014de1b1eed7915d43e3724c321… (48 bytes)
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 2b06010505070101 | OID: 1 3 6 1 5 5 7 1 1 (authorityInfoAccess)
          - OCTET STRING | Hex: 304a302106082b060105050730018615… (152 bytes)
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d11 | OID: 2 5 29 17 (subjectAltName)
          - OCTET STRING | Hex: 3010820e7777772e676f6f676c652e63… (36 bytes)
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d20 | OID: 2 5 29 32 (certificatePolicies)
          - OCTET STRING | Hex: 300a3008060667810c010201
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d1f | OID: 2 5 29 31 (cRLDistributionPoints)
          - OCTET STRING | Hex: 302d302ba029a0278625687474703a2f… (94 bytes)
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 2b06010401d679020402 | OID: 1 3 6 1 4 1 11129 2 4 2 (googleSignedCertificateTimestamp)
          - OCTET STRING | Hex: 0481f300f1007700dddcca3495d7e116… (492 bytes)
  - SEQUENCE
    - OBJECT IDENTIFIER | Hex: 2a864886f70d01010b | OID: 1 2 840 113549 1 1 11 (sha256WithRSAEncryption)
    - NULL
  - BIT STRING | Hex: 0062c5c5eda9af6b5b0fb40aa342b635… (514 bytes)

CERTIFICATE
- SEQUENCE
  - SEQUENCE
    - Tag(0)
      - INTEGER | Hex: 02 | Int: 2
    - INTEGER | Hex: 7ff005a07c4cded100ad9d66a5107b98 | Int: -1525646440
    - SEQUENCE
      - OBJECT IDENTIFIER | Hex: 2a864886f70d01010b | OID: 1 2 840 113549 1 1 11 (sha256WithRSAEncryption)
      - NULL
    - SEQUENCE
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 550406 | OID: 2 5 4 6 (countryName)
          - PrintableString | Hex: 5553 | UTF-8: "US"
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 55040a | OID: 2 5 4 10 (organizationName)
          - PrintableString | Hex: 476f6f676c6520547275737420536572… (50 bytes) | UTF-8: "Google Trust Services LLC"
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 550403 | OID: 2 5 4 3 (commonName)
          - PrintableString | Hex: 47545320526f6f74205231 | UTF-8: "GTS Root R1"
    - SEQUENCE
      - UTCTime | Hex: 3233313231333039303030305a | UTF-8: "231213090000Z" | Date: 2023-12-13T09:00:00.000Z
      - UTCTime | Hex: 3239303232303134303030305a | UTF-8: "290220140000Z" | Date: 2029-02-20T14:00:00.000Z
    - SEQUENCE
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 550406 | OID: 2 5 4 6 (countryName)
          - PrintableString | Hex: 5553 | UTF-8: "US"
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 55040a | OID: 2 5 4 10 (organizationName)
          - PrintableString | Hex: 476f6f676c6520547275737420536572… (42 bytes) | UTF-8: "Google Trust Services"
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 550403 | OID: 2 5 4 3 (commonName)
          - PrintableString | Hex: 575232 | UTF-8: "WR2"
    - SEQUENCE
      - SEQUENCE
        - OBJECT IDENTIFIER | Hex: 2a864886f70d010101 | OID: 1 2 840 113549 1 1 1 (rsaEncryption)
        - NULL
      - BIT STRING | Hex: 003082010a0282010100a9ff9c7f451e… (542 bytes)
    - BIT STRING
      - SEQUENCE
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d0f | OID: 2 5 29 15 (keyUsage)
          - BOOLEAN | Hex: ff
          - OCTET STRING | Hex: 03020186
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d25 | OID: 2 5 29 37 (extKeyUsage)
          - OCTET STRING | Hex: 301406082b0601050507030106082b06… (44 bytes)
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d13 | OID: 2 5 29 19 (basicConstraints)
          - BOOLEAN | Hex: ff
          - OCTET STRING | Hex: 30060101ff020100
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d0e | OID: 2 5 29 14 (subjectKeyIdentifier)
          - OCTET STRING | Hex: 0414de1b1eed7915d43e3724c321bbec… (44 bytes)
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d23 | OID: 2 5 29 35 (authorityKeyIdentifier)
          - OCTET STRING | Hex: 30168014e4af2b26711a2b4827852f52… (48 bytes)
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 2b06010505070101 | OID: 1 3 6 1 5 5 7 1 1 (authorityInfoAccess)
          - OCTET STRING | Hex: 3026302406082b060105050730028618… (80 bytes)
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d1f | OID: 2 5 29 31 (cRLDistributionPoints)
          - OCTET STRING | Hex: 30223020a01ea01c861a687474703a2f… (72 bytes)
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d20 | OID: 2 5 29 32 (certificatePolicies)
          - OCTET STRING | Hex: 300a3008060667810c010201
  - SEQUENCE
    - OBJECT IDENTIFIER | Hex: 2a864886f70d01010b | OID: 1 2 840 113549 1 1 11 (sha256WithRSAEncryption)
    - NULL
  - BIT STRING | Hex: 0045758be51f3b4413961aab58f135c9… (1026 bytes)

CERTIFICATE
- SEQUENCE
  - SEQUENCE
    - Tag(0)
      - INTEGER | Hex: 02 | Int: 2
    - INTEGER | Hex: 77bd0d6cdb36f91aea210fc4f058d30d | Int: -262614259
    - SEQUENCE
      - OBJECT IDENTIFIER | Hex: 2a864886f70d01010b | OID: 1 2 840 113549 1 1 11 (sha256WithRSAEncryption)
      - NULL
    - SEQUENCE
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 550406 | OID: 2 5 4 6 (countryName)
          - PrintableString | Hex: 4245 | UTF-8: "BE"
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 55040a | OID: 2 5 4 10 (organizationName)
          - PrintableString | Hex: 476c6f62616c5369676e206e762d7361 | UTF-8: "GlobalSign nv-sa"
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 55040b | OID: 2 5 4 11 (organizationalUnitName)
          - PrintableString | Hex: 526f6f74204341 | UTF-8: "Root CA"
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 550403 | OID: 2 5 4 3 (commonName)
          - PrintableString | Hex: 476c6f62616c5369676e20526f6f7420… (36 bytes) | UTF-8: "GlobalSign Root CA"
    - SEQUENCE
      - UTCTime | Hex: 3230303631393030303034325a | UTF-8: "200619000042Z" | Date: 2020-06-19T00:00:42.000Z
      - UTCTime | Hex: 3238303132383030303034325a | UTF-8: "280128000042Z" | Date: 2028-01-28T00:00:42.000Z
    - SEQUENCE
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 550406 | OID: 2 5 4 6 (countryName)
          - PrintableString | Hex: 5553 | UTF-8: "US"
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 55040a | OID: 2 5 4 10 (organizationName)
          - PrintableString | Hex: 476f6f676c6520547275737420536572… (50 bytes) | UTF-8: "Google Trust Services LLC"
      - SET
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 550403 | OID: 2 5 4 3 (commonName)
          - PrintableString | Hex: 47545320526f6f74205231 | UTF-8: "GTS Root R1"
    - SEQUENCE
      - SEQUENCE
        - OBJECT IDENTIFIER | Hex: 2a864886f70d010101 | OID: 1 2 840 113549 1 1 1 (rsaEncryption)
        - NULL
      - BIT STRING | Hex: 003082020a0282020100b611028b1ee3… (1054 bytes)
    - BIT STRING
      - SEQUENCE
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d0f | OID: 2 5 29 15 (keyUsage)
          - BOOLEAN | Hex: ff
          - OCTET STRING | Hex: 03020186
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d13 | OID: 2 5 29 19 (basicConstraints)
          - BOOLEAN | Hex: ff
          - OCTET STRING | Hex: 30030101ff
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d0e | OID: 2 5 29 14 (subjectKeyIdentifier)
          - OCTET STRING | Hex: 0414e4af2b26711a2b4827852f52662c… (44 bytes)
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d23 | OID: 2 5 29 35 (authorityKeyIdentifier)
          - OCTET STRING | Hex: 30168014607b661a450d97ca89502f7d… (48 bytes)
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 2b06010505070101 | OID: 1 3 6 1 5 5 7 1 1 (authorityInfoAccess)
          - OCTET STRING | Hex: 3052302506082b060105050730018619… (168 bytes)
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d1f | OID: 2 5 29 31 (cRLDistributionPoints)
          - OCTET STRING | Hex: 30293027a025a0238621687474703a2f… (86 bytes)
        - SEQUENCE
          - OBJECT IDENTIFIER | Hex: 551d20 | OID: 2 5 29 32 (certificatePolicies)
          - OCTET STRING | Hex: 30323008060667810c01020130080606… (104 bytes)
  - SEQUENCE
    - OBJECT IDENTIFIER | Hex: 2a864886f70d01010b | OID: 1 2 840 113549 1 1 11 (sha256WithRSAEncryption)
    - NULL
  - BIT STRING | Hex: 0034a41eb128a3d0b47617a6317a21e9… (514 bytes)
```

Now... you have to actually step back a bit to PEM to determine what those values actually are, which isn't something that I needed for this particular project. But you can already see that the initial `CERTIFICATE` is always a `SEQUENCE` containing an ID, the signing type (RSA etc), some basic data as a `SEQUENCE` of `SEQUENCE` key/value pairs (countryName, etc), the valid from/valid to dates, etc. 

## Constants

In case it's useful, here are some tables that I built up as I was working on this. First, ASN.1 tags and classes and then a list of OID values that were useful for this specific work. These could certainly be fleshed out, but they're a good start!

```javascript
// https://www.oss.com/asn1/resources/asn1-made-simple/asn1-quick-reference/asn1-tags.html
const ASN1_UNIVERSAL_TAGS = {
  1: "BOOLEAN",
  2: "INTEGER",
  3: "BIT STRING",
  4: "OCTET STRING",
  5: "NULL",
  6: "OBJECT IDENTIFIER",
  7: "ObjectDescriptor",
  8: "EXTERNAL",
  9: "REAL",
  10: "ENUMERATED",
  11: "EMBEDDED PDV",
  12: "UTF8String",
  13: "RELATIVE-OID",
  14: "TIME",
  16: "SEQUENCE",
  17: "SET",
  18: "NumericString",
  19: "PrintableString",
  20: "TeletexString", // also known as T61String
  21: "VideotexString",
  22: "IA5String",
  23: "UTCTime",
  24: "GeneralizedTime",
  25: "GraphicString",
  26: "VisibleString",
  27: "GeneralString",
  28: "UniversalString",
  29: "CHARACTER STRING",
  30: "BMPString",
  31: "DATE",
  32: "TIME-OF-DAY",
  33: "DATE-TIME",
  34: "DURATION",
};

const TAG_CLASSES = {
  0: "UNIVERSAL",
  1: "APPLICATION",
  2: "CONTEXT-SPECIFIC",
  3: "PRIVATE",
};

// https://www.cs.auckland.ac.nz/~pgut001/dumpasn1.cfg
const KNOWN_OID_VALUES = {
  "1 2 840 10045 2 1": "ecPublicKey",
  "1 2 840 10045 3 1 7": "c2tnb191v3",
  "1 2 840 113549 1 1 1": "rsaEncryption",
  "1 2 840 113549 1 1 11": "sha256WithRSAEncryption",
  "1 2 840 113549 1 1 5": "sha1WithRSAEncryption",
  "1 3 6 1 4 1 11129 2 4 2": "googleSignedCertificateTimestamp",
  "1 3 6 1 5 5 7 1 1": "authorityInfoAccess",
  "2 5 29 14": "subjectKeyIdentifier",
  "2 5 29 15": "keyUsage",
  "2 5 29 17": "subjectAltName",
  "2 5 29 19": "basicConstraints",
  "2 5 29 31": "cRLDistributionPoints",
  "2 5 29 32": "certificatePolicies",
  "2 5 29 35": "authorityKeyIdentifier",
  "2 5 29 37": "extKeyUsage",
  "2 5 4 10": "organizationName",
  "2 5 4 11": "organizationalUnitName",
  "2 5 4 3": "commonName",
  "2 5 4 6": "countryName",
  "2 5 4 7": "localityName",
  "2 5 4 8": "stateOrProvinceName",
};
```