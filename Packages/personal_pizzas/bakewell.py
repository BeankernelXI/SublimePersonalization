import sublime
import sublime_plugin

from User.SelectionGroups import *


#####################################################################
# Replacement for TextPastry
# provides a prompt for quickly calling commands
# especially useful for passing string arguments eg join
#####################################################################

#TODO:

commands = {
 "commands":
 [
   { "match": "^m(any)?( (\\d{1,3}))?$", "command": "make_many_selections", "args": {"number": "$3"} },
   { "match": "^a(lign)?$", "command": "indent_to_align" },
   { "match": "^c(ol(umn)?)?( (\\d{1,2}))?$", "command": "insert_to_align", "args": {"bufer": "$4"}},
   { "match": "^r(ename)? (.*)$", "command": "rename", "args": {"name": "$2"} },
 # { "match": "^o(pen)? (.*)$", "command": "open_or_create", "args": {"path": "$2"} }, // #Someday
   { "match": "^s(plit)?( -(( -)?[c])*)? (.*)$", "command": "split", "args": {"flags":"$2","re_delimiter": "$5"} },

   { "match": "^p(ull)?($| (.*)$)", "command": "pull", "args": {"delimiter": "$3"} },
   { "match": "^j(oin)?( -(( -)?[c])*)? (.*)$", "command": "join", "args": {"flags":"$2","delimiter": "$5"} },
   { "match": "^u(njoin)?( -(( -)?[c])*)? (.*)$", "command": "unjoin", "args": {"flags":"$2","re_delimiter": "$5"} },
   { "match": "^e(xpand)? (.*)$", "command": "expand", "args": {"param_string": "$2"} },

   { "match": "^(pc) (.*)$", "command": "create_phantoms", "args": {"param_string": "$2"} },
   { "match": "^pc$", "command": "destroy_phantoms" },
   { "match": "^sdp$", "command": "super_duper_phantoms" },

 ]
}

def delimeterify(delimiter):
  if not delimiter: return " "
  match = re.match("[\"'](.*)[\"']", delimiter)
  if match: return match.group(1)
  return delimiter

class MakeManySelectionsCommand(sublime_plugin.TextCommand):
  def run(self, edit, **args):
    print("MakeManySelections")
    raw_num = args['number']
    if raw_num is None:
      number = len(sublime.get_clipboard())
    else:
      number = int(raw_num)
    selection = self.view.sel()
    regions = list(selection)
    selection.clear()
    offset = 0
    for region in regions:
      a_offset = region.a + offset
      b_offset = region.b + offset
      self.view.replace(edit, sublime.Region(a_offset,b_offset), number*"#")
      new_regions = []
      for i in range(number):
        start = region.a + i + offset
        new_regions.append(sublime.Region(start,start+1))
      selection.add_all(new_regions)
      offset += number

class IndentToAlignCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("IndentToAlign")
    v = self.view
    lines = []
    depth = 0
    for region in v.sel():
      row, col = v.rowcol(region.a)
      depth = max(col, depth)
      lines.append(row)
    if len(lines) > len(set(lines)):
      # there is an assumption I could make, but I'd rather get an error
      print("ERROR: more cursors than lines (at least one line has multiple cursors)")
      return
    for region in v.sel():
      row, col = v.rowcol(region.a)
      point = v.line(region.b).a
      indent = depth - col # may add a buffer if I'm feeling edgy (so indent > 0)
      string = ' ' * indent
      v.insert(edit, point, string)

# please future me, dry this :(
class InsertToAlignCommand(sublime_plugin.TextCommand):
  def run(self, edit, bufer = None):
    print("InsertToAlign")
    v = self.view
    bufer = int(bufer or 0) # input can be all kinds of a mess, so best be safe
    lines = []
    line_counts = {}
    depth_matrix = []
    for region in v.sel():
      row, col = v.rowcol(region.begin())
      depth_matrix.append(col)
      lines.append(row)
      if row in line_counts:
        line_counts[row] += 1
      else:
        line_counts[row] = 1
    values_iter = iter(line_counts.values())
    sel_per_row = next(values_iter)
    if not all(sel_per_row == each for each in values_iter):
    # WARNING: ^^^ leaves iterator in inconsistent state
      return
    # target_depths.append(max(depth_matrix[i::sel_per_row]) + (i+1)*bufer)

    for i in range(sel_per_row):
      current_regions = list(v.sel())[i::sel_per_row]
      # find col of each an store them in depth_matrix
      depth_matrix = []
      for region in current_regions:
        row, col = v.rowcol(region.begin())
        depth_matrix.append(col)
      target_depth = max(depth_matrix) + (i+1)*bufer
      # target_depth = target_depths[i]
      offset = 0
      for region in list(v.sel())[i::sel_per_row]:
        point = region.begin() + offset
        row, col = v.rowcol(point)
        indent = target_depth - col
        offset += indent
        string = ' ' * indent
        v.insert(edit, point, string)

