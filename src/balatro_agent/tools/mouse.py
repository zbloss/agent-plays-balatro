from pyautogui import click, doubleClick, moveTo, rightClick, screenshot
from smolagents import Tool


class MouseTool(Tool):
    name: str = "mouse_tool"
    description: str = "A tool to control the mouse. It can click, double-click, right-click, and take screenshots."
    inputs: dict = {
        "action": {
            "type": "string",
            "description": "The action to perform: 'click', 'double_click', 'right_click', or 'screenshot'.",
        },
        "x": {
            "type": "integer",
            "description": "The x-coordinate for the mouse action.",
        },
        "y": {
            "type": "integer",
            "description": "The y-coordinate for the mouse action.",
        },
    }
    output_type: str = "string"

    def forward(self, action: str, x: int, y: int) -> str:
        """
        Perform the specified mouse action at the given coordinates.
        """
        if action == "click":
            click(x=x, y=y)
            return f"Clicked at ({x}, {y})"
        elif action == "double_click":
            doubleClick(x=x, y=y)
            return f"Double-clicked at ({x}, {y})"
        elif action == "right_click":
            rightClick(x=x, y=y)
            return f"Right-clicked at ({x}, {y})"
        elif action == "screenshot":
            screenshot_path = f"screenshot_{x}_{y}.png"
            screenshot(screenshot_path, region=(x, y, 100, 100))
            return f"Screenshot taken at ({x}, {y}) and saved as {screenshot_path}"
        else:
            return "Invalid action. Please use 'click', 'double_click', 'right_click', or 'screenshot'."
