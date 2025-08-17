#!/bin/bash
# Start all MCP servers in the monorepo

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the monorepo root directory"
    exit 1
fi

# Set environment variable for authentication
export MCP_AUTH_TOKEN="6b649d2159b61bf69f0a05fd9fe03bd8ead6f8414271b69149bce3fcd1326aec"

print_status "Starting MCP Monorepo servers..."

# Function to start a server in background
start_server() {
    local server_name=$1
    local script_path=$2
    local log_file=$3
    
    print_status "Starting $server_name..."
    
    if [ -f "$script_path" ]; then
        nohup bash -c "source venv/bin/activate && python3 $script_path" > "$log_file" 2>&1 &
        local pid=$!
        echo $pid > "${server_name}.pid"
        print_status "$server_name started with PID $pid"
    else
        print_error "Script not found: $script_path"
        return 1
    fi
}

# Start Database Server
start_server "database-server" "start_database_server.py" "database_mcp_server.log"

# Start Filesystem Server
start_server "filesystem-server" "start_filesystem_server.py" "filesystem_mcp_server.log"

# Wait a moment for servers to start
sleep 2

# Check if servers are running
print_status "Checking server status..."

check_server() {
    local server_name=$1
    local port=$2
    
    if curl -s "http://localhost:$port" > /dev/null 2>&1; then
        print_status "$server_name is running on port $port"
    else
        print_warning "$server_name may not be running on port $port"
    fi
}

check_server "Database Server" 3003
check_server "Filesystem Server" 3004

print_status "All servers started!"
print_status "Database Server: http://localhost:3003"
print_status "Filesystem Server: http://localhost:3004"
print_status "Logs: database_mcp_server.log, filesystem_mcp_server.log"
print_status "To stop servers: ./scripts/stop_all_servers.sh"


