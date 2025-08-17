#!/bin/bash
# Stop all MCP servers in the monorepo

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

print_status "Stopping MCP Monorepo servers..."

# Function to stop a server
stop_server() {
    local server_name=$1
    local pid_file="${server_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_status "Stopping $server_name (PID: $pid)..."
            kill "$pid"
            
            # Wait for process to terminate
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            if ps -p "$pid" > /dev/null 2>&1; then
                print_warning "$server_name did not stop gracefully, force killing..."
                kill -9 "$pid"
            fi
            
            rm -f "$pid_file"
            print_status "$server_name stopped"
        else
            print_warning "$server_name was not running (PID: $pid)"
            rm -f "$pid_file"
        fi
    else
        print_warning "PID file not found for $server_name"
    fi
}

# Stop Database Server
stop_server "database-server"

# Stop Filesystem Server
stop_server "filesystem-server"

# Also kill any remaining Python processes that might be our servers
print_status "Cleaning up any remaining server processes..."

# Kill processes listening on our ports
for port in 3003 3004; do
    pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        print_status "Killing processes on port $port: $pids"
        echo "$pids" | xargs kill -9 2>/dev/null || true
    fi
done

print_status "All servers stopped!"


