---
title: Ordering Board Game Geek GeekLists by Rank
date: 2021-06-28
programming/languages:
- Python
programming/topics:
- Small Scripts
programming/sources:
- APIs
- Board Games
- Board Game Arena
- Board Game Geek
---
A quick script.

I play a lot of board games. With the whole COVID-19 mess, I've been playing a lot on [Board Game Arena](https://boardgamearena.com/), which is a wonderful site. But one thing that's a bit lacking is having ratings / metadata about games to great games I've just not heard about before. Where can you get lots of that data? [Board Game Geek](https://boardgamegeek.com/)! 

The problem though, is merging the two. So, how do we do it? Well, this time around, I'm going to start with [this GeekList](https://boardgamegeek.com/geeklist/252354/list-games-board-game-arena) that someone else maintains of BGA games on BGG. Which has the games, but no ranks. And apparently there are no ways to rank those by BGG (for some reason). But that's easy when you know a bit of scripting!

<!--more-->

Relevant BGG APIs (yes, I know there's a version 2):

- [/xmlapi/geeklist/:id](https://boardgamegeek.com/wiki/page/BGG_XML_API&redirectedfrom=XML_API#toc7) - retrieve information about a GeekList
- [/xmlapi/boardgame/:id?stats=1](https://boardgamegeek.com/wiki/page/BGG_XML_API&redirectedfrom=XML_API#toc4) - without `stats=1`, you get lots of game information, but not the rankings

From there, I'm going to use some Python (it's what I know best), with [requests](https://docs.python-requests.org/en/master/) for fetching from the API and [xml.etree](https://docs.python.org/3/library/xml.etree.elementtree.html) for XML parsing. I swear there should be a more elegant way for the latter, but again, it works. 

Plug everything together and:

```python
import requests
import sys

from xml.etree import ElementTree as et

rankings = {}

for list in sys.argv[1:]:
    response = requests.get(f'https://www.boardgamegeek.com/xmlapi/geeklist/{list}')
    xml = et.fromstring(response.text)
    for item_el in xml.findall('item'):
        game_id = item_el.attrib['objectid']
        game_name = item_el.attrib['objectname']
        sys.stderr.write(f'Loading {game_name} ({game_id})\n')

        game_response = requests.get(f'https://www.boardgamegeek.com/xmlapi/boardgame/{game_id}?stats=1')
        game_xml = et.fromstring(game_response.text)

        for rank_el in game_xml.findall('.//rank'):
            try:
                rank_name = rank_el.attrib['friendlyname']
                rank_value = int(rank_el.attrib['value'])
            except ValueError:
                continue

            if rank_name not in rankings:
                rankings[rank_name] = []

            rankings[rank_name].append((rank_value, game_name))

for ranking, games in rankings.items():
    print(f'===== {ranking} =====')
    for i, (score, game) in enumerate(sorted(games), 1):
        print(f'{i: <5} {score: <5} {game}')
    print()
```

In summary:

- Fetch the geek list
- Iterate through `item` elements (these contain the items in the list)
    - For each, get the `objectid` (which is a game)
    - Fetch that game, including `stats=1`
    - For each list the game is on (overall, best strategy etc), store the ranking information
- Sort and print the information we collected

The first column is just numbering, the second is BGG rank overall within that category (so Through The Ages: A New Story of Civilization is the 8th highest ranked game on BGG as of now), and the last is the name. 

It's pretty nice:

```text
===== Board Game Rank =====
1     8     Through the Ages: A New Story of Civilization
2     16    Terra Mystica
3     17    7 Wonders Duel
4     28    Puerto Rico
5     39    The Crew: The Quest for Planet Nine
6     41    Tzolk'in: The Mayan Calendar
7     49    Clans of Caledonia
8     54    Through the Ages: A Story of Civilization
9     63    The Voyages of Marco Polo
10    65    Race for the Galaxy
...

===== Family Game Rank =====
1     3     The Crew: The Quest for Planet Nine
2     4     Lost Ruins of Arnak
3     9     7 Wonders
4     16    Stone Age
5     17    Welcome To...
6     22    Jaipur
7     29    Santorini
8     35    Carcassonne
9     39    Kingdomino
10    43    Nidavellir
...

===== Strategy Game Rank =====
1     8     Through the Ages: A New Story of Civilization
2     15    Terra Mystica
3     18    7 Wonders Duel
4     27    Puerto Rico
5     39    The Crew: The Quest for Planet Nine
6     41    Clans of Caledonia
7     42    Tzolk'in: The Mayan Calendar
8     47    Through the Ages: A Story of Civilization
9     50    Lost Ruins of Arnak
10    52    Teotihuacan: City of Gods
...

===== Abstract Game Rank =====
1     11    Santorini
2     13    Go
3     16    Hive
4     25    Taluva
5     29    Dragon Castle
6     35    Medina (Second Edition)
7     39    Tash-Kalar: Arena of Legends
8     46    Chess
9     51    Cribbage
10    52    Xiangqi
...

===== Party Game Rank =====
1     25    Skull
2     45    Coup
3     52    Perudo
4     56    Concept
5     75    Oriflamme
6     93    The Werewolves of Miller's Hollow
7     117   Saboteur
8     478   Scum: The Food Chain Game
9     572   Fluxx

===== Customizable Rank =====
1     73    Krosmaster: Arena

===== Thematic Rank =====
1     63    Dungeon Petz
2     173   K2
3     227   Rallyman: GT
4     303   Room 25
5     531   NOIR: Deductive Mystery Game
6     576   Penny Press

===== War Game Rank =====
1     25    Unconditional Surrender! World War 2 in Europe
2     65    Polis: Fight for the Hegemony

===== Children's Game Rank =====
1     132   Monster Factory
2     811   Connect Four
3     831   Battleship
```

I've played quite a few of these (and most of them were great!) but there are all sorts of ones I didn't even know were on BGA. All the games!

Next, I want to write something to scrape BGA (they don't have an official API, but that's workaroundable) and combine both data sets into something even better. The joys of scripting things. 