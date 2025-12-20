---
title: "Locking BGA tabs with UserScripts"
date: 2025-12-20
programming/languages:
- JavaScript
programming/topics:
- Userscripts
- Web Browsers
- Web Development
- MutationObserver
- Games
- Productivity
- Small Scripts
---
I play a lot of games on [Board Game Arena (BGA!)](https://boardgamearena.com/). A lot of those are turn based games with random people, but I have two subsets of games that I consider 'more important':

* Turn based games with people I know
* Alpha games I'm testing

Unfortunately, the first tends to have longer 'per turn' times and the latter doesn't have a timer at all, so both end up right at the very end of the sorted table list. But both, I'd rather play first and in-between other games. 

Super niche problems, I know. 

Generally, my solution has been to keep a tab open for each of those games in a Firefox Tab Group, but in those cases, I keep navigating off those pages accidentally (thank you next table button). 

Super *super* niche problems, now. 

In any case, I whipped up a quick userscript (I use ViolentMonkey) that will:

* Detect if a tab I'm on is one of the games I want to 'lock'
* Remove the next table button (buttons; there are two different ones)
* Disable navigation (at least make it pop up a warning)
* Periodically refresh the tab (BGA tends to go to sleep in the background)

<!--more-->

Voilà:

```javascript
// ==UserScript==
// @name         BGA Tab Locker
// @namespace    https://boardgamearena.com/
// @version      1.3
// @description  Lock specific Board Game Arena tables and prevent auto-navigation
// @match        https://boardgamearena.com/*
// @grant        none
// ==/UserScript==

(function () {
  ("use strict");

  const PAGE_REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes
  const LOCKED_TABLE_IDS = new Set(["8675309"]);

  let isRefreshing = false;

  console.debug("[BGA Tab Locker] Setting up load listener");
  window.addEventListener("load", () => {
    const tableID = new URLSearchParams(window.location.search).get("table");
    if (!tableID || !LOCKED_TABLE_IDS.has(tableID)) return;

    console.debug("[BGA Tab Locker] Locked table detected:", tableID);

    // Set up mutation observers on both IDs that any time those buttons change, hide them
    const hideElementById = (id) => {
      const targetNode = document.getElementById(id);
      if (!targetNode) return;

      const observer = new MutationObserver(() => {
        if (targetNode.style.display !== "none") {
          targetNode.style.display = "none";
          console.debug(
            `[BGA Tab Locker] Removed Next Table button from locked table (via MutationObserver on ${id})`
          );
        }
      });

      observer.observe(targetNode, {
        attributes: true,
        attributeFilter: ["style"],
      });

      targetNode.style.display = "none";
      console.debug(
        `[BGA Tab Locker] Removed Next Table button from locked table (initial hide on ${id})`
      );
    };
    hideElementById("go_to_next_table_inactive_player");
    hideElementById("go_to_next_table_active_player");

    // Periodically refresh the window
    setInterval(() => {
      console.debug("[BGA Tab Locker] Refreshing locked table");
      isRefreshing = true;
      window.location.reload();
    }, PAGE_REFRESH_INTERVAL);
  });

  // Block navigation attempts
  window.addEventListener("beforeunload", (event) => {
    const tableID = new URLSearchParams(window.location.search).get("table");
    if (!tableID || !LOCKED_TABLE_IDS.has(tableID)) return;
    if (isRefreshing) return;

    console.debug("[BGA Tab Locker] Blocking navigation from locked table");
    event.preventDefault();
    event.returnValue = "";
  });
})();
```

Basically, I set up a [MutationObserver](https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver) on both versions of the next table button (if it's your turn or not), hide them, and check if anything else modifies them--when they do, hide them again. 

And that's it!

I do have to modify the script to change the set of locked IDs whenever I want to add/remove them. I could probably inject a small API/button into the pages to do this instead. But this works well enough for now. 

Is this useful to absolutely anyone but me? Probably not. Was it neat to write? Absolutely!