#!/bin/bash
# Aktiviert die virtuelle Python-Umgebung für das Qolaba MCP Server Projekt

echo "🚀 Aktiviere virtuelle Python-Umgebung für Qolaba MCP Server..."
source .venv/bin/activate

echo "✅ Virtuelle Umgebung aktiviert!"
echo "🐍 Python Version: $(python --version)"
echo "📦 pip Version: $(pip --version)"
echo ""
echo "💡 Zum Deaktivieren verwenden Sie: deactivate"