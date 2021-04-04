import sublime
import sublime_plugin
import re

#####################################################################
# Editor improvements
# mostly navigation, some misc window and app commands
#####################################################################

#TODO:
  # nothing yet :)

# for those "scratch" files that aren't technically scratch files
class CloseHarderCommand(sublime_plugin.WindowCommand):
  # { "keys": ["super+w"], "command": "close_harder"},
  # { "keys": ["super+k", "super+w"], "command": "close_window" },
  # { "keys": ["super+shift+w"], "command": "close_all" },
  def run(self):
    print("CloseWithoutSaving")
    view = self.window.active_view()
    if not view.file_name(): view.set_scratch(True)
    view.close()

# mimics chrome and others, jumping focus to the last tab
class LastTabCommand(sublime_plugin.WindowCommand):
  # { "keys": ["super+9"], "command": "last_tab" },
  def run(self):
    print("LastTab")
    w = self.window
    group = w.active_group()
    w.focus_view(w.views()[-1])

# mimics chrome and others, quickly resetting zoom level
class ResetSizeCommand(sublime_plugin.ApplicationCommand):
  # { "keys": ["super+0"], "command": "reset_size" },
  def run(self):
    print("ResetSize")
    settings = sublime.load_settings("Preferences.sublime-settings")
    new_size = settings.get("default_font_size", 12)
    settings.set("font_size", new_size)
    sublime.save_settings("Preferences.sublime-settings")

# basically every other command has an 'extend' option, so here's this one
class JumpBackExtendCommand(sublime_plugin.TextCommand):
  # { "keys": ["super+["], "command": "jump_back"},
  # { "keys": ["super+shift+["], "command": "jump_back_extend"},
  def run(self, edit):
    print("JumpBackExtend")
    selection = self.view.sel()
    regions = list(selection)
    self.view.run_command("jump_back")
    selection.add_all(regions)
class JumpForwardExtendCommand(sublime_plugin.TextCommand):
   # { "keys": ["super+]"], "command": "jump_forward"},
   # { "keys": ["super+shift+]"], "command": "jump_forward_extend"},
  def run(self, edit):
    print("JumpForwardExtend")
    selection = self.view.sel()
    regions = list(selection)
    self.view.run_command("jump_forward")
    selection.add_all(regions)

# comments new line if appropriate
class SmartNewlineCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("SmartNewline")
    v = self.view
    for i in range(len(v.sel())):
      region = v.sel()[i]
      is_comment = v.score_selector(region.begin(),'comment')
      v.run_command("insert", { "characters": "\n"})
      if is_comment and not v.score_selector(v.sel()[i].begin(),'comment'):
        v.run_command("toggle_comment")

# the default macro for this is awful
#   doesn't delete contents of selections half the time
class DeleteToCommand(sublime_plugin.TextCommand):
  def run(self, edit, forward=False):
    print("DeleteTo")
    v = self.view
    for region in list(v.sel())[::-1]:
      if forward:
        v.erase(edit,sublime.Region(
                               region.begin(),
                               v.line(region.end()).end()
                             ))
      else:
        v.erase(edit,sublime.Region(
                               v.line(region.begin()).begin(),
                               region.end()
                             ))

# the default macro for this is awful too, for a similar reason
class AddLineCommand(sublime_plugin.TextCommand):
  def run(self, edit, forward=True):
    print("AddLine")
    v = self.view
    new_regions = []
    for region in v.sel():
      if forward:
        new_region = sublime.Region(region.end(),region.end())
      else:
        new_region = sublime.Region(region.begin(),region.begin())
      new_regions.append(new_region)
    v.sel().clear()
    v.sel().add_all(new_regions)
    if forward:
      v.run_command("run_macro_file", {"file": "res://Packages/Default/Add Line.sublime-macro"})
    else:
      v.run_command("run_macro_file", {"file": "res://Packages/Default/Add Line Before.sublime-macro"})
    v.run_command("clear_fields")


# puts the path onto your clipboard in various forms
class CopyPathCommand(sublime_plugin.TextCommand):
  def run(self, edit, mode = 'path'):
    print("CopyPath")
    v = self.view
    folder = v.window().extract_variables().get('folder','')
    file_path = v.window().extract_variables().get('file_path','')
    if folder: folder += '/' # likely blows up for root but idc
    path = v.file_name().replace( folder, '', 1) # only the first match
    # path "needs" to be escaped
    lines = [[],[]] # starts, ends
    eof = v.rowcol(v.size())[0]
    for region in v.sel():
      row_s,col_s = v.rowcol(region.begin() )
      row_e,col_e = v.rowcol(region.end() )
      if row_e == eof: # and col_e == 0: # git blame assumes files end in \n
        row_e -= 1 # doing this here since str#join is picky
      lines[0].append( str(row_s+1) ) # switch to 1-indexed
      lines[1].append( str(row_e+1) ) # switch to 1-indexed
    if mode == 'cd':
      sublime.set_clipboard('cd ' + file_path.replace(' ', '\\ '))
    elif mode == 'path':
      sublime.set_clipboard(path + ':' + ','.join(lines[0]) )
    elif mode == 'rspec':
      sublime.set_clipboard('rspec ' + path + ':' + ','.join(lines[0]) )
    elif mode == 'blame':
      out = 'git blame '
      for start, end in zip(lines[0],lines[1]):
        out += '-L' + start + ',' + end + ' '
      sublime.set_clipboard(out + path)
    else:
      print("Silly rabbit, I don't support \"%\""%mode)

