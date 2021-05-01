import sublime
import sublime_plugin

import re

#####################################################################
# Improvements to basic shortcuts
# especially to take better advantage of multiple selections
#####################################################################

#TODO:
  # move functionality of FancyCopy(UniqueCopy) to a new bakewell command
  # rename all these to be more descriptive


# duplicate the current line pasting each clipboard item on a new dup
class FancyPasteCommand(sublime_plugin.TextCommand):
  # BUG: fails strangely when clipboard ends in newline
  # is it really a bug tho if the default paste is to blame
  def run(self, edit, standin_clipboard = None):
    print("FancyPaste")
    v = self.view
    clipboard = standin_clipboard or sublime.get_clipboard()
    if len(v.sel()) == 1:
      region = v.sel()[0]
      content = v.substr(v.full_line(region))
      for unused in range(len(clipboard.split("\n"))-1):
        v.insert(edit, v.line(region).begin(), content)
        v.sel().add(region)
      v.run_command("paste")

# only unique substrings are copied
class FancyCopyCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("FancyCopy")
    v = self.view
    unique_content = set([ v.substr(region) for region in v.sel() ])
    if len(unique_content) == 1:
      [unique_str] = unique_content
      sublime.set_clipboard(unique_str)
    else: v.run_command('copy')

class AccumulatingCopyCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("AccumulatingCopy")
    v = self.view
    initial_clipboard = sublime.get_clipboard()
    acc_regions = []
    if initial_clipboard[-1] != '\n':
      initial_clipboard += '\n' # kinda hacky, but smarter is not better
    else:
      for region in v.sel():
        if(region.size() == 0 ):
          region = v.line(region)
        acc_regions.append( v.substr(region) )
    sublime.set_clipboard(initial_clipboard + '\n'.join(acc_regions) )

# dupes the whole line and puts a new cursor in the matching spot
class FancyDuplicateLineCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("FancyDuplicateLine")
    v = self.view
    for region in v.sel():
      line = v.full_line(region)
      v.insert(edit, line.begin(), v.substr(line))
    new_regions = []
    for region in v.sel():
      line_len = v.full_line(region).size()
      new_region = sublime.Region(region.a-line_len, region.b-line_len)
      new_regions.append(new_region)
    v.sel().add_all(new_regions)

# does what it says. creates a dup of the current line(s) that is commented
class DupAndCommentCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("DupAndComment")
    v = self.view
    for region in v.sel():
      point = v.line(region).begin()
      string = v.substr(v.full_line(region))
      v.insert(edit, point, string)
      line_len = len(string)
    v.run_command("toggle_comment")
    new_regions = []
    for region in v.sel():
      line_len = v.full_line(region).size()
      new_region = sublime.Region(region.a-line_len,region.b-line_len)
      new_regions.append(new_region)
    v.sel().clear()
    v.sel().add_all(new_regions)

# leaves cursors at each of the seams
class FancyJoinCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("FancyJoin")
    v = self.view
    v.run_command("split_selection_into_lines")
    v.run_command("clear_empty_regions") # this feels right. is there better?
    v.run_command("join_lines")

# the fact that I need to write this is hilarious.
# the builtin transpose tries to be so clever that it loses all reliability
class MyTransposeCommand(sublime_plugin.TextCommand):
  # { "keys": ["ctrl+s"], "command": "my_transpose" },
  def run(self, edit):
    print("MyTranspose")
    v = self.view
    if len(v.sel()) is 0: return
    substrs = [v.substr(v.sel()[-1])] # move last region to front
    for region in list(v.sel())[:-1]: # end on second to last region
      substrs.append(v.substr(region) )
    for region, string in zip(v.sel(), substrs):
      v.replace(edit, region, string)

# transpose but keeps each line independent
class InlineTransposeCommand(sublime_plugin.TextCommand):
  # { "keys": ["ctrl+shift+s"], "command": "inline_transpose" },
  def run(self, edit):
    print("InlineTranspose")
    v = self.view
    file_len, _ = v.rowcol(v.size())
    lines = [[] for i in range(file_len)] # [[]]*file_len is real bad
    for region in v.sel():
      row_s, _ = v.rowcol(region.begin())
      row_e, _ = v.rowcol(region.end())
      if row_s != row_e: return
      lines[row_s].append(region)
    all_substrs = []
    for line in lines:
      if len(line) == 0: continue
      substrs = [v.substr(line[-1])] # move last region to front
      for region in line[:-1]: # end on second to last region
        substrs.append(v.substr(region) )
      for i in substrs:
        all_substrs.append(i)
    for region, string in zip(v.sel(), all_substrs): # good pattern
      v.replace(edit, region, string)

# searches for an OR of your selections
class FancyFindUnderCommand(sublime_plugin.TextCommand):
  # { "keys": ["super+shift+a"], "command": "find_all_under" },
  def run(self, edit, mode='next', forward=True, extend=True):
    print("FancyFindAllUnder")
    v = self.view
    new_regions = []

    #TODO:
    # hook into search and take a regex arg

    v.run_command("select_words", {"mode":"empty"})
    v.run_command("make_regions_left_to_right") # this is ugly

    regex = '|'.join( [ re.escape(v.substr(region)) for region in v.sel() ] )
    all_matches = v.find_all(regex)
    # ^^ if you want IGNORECASE as an option/default add it yourself ;)

    if mode == 'next':
      #TODO: if top/bottom is already selected then wrap
      if forward:
        index = all_matches.index(v.sel()[-1])+1
      else:
        index = all_matches.index(v.sel()[0])-1
      wrap = len(all_matches)
      new_regions.append(all_matches[index%wrap])

    elif mode == 'all':
      new_regions = all_matches

    else:
      print("I'm sorry USER, I'm afraid I can't do %s"%mode)

    if len(new_regions) > 0:
      v.show(new_regions[0])
      if not extend: v.sel().clear()
      v.sel().add_all(new_regions)

# does the front half of find_under, with more flexibility
class SelectWordsCommand(sublime_plugin.TextCommand):
  def run(self, edit, mode='always'):
    print("SelectWords")
    v = self.view
    new_regions = []
    for region in v.sel():
     if region.empty() or mode == 'always':
       new_regions.append(v.word(region))
    v.sel().add_all(new_regions)







class MyPasteCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("MyPaste")
    v = self.view
    new_regions = []
    # interpret clipboard
    clipboard = sublime.get_clipboard()
    clipboard_state = oneof['solid', 'iterable', 'doubled']
    # interpret selections
    #   if total number of sel is a multiple of cb length
    #   then normal paste multiples (by cols or rows?)
    #                           aka 1 1 2 2 3 3 or 1 2 3 1 2 3
    #   if all lines have the same number of selections
    #   then fancy paste, repeating each cb line for each sel on the line
    # if blunt: just call the builtin?

    # we [default to blunt paste, basic fancy paste,(fancy?) paste onto newline]
    # iterate
    for region in v.sel():
      # design goals:
      # - always do the paste onto newline thing if
      #        splitting on /\n\n|\n\EOF/ leaves no \n left
      #        ^^ doing it literally like this sounds inefficient
      # - selections on the same line get special consideration
      #     InsertToAlign had similar requirements
      # - default to fancy paste, option for blunt paste
      # -

      new_regions.append(region)

    if len(new_regions) > 0:
      v.show(new_regions[0])
      v.sel().clear()
      v.sel().add_all(new_regions)












