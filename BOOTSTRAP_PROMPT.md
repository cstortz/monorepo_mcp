# Monorepo MCP Server Bootstrap Prompt

Use this prompt to quickly bootstrap a new MCP server for development. This prompt provides step-by-step instructions for setting up a new server in the monorepo.

## Quick Start

Copy and paste this prompt into your AI assistant to get started:

---

I want to create a new MCP server for [DATABASE_TYPE] in the monorepo_mcp project. Please help me bootstrap it for development.

**Database Type:** [DATABASE_TYPE] (e.g., MongoDB, Elasticsearch, Cassandra, Neo4j, InfluxDB, CouchDB, DynamoDB, SQLite, etc.)

**Server Name:** [SERVER_NAME] (e.g., mongodb_server, elasticsearch_server, etc.)

**Port:** [PORT] (e.g., 3005, 3006, etc.)

Please follow these steps:

1. **Create the server structure** using the template:
   ```bash
   cd /home/cstortz/repos/monorepo_mcp
   python shared/scripts/create_server.py [SERVER_NAME] [DATABASE_TYPE] [PORT]
   ```

2. **Update the configuration** in `servers/[SERVER_NAME]/config.yaml`:
   - Set the correct database host, port, and credentials
   - Update the server port if needed
   - Configure any database-specific settings

3. **Implement database-specific tools** in `servers/[SERVER_NAME]/server.py`:
   - Add tools for your specific database operations
   - Implement proper error handling
   - Add database-specific health checks
   - Include any custom functionality needed

4. **Create comprehensive tests** in `servers/[SERVER_NAME]/tests/`:
   - Test all database operations
   - Test error conditions
   - Test integration with the core components
   - Ensure admin tools are working

5. **Set up environment variables**:
   ```bash
   export MCP_AUTH_TOKEN="your-secure-auth-token"
   export [DATABASE_TYPE_UPPER]_PASSWORD="your-database-password"
   ```

6. **Test the server**:
   ```bash
   cd servers/[SERVER_NAME]
   python start.py
   ```

7. **Verify functionality**:
   - Check that the server starts without errors
   - Test admin tools (get_system_info, health_check, etc.)
   - Test database-specific tools
   - Verify security features are working

Please provide the specific implementation details for [DATABASE_TYPE], including:
- Database connection setup
- Specific tools and operations
- Error handling patterns
- Testing strategies
- Any database-specific considerations

---

## Database-Specific Considerations

### MongoDB
- Use pymongo for connection
- Implement collection operations
- Add aggregation pipeline support
- Handle BSON serialization

### Elasticsearch
- Use elasticsearch-py client
- Implement index operations
- Add search functionality
- Handle JSON document operations

### Cassandra
- Use cassandra-driver
- Implement keyspace and table operations
- Handle CQL queries
- Manage connection pooling

### Neo4j
- Use neo4j-driver
- Implement graph operations
- Add Cypher query support
- Handle graph traversal

### Redis
- Use redis-py
- Implement key-value operations
- Add data structure support
- Handle pub/sub functionality

### PostgreSQL/MySQL
- Use appropriate database driver
- Implement SQL operations
- Add transaction support
- Handle connection pooling

## Security Checklist

- [ ] Authentication token is properly configured
- [ ] IP filtering is set up correctly
- [ ] Rate limiting is configured
- [ ] SSL/TLS is enabled if needed
- [ ] Database credentials are secure
- [ ] Error messages don't leak sensitive information

## Testing Checklist

- [ ] Unit tests for all tools
- [ ] Integration tests with database
- [ ] Error condition tests
- [ ] Security tests
- [ ] Performance tests
- [ ] Admin tools tests

## Performance Considerations

- [ ] Connection pooling is implemented
- [ ] Queries are optimized
- [ ] Caching is used where appropriate
- [ ] Resource limits are set
- [ ] Monitoring is in place

## Documentation

- [ ] README is updated
- [ ] API documentation is complete
- [ ] Configuration examples are provided
- [ ] Troubleshooting guide is available

## Example Implementation

Here's a basic example for a new database server:

```python
class YourDatabaseTools:
    def get_tools(self):
        return {
            "database_health": {
                "name": "database_health",
                "description": "Check database health",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "your_custom_operation": {
                "name": "your_custom_operation",
                "description": "Perform custom database operation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "parameter": {
                            "type": "string",
                            "description": "Operation parameter"
                        }
                    },
                    "required": ["parameter"]
                }
            }
        }
    
    async def database_health(self, args, session):
        # Implement health check
        pass
    
    async def your_custom_operation(self, args, session):
        # Implement custom operation
        pass
```

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure the core module path is correct
2. **Configuration errors**: Check YAML syntax and environment variables
3. **Database connection issues**: Verify credentials and network connectivity
4. **Permission errors**: Check file permissions and database access rights

### Debug Mode

Enable debug logging by setting:
```yaml
logging:
  level: "DEBUG"
```

### Health Check

Use the built-in health check tool to verify server status:
```bash
# Test via MCP client
curl -X POST http://localhost:[PORT]/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "health_check", "arguments": {}}'
```

## Next Steps

After bootstrapping your server:

1. **Add to Claude Desktop configuration**:
   ```json
   {
     "mcpServers": {
       "[SERVER_NAME]": {
         "command": "python",
         "args": ["/path/to/monorepo_mcp/servers/[SERVER_NAME]/start.py"],
         "env": {
           "MCP_AUTH_TOKEN": "your-auth-token"
         }
       }
     }
   }
   ```

2. **Deploy to production**:
   - Set up proper logging
   - Configure monitoring
   - Set up SSL certificates
   - Configure load balancing if needed

3. **Contribute back**:
   - Update documentation
   - Add to the template
   - Share best practices
   - Report issues

---

This bootstrap prompt provides everything needed to quickly create a new MCP server in the monorepo. Just replace the placeholders with your specific database type and requirements.
