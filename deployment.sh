#!/bin/bash
set -euo pipefail

DEPLOY_DIR="/opt/mcp-server"
SERVICE_NAME="production-mcp-server"
BACKUP_DIR="/opt/mcp-server/backups"

echo "🚀 Starting MCP Server Production Deployment"

# Create backup
echo "📦 Creating backup..."
mkdir -p "$BACKUP_DIR"
if [ -d "$DEPLOY_DIR" ]; then
    tar -czf "$BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S).tar.gz" -C "$DEPLOY_DIR" .
fi

# Stop existing service
echo "🛑 Stopping existing service..."
sudo systemctl stop "$SERVICE_NAME" || true

# Deploy new version
echo "📁 Deploying new version..."
sudo mkdir -p "$DEPLOY_DIR"
sudo cp production_mcp_server.py "$DEPLOY_DIR/"
sudo cp health_check.py "$DEPLOY_DIR/"
sudo cp requirements.txt "$DEPLOY_DIR/"

# Install dependencies
echo "📦 Installing dependencies..."
cd "$DEPLOY_DIR"
sudo pip install -r requirements.txt

# Set permissions
echo "🔐 Setting permissions..."
sudo chown -R mcpuser:mcpuser "$DEPLOY_DIR"
sudo chmod +x "$DEPLOY_DIR/production_mcp_server.py"

# Install/update systemd service
echo "⚙️  Installing systemd service..."
sudo cp production-mcp-server.service /etc/systemd/system/
sudo systemctl daemon-reload

# Start service
echo "▶️  Starting service..."
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

# Verify deployment
echo "✅ Verifying deployment..."
sleep 5
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ Deployment successful!"
    echo "📊 Service status:"
    sudo systemctl status "$SERVICE_NAME" --no-pager
else
    echo "❌ Deployment failed!"
    echo "📝 Service logs:"
    sudo journalctl -u "$SERVICE_NAME" --no-pager -n 20
    exit 1
fi

echo "🎉 Production deployment complete!"
echo "🔗 Server should be available at: https://your-domain.com:3001"