# improves move(by:"stops", empty_line: True)
# jumps to the next line that borders on an empty line
class MoveToNextGapBoundryCommand(sublime_plugin.TextCommand):
  # { "keys": ["alt+up"], "command": "move_to_next_gap_boundry", "args": {"forward": false} }
  # { "keys": ["alt+down"], "command": "move_to_next_gap_boundry", "args": {"forward": true} }
  # { "keys": ["shift+alt+up"], "command": "move_to_next_gap_boundry", "args": {"forward": false, "extend": true}}
  # { "keys": ["shift+alt+down"], "command": "move_to_next_gap_boundry", "args": {"forward": true, "extend": true}}
  def run(self, edit, forward = True, extend = False):
    print("MoveToNextGapBoundry")
    v = self.view
    new_regions = []
    for region in v.sel():
      select_start = region.a # for extend == True
      cursor_line = v.line(region.b)
      search_start = cursor_line.b if forward else cursor_line.a
      # ^^ so that CLASS_WORD_END always skips the current line
      next_empty_line = v.find_by_class(search_start, forward, sublime.CLASS_EMPTY_LINE)
      next_wordy_line = v.find_by_class(search_start, forward, sublime.CLASS_WORD_END)

      # simple alg to jump the way we want.
      # we undershoot so the cursor always lands on a non-empty line
      if forward:
        target = max(next_wordy_line, next_empty_line - 1)
      else:
        target = min(next_wordy_line, next_empty_line + 1)

      # for now, bluntly puts the new cursor at the end of the line
      # TODO: put cursor at start if going back
      target = v.line(target).b

      if extend:
        new_regions.append( sublime.Region(select_start, target) )
      else:
        new_regions.append( sublime.Region(target, target) )
    v.show(new_regions[0]) # convention says we track only the first region
    v.sel().clear()
    v.sel().add_all(new_regions)

# shows all the diffs, not just the selected one
class ToggleHunkDiffEntireFileCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("ToggleHunkDiffEntireFile")
    v = self.view
    s = v.sel()
    regions = list(s) # save current selection
    s.clear()
    s.add(sublime.Region(0,v.size())) # select entire file
    v.run_command("toggle_inline_diff")
    s.clear()
    s.add_all(regions) # restore original selection

# reset those colorful gutter bars for files not in version control
class ResetReferenceDocumentCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("ResetReferenceDocument")
    v = self.view
    v.reset_reference_document()

# pulls selection into a new assignment on the preceding line
class RefactorCommand(sublime_plugin.TextCommand):
  # { "keys": ["super+k","super+r"], "command": "refactor"},
  def run(self, edit):
    print("Refactor")
    v = self.view
    new_regions = []
    for region in v.sel():
      point = v.line(region).begin()
      # is there a consise way to match indentation?
      word = v.substr(v.word(point))
      match = re.match( "\n(( |\t)*)", word )
      if(match):
        indentation = match.group(1)
      else:
        indentation = ''
      string = indentation + " = " + v.substr(region) + "\n"
      v.insert(edit, point, string)
      new_point = point+len(indentation)
      new_regions.append(sublime.Region(new_point,new_point))
    v.sel().add_all(new_regions)

class NewRefactorCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("Refactor")
    v = self.view
    new_regions = []
    # edit_pairs = []
    for i, region in enumerate(v.sel()):


      new_regions.append(region)

    if len(new_regions) > 0:
      v.show(new_regions[0])
      v.sel().clear()
      v.sel().add_all(new_regions)

# check out fancy.find_under for a more general version of this
class FindFromClipboardCommand(sublime_plugin.TextCommand):
  def run(self, edit, in_selection=False):
    print("FindFromClipboard")
    v = self.view
    lines = re.split("\n", sublime.get_clipboard())

    found = []
    for line in lines:
      if in_selection:
        for region in v.find_all(line,sublime.LITERAL):
          if v.sel().contains(region):
            found.append(region)
      else:
        found += v.find_all(line,sublime.LITERAL)

    if len( found ) > 0:
      v.show(found[0])
      v.sel().clear()
      v.sel().add_all( found )

class ClearEmptyRegionsCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("ClearEmptyRegions")
    v = self.view
    new_regions = []
    for region in v.sel():
      if not region.empty():
        new_regions.append(region)
    if len(new_regions) > 0:
      v.sel().clear()
      v.sel().add_all(new_regions)

class SelectGapsCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print("SelectGaps")
    v = self.view
    new_regions = []
    old_region = v.sel()[0]
    for region in list(v.sel())[1:]:
      new_regions.append(sublime.Region(old_region.end(), region.begin()))
      old_region = region
    if len(new_regions) > 0:
      v.sel().clear()
      v.sel().add_all(new_regions)





