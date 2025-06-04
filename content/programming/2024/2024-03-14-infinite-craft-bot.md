---
title: "Infinite Craft Bot"
date: 2024-03-14
programming/languages:
- Python
programming/topics:
- Algorithms
- Search
- Breadth First
- Graph Theory
---
You've probably seen [Neil.fun](https://neil.fun)'s [Infinite Craft](https://neal.fun/infinite-craft/) game somewhere on the internet. If not, in a nutshell:

* You start with 4 blocks: `Earth`, `Fire`, `Water`, and `Wind`. 
* You can combine any two blocks, for example:
  * `Earth + Water = Plant`
  * `Plant + Fire = Smoke`
  * `Smoke + Smoke = Cloud`

That's... pretty much it, from a gameplay perspective. There's not really any goal, other than what you set yourself (try to make Cthulhu!). Although if you manage to find something no one has ever made before, you get a neat little note for it!

So wait, what do I mean by 'something no one has ever seen before'?

Well, if two elements have ever been combined by anyone before, you get a cached response. Barring resets of the game (no idea if / how often this has happened, but I assume it has), if `A + B = C` for you, `A + B = C` for everyone. 

And here's the fun part: if you find a combination no one has ever found before: `Neil.fun` will send the combination out to an LLM to generate the new answer. The specific prompt isn't public (so far as I know), but essentially what that means is that you have a basically infinite crafting tree[^infinitish]!

So of course seeing something like this I want to automate it. :smile:

<!--more-->

- - -

{{<toc>}}

## The bot 

In a nutshell, my algorithm is this:

* Store all known elements and combinations in [a cache](#the-cache)
* Forever (or until the site blows up):
  * Wait a moment[^disclaimer]
  * Choose two random elements we haven't chosen together before, submit them
  * Record the response in the cache

That's... really it. It took a bit more than that to get working (see [bot detection](#bot-detection)), but that's *really* it. Here's the code:

```python
# Initial values
elements = ["Wind", "Earth", "Fire", "Water"]
emoji = {
    "Wind": "🌬️",
    "Earth": "🌍",
    "Fire": "🔥",
    "Water": "💧",
}
children = {}
parents = {}
history = set()
discoveries = []

start = time.time()

failures = 0
max_failures = 5

# Start guessing
while failures < max_failures:
    time.sleep(0.1)

    # Save periodically
    if time.time() - start > 60:
        start = time.time()
        save()

    # Pick two random elements
    e1 = random.choice(elements)
    e2 = random.choice(elements)
    e1, e2 = sorted([e1, e2])
    pair = f"{e1}\0{e2}"

    # Skip if we've already tried this pair
    if pair in history:
        continue
    history.add(pair)

    # Make the request
    response = requests.get(
        f"https://neal.fun/api/infinite-craft/pair",
        params={
            "first": e1,
            "second": e2,
        },
        headers=...
    )

    # Parse response, print it out
    try:
        data = response.json()
    except json.JSONDecodeError:
        failures += 1
        print(f"Failed to fetch JSON, retrying ({failures}/{max_failures})...")
        continue

    if data["result"] not in emoji:
        print(
            f'{emoji[e1]} {e1} + {emoji[e2]} {e2} -> {data["emoji"]} {data["result"]}{" (NEW)" if data["isNew"] else ""}'
        )

    # Store any new discoveries
    if data["isNew"]:
        discoveries.append(data["result"])

    # Store new elements
    if not data["result"] in emoji:
        elements.append(data["result"])
        emoji[data["result"]] = data["emoji"]

    # Store the forward relationship
    children[pair] = data["result"]

    # Store the reverse relationship
    if data["result"] not in parents:
        parents[data["result"]] = set()
    parents[data["result"]].add(pair)
```

As mentioned, we have some custom types:

* `Element` - A `str` representing the name of a single element. 
* `ElementPair` - A `str` containing two null delimited `Elements`; so `Earth + Wind` would be encoded as `"Earth\u0000Wind"`. This handles the case that a specific element might actually have a `+` in the name, while (so far as I can tell) they will never contain a null byte. 
* `Emoji` - A `str` containing the single (unicode) character that represents an `Element`, like `Wind` is 🌬️ and `Earth` is 🌍, etc. 

From there, we can represent our data structures:

* `elements: list[Element]` - Stores all elements that we know about. This has to be a `List` so that we can use `random.choice` (that should really be available on `Set`, no?)
* `emoji: dict[Element, Emoji]` - Maps each element to the (I assume generated) emoji that is sent with it; this also serves as an `O(1)` way to check if we've seen an `Element` before (which `elements` can't do)
* `children: dict[ElementPair, Element]` - Maps all known combinations we've seen
* `parents: dict[Element, set[ElementPair]]` - Stores every combination that can be used to create a specific `Element`; because JSON doesn't natively do `sets`, this is stored: list` and converted on save/load
* `history: set[ElementPair]` - Stores all pairs we've tried; looking back on this now, this is just `children.keys()` so we didn't have to store this separately
* `discoveries: list[Element]` - Any elements that have never been created before in the (current) history of Infinite Craft, discovered by us! (or at least this bot)... Some of these are *weird*. 

### Bot detection

One oddity (as hinted at with that `headers=...` line above) is that you can't just fire off a request and hope that it will work. I'm honestly not sure if this is intentional (minimal) bot prevention or if it's a side effect of a library or cache used (there is CloudFront involved here). 

But after a fair bit of experimentation, I've found that you need to supply:

```python
headers={
    "User-Agent": user_agent,
    "Referer": "https://neal.fun/infinite-craft/",
    "Referrer-Policy": "strict-origin-when-cross-origin",
},
```

Where `user_agent` is a valid/new enough user agent. So a current version of Firefox/Chrome/etc. 

It's interesting looking back at previous implementations others have done of this and/or some libraries people have written to do exactly this behavior. Many of them just don't currently work--and it's all because of these header checks.[^disclaimer]

### The cache

So we don't want to just run this once. What if it crashes? We'd have to lose all that progress on each run!

I'm using {{<doc python atexit>}} to save all of these values to a JSON file any time this program exists:

```python
def save():
    print(f"Saving {len(elements)} elements to cache")
    with open("cache.json", "w") as f:
        json.dump(
            {
                "elements": elements,
                "emoji": emoji,
                "children": children,
                "parents": {k: list(v) for k, v in parents.items()},
                "history": list(history),
                "discoveries": discoveries,
            },
            f,
            indent=2,
        )


atexit.register(save)
```

And likewise loading them on every start:

```python
try:
    with open("cache.json", "r") as f:
        print("Loading from cache")
        data = json.load(f)
        elements = data["elements"]
        emoji = data["emoji"]
        children = data["children"]
        parents = {k: set(v) for k, v in data["parents"].items()}
        history = set(data["history"])
        discoveries = data["discoveries"]

except FileNotFoundError:
    print("Cache not found")
    elements = ["Wind", "Earth", "Fire", "Water"]
    emoji = {
        "Wind": "🌬️",
        "Earth": "🌍",
        "Fire": "🔥",
        "Water": "💧",
    }
    children = {}
    parents = {}
    history = set()
    discoveries = []
```

## Findings

And ... that's it. Off we go! I ran it off and on over the course of a few nights (whenever I remembered it) and all together found some 4000 or so elements; over 400 of them never seen before! That's more than I expected. 

So, what interesting things did we find/discover with this data? 

### Raw data

Well, as mentioned, we have some 4000 elements:

```bash
$ cat cache.json | jq -r '.elements[]' | wc -l

    4321

$ cat cache.json | jq -r '.elements[]'

Wind
Earth
Fire
Water
Dust
...
C-3po
Space Fish
Steampunk Poseidon
Harry Potter and the Sorcerer’s Stone
Apex Cider
```

### Discoveries

And of those, a good number have never been seen before!

```bash
$ cat cache.json | jq -r '.discoveries[]' | wc -l

     454

$ cat cache.json | jq -r '.discoveries[]'

Yggdrasil Fishing Pole
Snow Pig Fishing Pole
Treebillionaire
Donut-dusa
Moldy Fireman Rich
...
E-megatitan
Mr. Selfie Mayhem
Baconnaut Trumpwave
Ginguitilla Hobopoly
Apex Cider
```

I know right[^iknow]? A lot of them are of the form '(adjective) (noun)', sometimes with multiple in either category. And one reason we have so many... well look at those first two. If no one has ever seen a `Yggrasil Fishing Pole`, well it stands to reason they've never combined it with `Snow Pig` to get a `Snow Pig Fishing Pole`! :smile:

### Minimal ancestors

Next, let's do something a bit more interesting. Let's take all of those `parents` lists we've generated before and find the minimal set of ancestors needed to build any specific element. More specifically:

* Create a `dict[Element, Set[Element]]` of minimal ancestors; populate with initial elements
* Until this `dict` doesn't change:
  * For each element `e`:
    * For each pair `(e1) + (e2)` that can make `e`:
      * Look up the minimal ancestors of `e1` and `e2`
      * If either is not yet set, ignore this pair for now
      * If both are set, `union` their minimal ancestors and add `{e1, e2}`
      * If this `union` is smaller than the current minimal set of `e` (or if that hans't been set)
        * Update `e`'s minimal set

In code:

```python
import json

with open("cache.json", "r") as f:
    data = json.load(f)
    parents = data["parents"]

minimal_ancestors = {
    "Wind": set(),
    "Earth": set(),
    "Fire": set(),
    "Water": set(),
}

settled = False

while not settled:
    settled = True

    for element in parents:
        for pair in parents[element]:
            e1, e2 = pair.split("\0")
            if e1 not in minimal_ancestors or e2 not in minimal_ancestors:
                continue

            candidate = (
                {e1, e2}.union(minimal_ancestors[e1]).union(minimal_ancestors[e2])
            )

            new_best = False
            if element not in minimal_ancestors:
                new_best = True
            elif len(candidate) < len(minimal_ancestors[element]):
                new_best = True

            if new_best:
                settled = False
                minimal_ancestors[element] = candidate
```

This lets us find the elements that are the most 'complicated' to build. Even if we take the easiest (known) way to build them, it will still take at least some minimal number of steps to make them. 

```python
for i, (
    size,
    key,
) in enumerate(reversed(sorted((len(v), k) for k, v in minimal_ancestors.items())), 1):
    print(f"[{i}] {key}: {size}")
    if i >= 10:
        break
```

Out of my data set, we have:

```python
$ poetry run python minimal-ancestors.py

[1] The Flying Squidtopus: 313
[2] Banana Sword: 291
[3] The Flying Sharktopus: 287
[4] Pigsink: 279
[5] Bananamobile: 275
[6] Cryptopopet: 268
[7] Banana Kong: 267
[8] Blueberry: 266
[9] Baconnaut Creeperzilla: 265
[10] Antbacon Sharktopus: 264
```

Yup. It takes at least 287 other elements to make `The Flying Sharktopus` (the `The` is part of the `Element`!). And another 26 to make that into `The Flying Squidtopus`. The most interesting part of that (to me)? 

```bash
$ cat cache.json | jq -r '.discoveries[]' | grep 'The Flying'

The Flying Porkosaurus
The Flying Organ Grinder
The Flying Charizard Express
The Flying Crabstick Of The Apes
The Flying Apple Fritter
The Flying Cryptotortoise
The Flying Fisherman Express
The Flying Garbage Truck
The Flying Golemzilla
The Flying Cactus Lobster Express
The Flying Porkinator Express
The Flying Dumbledore Fritter
The Flying Sad Wizard
```

*Neither of those* are ones we actually discovered. Someone else found both of them! It's entirely possible there are easier ways to get to them, but I still found that interesting. 

### Rebuilding a path

Okay, we can find the hard elements, but what about actually printing out the path to any particular element? Well, first we start with the same minimal element code, but then we need to do another loop:

* Generate a set of `minimal elements`
* Start with a set of the elements we have `built` and those `to_build` (everything but the basic starting 4)
* Until the `to_build` is empty:
  * For each element `e` in `to_build`; check each pair of elements `e1` and `e2` in built; if any pair makes `e`, report it and move it from `to_build` to `built`

In code:

```python
for arg in sys.argv[1:]:
    print(f"=== {arg} ===")
    if arg not in minimal_ancestors:
        print("Unknown element\n")
        continue

    ancestors = minimal_ancestors[arg]

    def seek(known, target):
        for e1 in known:
            for e2 in known:
                pair = f"{e1}\0{e2}"

                if pair in parents[target]:
                    return (e1, e2)

        raise Exception(f"Could not find a way to build {target}")

    built = {"Earth", "Fire", "Water", "Wind"}
    to_build = set(ancestors).union({arg}).difference(built)

    # Need to loop until settled to handle cases where two tied ancestors only one can build

    while to_build:
        for _, ancestor in sorted(
            (len(minimal_ancestors[ancestor]), ancestor) for ancestor in list(to_build)
        ):
            newly_built = set()

            if minimal_ancestors[ancestor]:
                try:
                    e1, e2 = seek(built, ancestor)
                    print(ancestor, ":", e1, "x", e2)

                    built.add(ancestor)
                    newly_built.add(ancestor)

                except Exception:
                    continue

            to_build = to_build.difference(newly_built)

    print()
```

This will eventually print out the exact combination of elements needed to get to any one target (if we know how):

```bash
$ poetry run python ancestors.py "Gandalf"

=== Gandalf ===
Dust : Earth x Wind
Lava : Earth x Fire
Planet : Dust x Earth
Sandstorm : Dust x Wind
Moon : Earth x Planet
Mud : Dust x Water
Storm : Planet x Wind
Clay : Mud x Mud
Swamp : Mud x Water
Volcano : Clay x Lava
Brick : Clay x Clay
Dust Storm : Sandstorm x Storm
Mist : Swamp x Wind
Pottery : Clay x Earth
Fog : Brick x Mist
House : Brick x Earth
Ceramic : Fire x Pottery
Cloud : Fog x Wind
Dustbin : Dust x House
Ghost : Fog x Swamp
Lunar Eclipse : Dust Storm x Moon
Pig : Dustbin x Mud
Pot : Ceramic x Earth
Rain : Cloud x Earth
Fireball : Fire x Ghost
Haunted House : House x Moon
Stone : Lava x Rain
Piggy Bank : Ceramic x Pig
Sun : Fireball x Moon
Plant : Pot x Sun
Desert : Sandstorm x Sun
Glass : Brick x Sun
Lens : Fog x Glass
Telescope : Dust x Glass
Wine : Glass x Water
Camera : Lens x Plant
Rich Ghost : Ghost x Piggy Bank
Ghost Town : Desert x Haunted House
Gold Rush : Dust x Ghost Town
Rich Lava : Rich Ghost x Volcano
Gold : Earth x Rich Lava
Petra : Camera x Stone
Pirate : Gold x Swamp
Stonehenge : Petra x Telescope
Money Tree : Gold Rush x Plant
Pirate Ship : Pirate x Sun
Druid : Lunar Eclipse x Stonehenge
Titanic : Petra x Pirate Ship
Bankrupt : Money Tree x Titanic
Drunk : Bankrupt x Wine
Black Hole : Dust Storm x Telescope
Wizard : Black Hole x Druid
Gandalf : Drunk x Wizard
```

Yup. `Drunk + Wizard = Gandalf` apparently. I would have gone for `High`, but so it goes. :smile:

### The most/least interesting

And finally, we have arguably the 'most/least' interesting elements. Either from the perspective of the `Emoji` used by the most/least known `Elements` or from the `Elements` with the most children. 

For the most part, it's a bunch of sorting and filtering. 

Here's what I found from my data:

```bash
$ poetry run python most-least.py

easiest to get (179, 'Pig') : Pigpen x Tsunami, Church x Rich Bacon, Fake x Pig King Kong ...
singletons ( 2278 ):  Sad Mangrotron, Porky Poseidon, Sea Weed ...
most children (52, 'Earth') : Eruption, Dust, Earth ...
singleton children ( 449 ) :  The Flying Porkinator Express, Captain Narcissist, Herculean Flying Organ Grinder ...
most common emoji (222, '🦀') : Spongebob Crab Rangoon Pants, Crab Titanium, Crab Cone ...
singleton emoji ( 171 ) :  🚕, 🤕, 🦉, 🦡, 🐞, 🏇, 😵, 👘, 🇻, 🏃 ...
```

Specifically, 'easiest to get' is the `Element` we can get 179 different ways. Take that `Pig`. 

`singletons` is the more than half we've only found one way (so far) to get to, with `singleton_children` being those elements that only create 1 other element (but not zero) and  `singleton emoji` the `Emoji` only used by a single element (necessarily a `singleton` itself). 

`most_children` is the most prolific element: `Earth`, which can make 52 others (makes sense, it's a base element), while the most common emoji... [[wiki:Carcinisation]]() is real, yo. 

And that's it. It's a fun little project based on a fun little project. Onwards!

[^infinitish]: Technically, you could end up in a state where every single possible element has been found, since there are multiple ways to make any specific element. For example you can make `Gandalf` from `Bilbo + Thunderstorm` or `Blacksmith + Dumbledore`. Or even `Old Man + Rainbow Smaug`[^iknow]!. But eventually, you might combine `Bilbo` with every other element. And `Thunderstorm` with every other element. Etc. But it seems that the branching factor is sufficiently high that this should never practical happen[^heatdeath]. 

[^iknow]: I know right? You'd think just `Old Man + Smaug`, but you'll see / have seen in [the implementation details](#the-bot) that I'm choosing which things to combine randomly. So I never actually tried just `Smaug` for this. I do have him (`Fire Flower + The Hobbit`. Or actually `Fire + Gandalf`), I just didn't try that combination. 

[^heatdeath]: `Astrologer + Rainbow Smoke Train = The End of the World`

[^disclaimer]: Okay, first up: This is not at all 'optimal' web citizen behavior. 

    On one hand, there's nothing that suggests Infinite Craft was designed to be automated--there's only an API so much as the site itself exists and even that has some basic bot protection (intentional or not). 

    On the other hand, there's little *specifically* on Neil.fun that prohibits this behavior. There's not really a terms of service (although there is a Privacy Policy). Nor even a robots.txt (not that I went looking before implementing this). 

    So... I suppose your milage may vary. I did make sure to put in some manual delays in my code (so it didn't just run as quickly as possible). I ran it primarily at night (although when that is varies depending on where in the world you are, of course). And when the site started responding oddly, I stopped scraping (although that was half or more because it stopped giving useful data). 

