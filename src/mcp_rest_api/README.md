# REST API MCP Server

## Description
The REST API MCP Server provides tools for interacting with REST APIs, specifically the resume generation API. This server acts as a bridge between Claude Desktop and external REST services, allowing you to generate, manage, and download resumes through MCP tools.

## Tools

### `generate_resume`
Generates a Word document resume from JSON data.

**Parameters:**
- `contact_info` (object): Contact information including name, location, phone, email, linkedin, medium
- `summary` (string): Professional summary
- `skills` (array): List of skills
- `experience` (array): Work experience entries with company, title, summary, accomplishments
- `education` (array): Education entries with institution, degree, field, graduation year

### `list_resumes`
Lists all generated resumes with metadata.

**Parameters:** None

### `download_resume`
Downloads a specific resume by ID.

**Parameters:**
- `resume_id` (string): ID of the resume to download

### `delete_resume`
Deletes a specific resume by ID.

**Parameters:**
- `resume_id` (string): ID of the resume to delete

### `get_resume_api_info`
Gets information about the resume API and available endpoints.

**Parameters:** None

## Configuration

### Environment Variables
- `MCP_AUTH_TOKEN`: Authentication token for the server
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `MCP_PORT`: Port number for the server (default: 3004)
- `RESUME_API_URL`: URL of the resume API service (default: http://dev01.int.stortz.tech:8002)

## Usage

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate

# Run server
python -m mcp_rest_api --host 0.0.0.0 --port 3004 --log-level INFO --no-auth
```

### Docker
```bash
# Build and run
./scripts/build-rest-api-mcp.sh
./scripts/run-rest-api-mcp.sh

# Or deploy all servers
./scripts/run-all-servers.sh
```

### Individual Docker Compose
```bash
cd docker/mcp_rest_api
docker compose up -d
```

## Claude Desktop Configuration
Add this to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "rest-api-mcp": {
      "command": "socat",
      "args": ["-", "TCP:localhost:3004"],
      "env": {}
    }
  }
}
```

## API Integration

This MCP server integrates with the resume generation API available at `http://dev01.int.stortz.tech:8002`. The API provides the following endpoints:

- `POST /generate-resume`: Generate a Word document resume
- `GET /resumes`: List all generated resumes
- `GET /resumes/{resume_id}`: Download a specific resume
- `DELETE /resumes/{resume_id}`: Delete a specific resume

## Architecture

The REST API MCP Server follows the standard MCP architecture:

1. **JSON-RPC Protocol**: Implements the Model Context Protocol using JSON-RPC 2.0
2. **Tool Registry**: Maintains a registry of available tools with input schemas
3. **HTTP Client**: Uses aiohttp for making HTTP requests to external APIs
4. **Error Handling**: Comprehensive error handling for API failures and network issues
5. **Authentication**: Supports token-based authentication
6. **File Handling**: Handles file downloads and base64 encoding for binary data

## Example Usage

### Generate a Resume
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "generate_resume",
    "arguments": {
      "contact_info": {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "(555) 123-4567",
        "location": "San Francisco, CA"
      },
      "summary": "Experienced software engineer with 5+ years in web development",
      "skills": ["Python", "JavaScript", "React", "Node.js"],
      "experience": [
        {
          "company": "Tech Corp",
          "title": "Senior Developer",
          "summary": "Led development of web applications",
          "accomplishments": ["Improved performance by 50%", "Mentored junior developers"]
        }
      ]
    }
  }
}
```

### List Resumes
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "list_resumes",
    "arguments": {}
  }
}
```

## Error Handling

The server provides comprehensive error handling:

- **API Errors**: HTTP status codes and error messages from external APIs
- **Network Errors**: Connection timeouts and network failures
- **Validation Errors**: Missing required fields and invalid data
- **Authentication Errors**: Invalid or missing authentication tokens

## Security

- **Non-root User**: Docker containers run as non-root user
- **Environment Variables**: Sensitive configuration via environment variables
- **Authentication**: Optional token-based authentication
- **Input Validation**: Comprehensive validation of tool parameters

## Monitoring

- **Health Checks**: Docker health checks for container monitoring
- **Logging**: Structured logging with configurable levels
- **Metrics**: Request metrics and performance monitoring
- **Resource Limits**: Memory and CPU limits for container resources

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check if the resume API is accessible at the configured URL
2. **Authentication Errors**: Verify the MCP_AUTH_TOKEN is set correctly
3. **Port Conflicts**: Ensure port 3004 is available
4. **File Download Issues**: Check network connectivity and API response format

### Debug Mode
```bash
# Run with debug logging
python -m mcp_rest_api --log-level DEBUG --no-auth
```

### Docker Logs
```bash
# View container logs
docker logs rest-api-mcp-server

# Follow logs in real-time
docker logs -f rest-api-mcp-server
```
