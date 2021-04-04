import sublime
import sublime_plugin

import subprocess
import re, json, html

#####################################################################
# Build Phantoms
#
#####################################################################

#TODO:
  # show regions as they are added, not just after the build


class BuildWithPhantomsCommand(sublime_plugin.TextCommand):
  # overloaded command to keep subscribed lines
  def __init__(self, view):
    self.view = view
    self.subscribed_lines = []

  # flag mask options:
  # ADD, ADD_ONCE, BUILD, CLEAR, *_ = Flags()

  MAGIC_STRING = 'BUILD_RESULTS'
  MAGIC_KEY = 'build_result'

  def run(self, edit, mode=None, modes=[]):
    print("BuildWithPhantoms")
    v = self.view
    if mode: modes.append(mode) # to make the api more flexible
    print(modes)

    if 'clear' in modes:
      v.erase_phantoms(self.MAGIC_KEY)
      v.erase_regions(self.MAGIC_KEY)
      self.subscribed_lines = []

    if 'add' in modes:
      for region in v.sel():
        self.subscribed_lines.append([region.begin(),region.end()])
        #TODO: mark regions a different way too

    if 'add_once' in modes:
      additional_lines = [[region.begin(),region.end()] for region in v.sel()]
    else:
      additional_lines = []

    if 'build' in modes or not modes:
      output_json = self.run_file(additional_lines)
      # print(output_json)
      v.erase_phantoms(self.MAGIC_KEY)
      self.create_phantoms(output_json)
      self.mark_regions(output_json)

  def run_file(self,additional_lines):
    whole_file = self.view.substr(sublime.Region(0,self.view.size()))
    chopped_text = [self.ruby_intro()]
    prev_point = 0

    for region_begin, region_end in (self.subscribed_lines + additional_lines):
      chopped_text.append( whole_file[prev_point:region_begin] )
      if region_begin == region_end:
        chopped_text.append( self.ruby_insertion_chain(region_begin,region_end) )
      else:
        chopped_text.append( self.ruby_insertion_start() )
        chopped_text.append( whole_file[region_begin:region_end] )
        chopped_text.append( self.ruby_insertion_end(region_begin,region_end) )
      prev_point = region_end
    chopped_text.append( whole_file[prev_point:] )
    chopped_text.append( self.ruby_outro() )
    new_whole_file = ''.join(chopped_text)
    # print(new_whole_file)

    # self.view.window().run_command("exec", {
    #   "shell_cmd": "echo $" + repr(new_whole_file) + " | ruby | grep" + self.MAGIC_STRING
    #   })

    s = subprocess.Popen(
                    "ruby",
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    )

    out, err = s.communicate(new_whole_file.encode('utf8'))
    if err:
      print(err)
      raise
    matcher = '(%s)(.*)\\n'%(self.MAGIC_STRING)
    match = re.search(matcher, out.decode('utf8'))
    if match:
      return(match.group(2))
    else:
      return ""

  def ruby_intro(self):
    return """
    require 'json'
    $collection_of_json_objects = []
    def save_it_to_json(points, result)
      thing = { points: points,
                result: result.inspect
              }
      $collection_of_json_objects << thing
    end
    """

  def ruby_insertion_start(self):
    return "("
  def ruby_insertion_end(self,start_point, end_point):
    # seriously, none of the better interpolation methods work here...
    return ").tap{|it| save_it_to_json("+str([start_point, end_point])+".inspect, it)}"

  def ruby_insertion_chain(self,start_point, end_point):
    return ".tap{|it| save_it_to_json("+str([start_point, end_point])+".inspect, it)}"

  def ruby_outro(self):
    return '\nputs "%s#{$collection_of_json_objects.to_json}"'%(self.MAGIC_STRING)

  def create_phantoms(self,output_json):
    # iterates over json
    # creates a phantom for each one
    phantoms = {}
    for output in json.loads(output_json):
      phantoms.setdefault(output['points'],[]).append(output['result'])
    for points, results in phantoms.items():
      points = json.loads(points)
      region = sublime.Region(points[0],points[1])
      result = self.explain_results(results)
      self.view.add_phantom(self.MAGIC_KEY, region, result, sublime.LAYOUT_BELOW)

  def mark_regions(self,output_json):
    points = list(set( [ output['points'] for output in json.loads(output_json) ] ))
    regions = [sublime.Region(*json.loads(pair)) for pair in points]
    self.view.add_regions(self.MAGIC_KEY, regions, 'source.ruby.orange', '', sublime.DRAW_NO_FILL)

  def explain_results(self,results):
    results_set = list(set(results))
    if len(results_set) == 1:
      return html.escape( "=> " + results[0] )
    elif len(results) > 10:
      return html.escape( "*> " + ', '.join(results[0:3])+", ... "+', '.join(results[-3::]) )
    else:
      return html.escape( "*> " + ', '.join(results) )






