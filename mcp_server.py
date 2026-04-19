from mcp.server.fastmcp import FastMCP

mcp = FastMCP("DocumentMCP", log_level="ERROR")

docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

# Read doc tool
@mcp.tool()
def read_doc(doc_id: str) -> str:
    """Reads the content of a document. The doc_id is exactly the filename (e.g., 'report.pdf' or 'plan.md')."""
    return docs.get(doc_id, f"Error: Document '{doc_id}' not found.")

# Edit doc tool
@mcp.tool()
def edit_doc(doc_id: str, content: str) -> str:
    """Edits an existing document or creates a new one. The doc_id is exactly the filename (e.g., 'report.pdf')."""
    docs[doc_id] = content
    return f"Success: Document '{doc_id}' has been saved/updated."

# Return doc id
@mcp.resource("docs://documents")
def list_docs() -> str:
    """Returns a list of all available document IDs."""
    return "\n".join(docs.keys())

# Return content of doc
@mcp.resource("docs://documents/{doc_id}")
def get_doc(doc_id: str) -> str:
    """Returns the specific content of a document."""
    return docs.get(doc_id, "Document not found.")

# Rewrite doc to markdown
@mcp.prompt()
def rewrite_markdown(doc_id: str) -> str:
    """Prompt to rewrite a document in markdown format."""
    content = docs.get(doc_id, "No content found.")
    return f"Please rewrite the following document in a well-structured markdown format:\n\n{content}"

# Summarize doc in bulleted format
@mcp.prompt()
def summarize_doc(doc_id: str) -> str:
    """Prompt to summarize a document."""
    content = docs.get(doc_id, "No content found.")
    return f"Please provide a concise, bulleted summary of the following document:\n\n{content}"

if __name__ == "__main__":
    mcp.run(transport="stdio")