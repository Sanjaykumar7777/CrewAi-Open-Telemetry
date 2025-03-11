from crewai_tools import ScrapeWebsiteTool, FileWriterTool, TXTSearchTool
import requests


tool = ScrapeWebsiteTool(website_url='https://en.wikipedia.org/wiki/Artificial_intelligence')  

# Extract the text
text = tool.run()
print(text)

file_writer_tool = FileWriterTool()

# content to a file in a specified directory
result = file_writer_tool._run(filename='ai.txt', content = text, directory = '', overwrite=True)
print(result)

import os
from crewai_tools import TXTSearchTool

import os
os.environ['OPENAI_API_KEY'] = ''

tool = TXTSearchTool(txt='ai.txt')

from crewai import Agent, Task, Crew

context = tool.run('What is natural language processing?')

data_analyst = Agent(
    role='Educator',
    goal=f'Based on the context provided, answer the question - What is Natural Language Processing? Context - {context}',
    backstory='You are a data expert',
    verbose=True,
    allow_delegation=False,
    tools=[tool]
)

test_task = Task(
    description="Understand the topic and give the correct response",
    tools=[tool],
    agent=data_analyst,
    expected_output='Give a correct response'
)

crew = Crew(
    agents=[data_analyst],
    tasks=[test_task]
)

output = crew.kickoff()