#!/usr/bin/python
# encoding: utf-8

import sys

from workflow import Workflow, ICON_ERROR, ICON_INFO

__version__ = '1.2'

def main(wf):
  from lxml import html
  import requests
  import json
  import urllib
  import re

  def search(query):
    if wf.update_available:
      wf.add_item('New version available',
                  'Press enter install the update',
                  autocomplete='workflow:update',
                  icon=ICON_INFO)

    if query.startswith("answer:"):
      show_answers_for_question(query.replace("answer:", ""))
      return

    searchTerm = ' '.join(['site:stackoverflow.com/questions'] + [query])
    searchUrl = 'google.com/search?' + urllib.urlencode({'q': searchTerm})

    searchResults = search_google(searchTerm)

    numResults = 0

    for result in searchResults:
      url = result['url']
      if numResults is 0:
        stackoverflowResponse = requests.get(url)
        answers = get_stack_overflow_answers(stackoverflowResponse)
        if len(answers) > 0:
          numResults = numResults + 1
          question = get_question_title(stackoverflowResponse)
          output_answer(url, question, answers[0], "Best answer for: ")
          wf.add_item("Other Questions:", "(press TAB or ENTER to view answers)")
      else:
        wf.add_item(
          re.search("/([^/]*)$", url).group(1).replace("-", " "), 
          "",
          copytext = url,
          autocomplete = "answer:" + url,
          arg = url,
          valid = True,
          icon = "appbar.question.png")

    if numResults is 0:
      wf.add_item(
        'No results found', 
        'Select to view google search', 
        arg = 'http://www.' + searchUrl, 
        valid = True)

    # Send output to Alfred
    wf.send_feedback()

  def show_answers_for_question(url):
    stackoverflowResponse = requests.get(url)
    answers = get_stack_overflow_answers(stackoverflowResponse)
    question = get_question_title(stackoverflowResponse)
    for answer in answers:
      output_answer(url, question, answer)

    if len(answers) is 0:
      wf.add_item(
          'No answers found', 
          'Select to view stack overflow question', 
          arg = url, 
          valid = True)
    wf.send_feedback()

  def output_answer(question_url, question_title, answer, subtitlePrefix = ""):
    answer_lines = answer_lines_by_priority(answer.find('.//div[@class="post-text"]'))
    wf.add_item(
      get_line(answer_lines, 0), 
      subtitlePrefix + question_title,
      copytext = get_line(answer_lines, 0),
      largetext = answer.find('.//div[@class="post-text"]').text_content(),
      autocomplete = "answer:" + question_url,
      arg = question_url + "#" + answer.attrib["id"],
      valid = True,
      icon = "appbar.check.png")

  def search_google_api(query):
    response = requests.get('http://ajax.googleapis.com/ajax/services/search/web?v=1.0', params={'q': query})

    parsedResponse = json.loads(response.content)

    if parsedResponse['responseDetails'] != None:
      wf.add_item(
        'Google API limit has been hit: press enter to open google search', 
        parsedResponse['responseDetails'], 
        arg = 'http://www.google.com/search?' + urllib.urlencode({'q': query}),
        valid = True,
        icon = ICON_ERROR)

    if parsedResponse['responseData'] is None:
      return []

    return parsedResponse['responseData']['results']

  def search_google(query):
    response = requests.get('http://www.google.com/search', params={'q': query})
    tree = html.fromstring(response.text)

    return map(lambda a: {"url": get_google_link_url(a.attrib["href"])}, tree.xpath('//h3[@class="r"]//a'))

  def get_google_link_url(url):
    if url.startswith("/url?"):
      return re.search("url\?q=([^&]*)", url).group(1)
    else:
      return url

  def get_stack_overflow_answers(resp):
    tree = html.fromstring(resp.text)
    return tree.xpath('//div[@id="answers"]//div[@itemtype="http://schema.org/Answer"]')

  def get_question_title(resp):
    tree = html.fromstring(resp.text)
    return tree.xpath('//div[@id="question-header"]//h1//a')[0].text_content()

  def answer_lines_by_priority(element):
    lines = []

    for child in element:
      if child.tag == 'pre':
        lines.append(child.text_content())

    for child in element:
      if child.tag != 'pre':
        lines.append(child.text_content())

    return map(lambda l: l.replace('\n', '    '), lines)

  def get_line(lines, num):
    if len(lines) <= num:
      return 'No text found'
    else:
      return lines[num]

  search(wf.args[0])

if __name__ == '__main__':
    wf = Workflow(libraries=['./lib'], update_settings={
        'github_slug': 'Que3216/alfred-stack-overflow',
        'version': __version__,
        # Optional number of days between checks for updates
        'frequency': 1
    })
    sys.exit(wf.run(main))
