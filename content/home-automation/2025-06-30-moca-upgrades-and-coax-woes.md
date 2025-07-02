---
title: MoCA Upgrades and Coax woes
date: 2025-06-30
programming/topics:
- MoCA
- Coaxial
- Home networking
- Mesh networking
- Ethernet
- DOCSIS
- Modem
- Router
- Switch
- Latency
---
So over the past week or so... I've been having some serious issues with the internet at home. And since I work remotely with computers for a living... well, having a stable internet connection is kind of important. 

So I decided to finally bite the bullet and do an upgrade that I've been meaning to do for a long time: Install [[wiki:MoCA Adaptors]]() to use the existing [[wiki:coaxial cables]]() already in the walls to provide a wired connection between the mesh routers I'm already using on the various floors of the house.

Oh, this took *far* longer than I hoped it would...

<!--more-->

- - -

{{<toc>}}

Here's a general key to the different connection types:

{{<mermaid>}}
flowchart TD
  subgraph "Key"
    Coax --- Coax
    Ethernet -.- Ethernet
    WiFi -.-|wifi| WiFi
  end
{{</mermaid>}}

## V0 - How it was before

So in the original configuration, I had all of the core networking devices in my office. Since this is where my work is, along with my home server and NAS, this made sense. 

But unfortunately, the coaxial connection coming into the house went into the basement... So I had a cable running into the basement, through a crawlspace, through the garage, into the garage attic, into the office. Not ideal. 

From there, I had the primary mesh router, which connected everything I cared about with a wired ethernet connection. I had two more routers on the first floor and basement, these were connected via wifi to the primary router. 

Functional, but we would sometimes have *pretty bad* latency issues between the mesh routers. So I thought we could do better.

{{<mermaid>}}
flowchart TD
  Pedestal

  subgraph Office
    Modem
    Router_Office["Primary Mesh Router"]
    Switch_Office["Ethernet Switch"]
    Server
    NAS
  end

  subgraph "Basement"
    subgraph "Utility Room"
      Coax11["*coax*"]
    end

    subgraph "Media Room"
      Router_Basement["Mesh Router"]
    end
  end

  subgraph "Living Room"
      Router_LivingRoom["Mesh Router"]
  end

  Pedestal --- Coax11
  Coax11 --- Modem

  Modem -.- Router_Office
  Router_Office -.- Switch_Office
  Switch_Office -.- Server
  Switch_Office -.- NAS

  Router_Office -.-|wifi| Router_LivingRoom
  Router_LivingRoom -.-|wifi| Router_Basement
{{</mermaid>}}

## V1 - Splitters to the office

So, as mentioned, I decided that enough was enough. I was going to actually try those MoCA adaptors I'd heard so much about. I had to install a pair of coaxial splitters, but what could go wrong? 

{{<mermaid>}}
flowchart TD
  Pedestal

  subgraph Office
    Modem
    CoaxSplitter_Office["1:2 Coax Splitter"]
    Router_Office["Primary Mesh Router"]
    MoCA_Office["MoCA"]
    Hub_Office["Ethernet Hub"]

    CoaxSplitter_Office --- MoCA_Office
    CoaxSplitter_Office ---|Filter| Modem

    Modem -.- Router_Office
    Router_Office -.- Hub_Office
    Hub_Office -.- Server
    Hub_Office -.- NAS
    Hub_Office -.- MoCA_Office
  end

  subgraph "Basement"
    subgraph "Utility Closet"
      CoaxSplitter["1:3 Coax Splitter"]
      MoCA_Basement[MoCA]
    end

    subgraph "Media Room"
      Hub_Basement["Ethernet Hub"]
      Router_Basement["Mesh Router"]
      MediaDevices([Media Devices])
    end

    MoCA_Basement -.- Hub_Basement
    Hub_Basement -.- MediaDevices
    Hub_Basement -.- Router_Basement
  end
  
  subgraph "Living Room"
    MoCA_LivingRoom["MoCA"]
    Router_LivingRoom["Mesh Router"]

    MoCA_LivingRoom -.- Router_LivingRoom
  end

  Pedestal ---|Filter| CoaxSplitter
  CoaxSplitter --- CoaxSplitter_Office
  CoaxSplitter --- MoCA_LivingRoom
  CoaxSplitter --- MoCA_Basement
{{</mermaid>}}

In this case, I needed two splitters: the first would split the connection to the three rooms from outside and the second would be in the office to have an incoming connection to the modem and an 'outgoing' connection to the MoCA network. 

Eventually, I did get this working. It took a lot of trial and error, replacing cables, and connecting things in the right order, but I did get it working. 

And all was well... (Or not, seeing as we have more blog post to go.)

As a side note: I tried both with and without [[wiki:MoCA POE Filters]]() as shown. In theory, MoCA and incoming cable internet (using [[wiki:DOCSIS 3.1]]()) can overlap slightly. 

Also, if you 'leak' MoCA connections to the external connection, in theory others in the same neighborhood could install their own MoCA adaptors and pick up your network. Is this likely where I live? No. Do I work in security and should be paranoid about this anyways? Yes. 

