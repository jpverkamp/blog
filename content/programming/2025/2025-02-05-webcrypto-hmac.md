---
title: "WebCrypto SHA-256 HMAC"
date: 2025-02-05
programming/languages:
- JavaScript
programming/topics:
- Web Crypto API
- Cryptography
- HMAC
- SHA-256
- Signing
series:
- Coding Quick Tips
---
A quick random thing I learned that I found helpful (and you might too!):

```javascript
async function hmac(text, secret) {
    let enc = new TextEncoder("utf-8");
    let algorithm = { name: "HMAC", hash: "SHA-256" };
    
    let key = await crypto.subtle.importKey("raw", enc.encode(secret), algorithm, false, ["sign", "verify"]);
    let signature = await crypto.subtle.sign(algorithm.name, key, enc.encode(text));
    let digest = btoa(String.fromCharCode(...new Uint8Array(signature)));

    return digest;
}
```

This is a function that uses the [Web Crypto API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Crypto_API) to calculate a [[wiki:SHA-256]]() [[wiki:HMAC]]() of a string given a secret value. 

I mostly worked this out so that I could figure out how *exactly* `TextEncoder` worked, along with `importKey` (to turn a secret into proper key material) and also how to convert that back into a hex digest.

```javascript
>> await hmac("lorem ipsum", "super secret")
"qArFX93Zi83ccIayhYnuFDpd4pk3eB4rZYDvNteobSU="

>> await hmac("lorem ipsum doler sit amet", "super secret")
"klTAioH5nNkguNhU2YcJshaZZtJW9DEb+MTqz4NWq8E="

>> await hmac("lorem ipsum", "even more super secret!")
"RoQLg2uz5KWLMJM72VExH5gZOls5bdZZyzHi678eDWs=" 

>> await hmac("lorem ipsum", "super secret")
"qArFX93Zi83ccIayhYnuFDpd4pk3eB4rZYDvNteobSU="
```

Disclaimer: This totally counts as rolling your own crypto. Don't do this unless you know what you're doing. :smile:

Disclaimer disclaimer: I only rarely know what I'm doing. :smile: :smile:

Also, for what it's worth, this is equivalent to the Python standard libraries' {{<doc python hmac>}} + {{<doc python base64>}}:

```python
>>> base64.b64encode(hmac.digest(b'super secret', b'lorem ipsum', 'SHA256')).decode()
'qArFX93Zi83ccIayhYnuFDpd4pk3eB4rZYDvNteobSU='
```

<!--more-->