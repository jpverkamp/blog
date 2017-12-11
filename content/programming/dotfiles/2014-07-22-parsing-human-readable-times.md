---
title: Parsing human readable times
date: 2014-07-22
programming/languages:
- PHP
programming/topics:
- Dotfiles
- Open Source
- Unix
---
So what day was 9 days ago again?

```bash
$ when 9 days ago

2014-07-13
```

<!--more-->

How do we do it?

Through the miracle of PHP[^1]!

```php
#!/usr/bin/env php
<?php
array_shift($argv);
$date_string = implode(' ', $argv);

date_default_timezone_set('America/Los_Angeles');
echo date('Y-m-d', strtotime($date_string)) . "\n";
```

One thing that PHP has going for it is a really nice date parsing function `strtotime`. Give it just about anything and it will turn it into a date.

`array_shift` is used to pop off the first argument, which is the name of the function. `implode` will stick the rest of the arguments together as a string rather than an array.

```bash
$ when last thursday

2014-07-17

$ when 2 months ago

2014-05-22
```

Particularly useful for the new style github interface. It's nice to have human readable dates in commit logs, but not always what I want.

The entire source code is in my [dotfiles]({{< ref "2015-02-11-update-dotfiles-encryption.md" >}}) repository: <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/when">when</a>.

[^1]: A phrase I never expected to utter