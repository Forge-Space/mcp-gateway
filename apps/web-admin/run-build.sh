#!/bin/bash
cd /Users/lucassantana/Desenvolvimento/mcp-gateway/apps/web-admin
npm run build > /Users/lucassantana/Desenvolvimento/mcp-gateway/apps/web-admin/build-result.txt 2>&1
echo "EXIT:$?" >> /Users/lucassantana/Desenvolvimento/mcp-gateway/apps/web-admin/build-result.txt
