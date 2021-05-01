import sublime
import sublime_plugin

#####################################################################
# Power User features to really push multiple selections
#####################################################################

#TODO:

# make individual selections on every character in regions #goofy
class EachCharCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("EachChar")
    v = self.view
    new_regions = []
    for region in v.sel():
      for loc in range(region.begin(), region.end() ):
        new_regions.append(sublime.Region(loc, loc+1))
    if len(new_regions) > 0:
      v.show(new_regions[0])
      v.sel().clear()
      v.sel().add_all(new_regions)

# switches what side of each selection the cursor is on
class ReverseRegionsCommand(sublime_plugin.TextCommand):
  # { "keys": ["ctrl+r"], "command": "reverse_regions"},
  def run(self, edit):
    print("ReverseRegions")
    v = self.view
    for region in v.sel():
      a, b = region.a, region.b
      v.sel().subtract(region)
      v.sel().add(sublime.Region(b,a))

# unifies the direction of all selections
class MakeRegionsLeftToRightCommand(sublime_plugin.TextCommand):
  # { "keys": ["ctrl+shift+r"], "command": "make_regions_left_to_right"},
  def run(self, edit):
    print("MakeRegionsLeftToRight")
    v = self.view
    for region in v.sel():
      a, b = region.a, region.b
      if a > b:
        v.sel().subtract(region)
        v.sel().add(sublime.Region(b,a))

# extends selection from both ends
class LeftOrRightCommand(sublime_plugin.TextCommand):
  # { "keys": ["super+,"], "command": "left_or_right", "args": {"direction": "left"}},
  # { "keys": ["super+."], "command": "left_or_right", "args": {"direction": "right"}},
  def run(self, edit, direction):
    print("InOrOut")
    v = self.view
    adj = 0
    if direction == 'left':  adj = -1
    if direction == 'right': adj = +1
    regions = list(v.sel())
    for region in regions:
      a, b = region.a, region.b
      v.sel().subtract(region)
      v.sel().add(sublime.Region(a - adj, b + adj) )

# selects just the edges of each selection
# for use in combination with expand_selection to select the ( { " etc
class SelectEdgesCommand(sublime_plugin.TextCommand):
  # { "keys": ["super+shift+,"], "command": "select_edges", "args": {"direction": "left"}},
  # { "keys": ["super+shift+."], "command": "select_edges", "args": {"direction": "right"}},
  def run(self, edit, direction):
    print("SelectEdges")
    if direction in ['left','right']:
      self.left_right(edit, direction)
    if direction in ['in','out']:
      self.in_out(edit, direction)

  # direction based on cursor, then mirrored for the other side
  def left_right(self,edit,direction):
    v = self.view
    adj = 0
    if direction == 'left':  adj = -1
    if direction == 'right': adj = +1
    regions = list(v.sel())
    for region in regions:
      a, b = region.a, region.b
      v.sel().subtract(region)
      v.sel().add(sublime.Region(a - adj, a) )
      v.sel().add(sublime.Region(b, b + adj) )

  # deprecated
  def in_out(self,edit,direction):
    v = self.view
    regions = list(v.sel())
    for region in regions:
      a, b = region.a, region.b
      if direction == 'in' and a - b in [-1,0,1]:
        continue
      v.sel().subtract(region)
      if (a < b and direction == 'in') or (a >= b and direction == 'out'):
        v.sel().add(sublime.Region(a,a+1))
        v.sel().add(sublime.Region(b-1,b))
      if (a > b and direction == 'in') or (a <= b and direction == 'out'):
        v.sel().add(sublime.Region(a-1,a))
        v.sel().add(sublime.Region(b,b+1))

# shifts selection to the left one character
class ShiftRegionLeftCommand(sublime_plugin.TextCommand):
  # { "keys": ["super+alt+,"], "command": "shift_region_left" },
  def run(self, edit, direction = None):
    print("ShiftRegionLeft")
    v = self.view
    for region in v.sel():
      if region.begin() == 0:
        continue
      string = v.substr(region)
      point_to = region.end() - 1 # pre offsetting
      region_from = sublime.Region(region.begin() - 1, region.begin() )
      string = v.substr(region_from)
      print(point_to, region_from, string)
      v.erase(edit, region_from)
      v.insert(edit, point_to, string)

# shifts selection to the right one character
class ShiftRegionRightCommand(sublime_plugin.TextCommand):
  # { "keys": ["super+alt+."], "command": "shift_region_right" },
  def run(self, edit, direction = None):
    print("ShiftRegionRight")
    v = self.view
    for region in v.sel():
      if region.end() == v.size():
        continue
      string = v.substr(region)
      point_to = region.begin()
      region_from = sublime.Region(region.end(), region.end() + 1 )
      string = v.substr(region_from)
      print(point_to, region_from, string)
      v.erase(edit, region_from)
      v.insert(edit, point_to, string)

# creates selections between pairs of cursors
class SlurpCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("Slurp")
    v = self.view
    s = list(v.sel())
    v.sel().clear()
    if len(s) % 2 is 0:
      for pairs in zip(s[::2],s[1::2]):
        start = pairs[0].begin()
        end = pairs[1].end()
        v.sel().add(sublime.Region(start,end))
    else:
      start = s[0].begin()
      end = s[-1].end()
      v.sel().add(sublime.Region(start,end))


# opposite of slurp, creates cursors on the edges of selections
class ReduceToEdgesCommand(sublime_plugin.TextCommand):
  # { "keys": ["super+shift+x"], "command": "reduce_to_edges"},
  def run(self, edit):
    print("ReduceToEdges")
    v = self.view
    regions = list(v.sel())
    v.sel().clear()
    for region in regions:
      v.sel().add(sublime.Region(region.a,region.a))
      v.sel().add(sublime.Region(region.b,region.b))

