from balatro_agent.tools.docling import DoclingTool

import os

print(os.getcwd())

image_path = "./images/sample.jpg"

example_tool = DoclingTool()
out = example_tool.forward(image_path)
print("Extracted Markdown Content:")
print(out)
