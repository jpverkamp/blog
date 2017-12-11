---
title: Wombat IDE - Line counter
date: 2011-09-13 04:59:08
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: line-counter
---
Minor coding-wise, but pretty important addition today:

<!--more-->

{{< figure src="/embeds/2011/line-count.png" >}}

If you don't see it, look on the right end of the toolbar. We now have a line/column count. What I really wanted was a column of line numbers down the left side of the text area and I actually have a version of that working. The problem was that it didn't necessarily work well with the code that allows for font size changes. When the font size changed, the line height wouldn't always change, causing strange visual artifacts. Since I couldn't work around that issue, I just added the line:column counter as shown. Hopefully, I can go back later and fix this in the future.