This setup ended up being stable for about 12 hours and then in the middle of the night... it just died. Try as I might, I just *could not* get it to connect in this configuration. 

## V2 - Modem in the basement

I ended up calling out a tech to check noise and signal strength on my connection, but one theory I had (before they showed up) was that the splitters weren't letting enough signal get to the modem. So as an interim solution, I ended up with this:

{{<mermaid>}}
flowchart TD
  Pedestal
  
  subgraph "Basement"
    subgraph "Utility Closet"
      CoaxSplitter12["1:2 Coax Splitter"]
      CoaxSplitter13["1:3 Coax Splitter"]
      MoCA_Basement[MoCA]
    end

    subgraph "Media Room"
      Modem
      Router_Basement["Primary Mesh Router"]
      Hub_Basement["Ethernet Hub"]
      MediaDevices([Media Devices])
    end    
  end

  subgraph "Living Room"
    MoCA_LivingRoom["MoCA"]
    Router_LivingRoom["Mesh Router"]
  end

  subgraph Office
    MoCA_Office["MoCA"]
    Router_Office["Mesh Router"]
    Hub_Office["Ethernet Hub"]
    Server
    NAS
  end

  Pedestal ---|Filter| CoaxSplitter12
  
  CoaxSplitter12 ---|Filter| Modem
  CoaxSplitter12 ---|but why...| CoaxSplitter13

  CoaxSplitter13 --- MoCA_Basement
  CoaxSplitter13 --- MoCA_Office
  CoaxSplitter13 --- MoCA_LivingRoom
  
  Modem -.- Router_Basement
  
  Router_Basement -.- Hub_Basement
  Hub_Basement -.- MediaDevices
  Hub_Basement -.- MoCA_Basement
  
  MoCA_LivingRoom -.- Router_LivingRoom
  
  MoCA_Office -.- Hub_Office
  Hub_Office -.- Router_Office
  Hub_Office -.- Server
  Hub_Office -.- NAS
{{</mermaid>}}

Here we have a single 1:2 splitter immediately on our connection which goes to the modem (now in the basement) and then splits back off to a 1:3 splitter connecting the MoCA networks.

Keen observers may note that this setup... is kind of silly. I do not at all need the coax connection labeled 'but why?'. That ends up being fairly close to what I did for [v3](#v3---separate-moca-completely-and-back-upstairs). Here, the primary hub is downstairs.

This never ended up working... but I don't think it was actually a wiring issue. Like I said, this one is actually pretty close to my final solution, but in this case, my networking gear is no longer in my office, so I have to go down two flights of stairs if I need to reset anything. No fun that. 

## V3 - Separate MoCA completely and back upstairs

So for the third (and final (for now)) solution, I ended up having a tech at the house which replaced all of the cables both leading into the house but also running out to the pedestal. While he was here, we also directly ran a line into the office (through the wall), which meant that I wouldn't need to pass the incoming connection and MoCA both over the line from basement to office. 

{{<mermaid>}}
flowchart TD
  Pedestal

  subgraph Office
    Modem
    Router_Office["Primary Mesh Router"]
    Switch_Office["Ethernet Switch"]
    Server
    NAS
    MoCA_Office["MoCA"]
  end

  subgraph "Basement"
    subgraph "Utility Closet"
      CoaxSplitter13["1:3 Coax Splitter\n(could be 1:2)"]
      MoCA_Basement[MoCA]
    end

    subgraph "Media Room"
      Router_Basement["Mesh Router"]
      Switch_Basement[Ethernet Switch]

      MediaDevices(["Media Devices"])
    end    
  end

  subgraph "Living Room"
    MoCA_LivingRoom["MoCA"]
    Router_LivingRoom["Mesh Router"]
  end

  Pedestal --- Modem

  Modem -.- Router_Office

  Router_Office -.- Switch_Office

  Switch_Office -.- MoCA_Office
  Switch_Office -.- Server
  Switch_Office -.- NAS

  CoaxSplitter13 --- MoCA_LivingRoom
  CoaxSplitter13 --- MoCA_Basement
  CoaxSplitter13 --- MoCA_Office
  
  MoCA_Basement -.- Switch_Basement
  Router_Basement -.- Switch_Basement

  Switch_Basement -.- MediaDevices
  
  MoCA_LivingRoom -.- Router_LivingRoom
{{</mermaid>}}

This... ended up sort of working? 

Once I fixed [the next issue](#the-problem-all-along), this set up is working great. I get very nearly my full advertised 1 Gbps down along with ~20ms ping even on wifi, which is a *major* upgrade.

## The problem all along

Except it turns out that the actual problem all along? Hardware issues with the modem that I had + some bad wiring. In the end, I switched to a bring-my-own-modem (which gives me a stats page too, yay!) and replaced several cheap ethernet cables with some slightly better ones. 

In general, the quality o cables *really* doesn't matter... but in this case, it did actually bite me. I don't know if they broke before I got them or I did something, but man that was a pain to track down. 

Hopefully this is helpful!

(If nothing else, I now have a copy of my current network connection the next time I need to remember how this all works...)