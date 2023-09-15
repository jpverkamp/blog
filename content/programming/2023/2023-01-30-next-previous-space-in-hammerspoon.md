---
title: "Next/Previous 'Space' in Hammerspoon"
date: 2023-01-30
programming/languages:
- Lua
programming/topics:
- Dotfiles
- Window Managers
- Productivity
---
A quick somewhat hacky followup to [[Once Again, to Hammerspoon]](): moving windows to the next/previous Space on a single screen. 

<!--more-->

```lua
function advanceWindow(params)
  local offset = params["offset"] or 1
  local window = params["window"] or hs.window.focusedWindow()

  local targetSpaceID = hs.spaces.windowSpaces(window)[1]
  local currentScreen = nil
  local currentIndex = nil

  for screen, spaces in pairs(hs.spaces.allSpaces()) do
    for index, space in ipairs(spaces) do
      if targetSpaceID == space then
        currentScreen = screen
        currentIndex = index
        break
      end
    end
    if current_space ~= nil then break end
  end

  local nextIDs = hs.spaces.allSpaces()[currentScreen]
  local nextIndex = (currentIndex + offset) % #nextIDs
  local nextSpaceID = nextIDs[nextIndex]

  hs.spaces.moveWindowToSpace(window, nextSpaceID)
  hs.spaces.gotoSpace(nextSpaceID)
end
```

This is a close cousin to `rehome`, but this time what I want to do is take a window in a Mission Control 'Space' and move it to the next (or previous (or offset by whatever)) space.

Really, the main complication here is needing to find the space ID, turn it into an index, apply the offset, and then turn it back into an ID... because the IDs are in who knows what order. But it does work. And plus, I found `hs.spaces.gotoSpace`, which uses Mission Control to follow the window. Pretty cool. 

Add a few keybindings:

```lua
-- move to next/previous screen (if there is one)
hs.hotkey.bind("⌘⌃⇧", "left",  thunkAdvanceWindow{offset=-1})
hs.hotkey.bind("⌘⌃⇧", "right", thunkAdvanceWindow{offset=1})
```

And away we go. 