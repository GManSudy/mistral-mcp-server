# Unified image for every MCP server in this repo.
# Select the server via MCP_ENTRYPOINT (path to the entry script)
# and optional MCP_ARGS (e.g. "--http --port 8000").
#
# Examples:
#   docker build -t mcp-servers .
#   docker run -p 8000:8000 --env-file .env mcp-servers                       # OpenProject HTTP
#   docker run -p 8001:8000 --env-file .env -e MCP_ENTRYPOINT=apps/mcp/trello_mcp.py \
#     -e MCP_ARGS="--http --port 8000" mcp-servers                             # Trello HTTP
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV MCP_ENTRYPOINT=openproject-mcp-http.py
ENV MCP_ARGS=""
EXPOSE 8000
CMD ["sh", "-c", "python ${MCP_ENTRYPOINT} ${MCP_ARGS}"]
