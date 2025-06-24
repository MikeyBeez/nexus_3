#!/bin/bash

PLIST_NAME="com.mikeybee.nexus3"
PLIST_FILE="/Users/bard/Code/nexus_3/com.mikeybee.nexus3.plist"
LAUNCHD_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

case "$1" in
    install)
        echo "Installing Nexus_3 service..."
        mkdir -p /Users/bard/Code/nexus_3/logs
        cp "$PLIST_FILE" "$LAUNCHD_PATH"
        launchctl load "$LAUNCHD_PATH"
        echo "Service installed and started"
        ;;
        
    uninstall)
        echo "Uninstalling Nexus_3 service..."
        launchctl unload "$LAUNCHD_PATH" 2>/dev/null
        rm -f "$LAUNCHD_PATH"
        echo "Service uninstalled"
        ;;
        
    start)
        echo "Starting Nexus_3 service..."
        launchctl start "$PLIST_NAME"
        ;;
        
    stop)
        echo "Stopping Nexus_3 service..."
        launchctl stop "$PLIST_NAME"
        ;;
        
    restart)
        echo "Restarting Nexus_3 service..."
        launchctl stop "$PLIST_NAME"
        sleep 2
        launchctl start "$PLIST_NAME"
        echo "Service restarted"
        ;;
        
    status)
        echo "Nexus_3 service status:"
        launchctl list | grep "$PLIST_NAME"
        ;;
        
    logs)
        echo "=== Nexus_3 Logs ==="
        tail -f /Users/bard/Code/nexus_3/logs/nexus.log
        ;;
        
    errors)
        echo "=== Nexus_3 Error Logs ==="
        tail -f /Users/bard/Code/nexus_3/logs/nexus-error.log
        ;;
        
    *)
        echo "Usage: $0 {install|uninstall|start|stop|restart|status|logs|errors}"
        exit 1
        ;;
esac
