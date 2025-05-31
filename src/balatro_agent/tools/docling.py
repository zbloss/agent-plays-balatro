from smolagents import Tool
from langchain_docling import DoclingLoader
from langchain_core.documents import Document


class DoclingTool(Tool):
    name: str = "docling_tool"
    description: str = "This tool takes an image and extracts text from it then returns the text as a string."
    inputs = {
        "image_path": {
            "type": "string",
            "description": "The path to the image file from which to extract text.",
        },
    }
    output_type = "string"

    def forward(self, image_path: str) -> str:
        """
        Extracts text from the provided image and returns it as markdown.

        Args:
            image_path (str): The path to the image file.

        Returns:
            str: The extracted text.
        """

        text = "No text extracted from the image."

        loader = DoclingLoader(image_path)
        docs: list[Document] = loader.lazy_load()
        if not docs:
            return text

        if isinstance(docs, list):
            if len(docs) == 0:
                return text

        document_content: str = [doc.page_content for doc in docs]
        document_content = "\n\n".join(document_content)

        return document_content