class SplitCommand(sublime_plugin.TextCommand):
  def run(self, edit, flags, re_delimiter = " "):
    print("Split")
    if not re_delimiter: re_delimiter = " "
    v = self.view
    if flags is None:
      for region in v.sel():
        split_str = re.split(re_delimiter, v.substr(region))
        delims = re.findall(re_delimiter, v.substr(region))
        offset = region.begin()
        v.sel().subtract(region)
        l = len(split_str[0])
        # TODO: flip region if initial region flipped
        if l > 0:
          v.sel().add(sublime.Region(offset,offset + l))
          offset += l
        for i in range(len(delims)):
          offset += len(delims[i])
          l = len(split_str[i+1])
          # TODO: flip region if initial region flipped
          if l > 0:
            v.sel().add(sublime.Region(offset,offset + l))
            offset += l
    else:
      if re.findall( "-c", flags ):
        string = "".join(re.split(re_delimiter, sublime.get_clipboard()))
        print("Setting clipboard to \"" + string + "\"")
        sublime.set_clipboard(string)

class RenameCommand(sublime_plugin.TextCommand):
  def run(self, edit, name):
    print("Rename")
    v = self.view
    v.set_name(name)
    v.insert(edit,0,'') # v.touch

# joins contents of saved regions and replaces each selection
class PullCommand(SelectionGroupsHelperCommand):
  def run(self, edit, delimiter = ''):
    print("Pull")
    v = self.view
    regions = []
    for region in self.current_group()[::-1]:
      regions.insert(0, v.substr(region) )
      v.erase(edit, region)
    string = delimiter.join(regions)
    for region in v.sel():
      v.replace(edit, region, string)
    v.run_command("clear_group")

# takes a string input and joins the clipboard using that string
class JoinCommand(sublime_plugin.TextCommand):
  def run(self, edit, flags, delimiter):
    print("Join")
    v = self.view
    delimiter = delimeterify(delimiter)
    string = delimiter.join(sublime.get_clipboard().split("\n"))
    if flags is None:
      for region in v.sel():
        v.replace(edit, region, string)
    else:
      if re.findall( "-c", flags ):
        print("Setting clipboard to \"" + string + "\"")
        sublime.set_clipboard(string)

# replaces all instances of the delimiter with newlines
class UnjoinCommand(sublime_plugin.TextCommand):
  def run(self, edit, flags, re_delimiter):
    print("Unjoin")
    v = self.view
    re_delimiter = delimeterify(re_delimiter)
    if flags is None:
      for region in v.sel():
        v.replace(edit, region, self.unjoin(v.substr(region), re_delimiter) )
    else:
      sublime.set_clipboard(self.unjoin(sublime.get_clipboard(), re_delimiter))
  def unjoin(self, str, re_del):
    return "\n".join(re.split(re_del, str))

# fancy paste but using the pastry command line
class ExpandCommand(sublime_plugin.TextCommand):
  def run(self, edit, param_string):
    print("Expand")
    v = self.view
    strings = param_string.split(" ")
    # for now only support single selection
    # TODO: in multiselection case mimic "word"
    if len(v.sel()) is 1:
      initial_region = v.sel()[0]
      line_to_duplicate = v.substr(v.full_line(initial_region))
      count = len(strings)
      # pretty fragile, be careful when editting below
      v.replace(edit, initial_region, strings[-1])
      for string in strings[-2::-1]: # inserts in reverse order because lazy
        v.insert(edit, v.line(initial_region).begin(), line_to_duplicate)
        v.sel().add(initial_region)
        v.replace(edit, initial_region, string)
      return

class FancyJoinCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("FancyJoin")
    v = self.view
    v.run_command("split_selection_into_lines")
    v.run_command("clear_empty_regions")
    v.run_command("join_lines")


