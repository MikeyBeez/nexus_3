#!/bin/bash

PLIST_NAME="com.mikeybee.nexus3"
PLIST_FILE="/Users/bard/Code/nexus_3/com.mikeybee.nexus3.plist"
LAUNCHD_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

case "$1" in
    install)
        echo "Installing Nexus_3 service..."
        
        # First, unload if already loaded
        if launchctl list | grep -q "$PLIST_NAME"; then
            echo "Service already loaded, unloading first..."
            launchctl unload "$LAUNCHD_PATH" 2>/dev/null
            sleep 2
        fi
        
        # Create logs directory
        mkdir -p /Users/bard/Code/nexus_3/logs
        
        # Copy plist file
        cp "$PLIST_FILE" "$LAUNCHD_PATH"
        
        # Load the service
        if launchctl load "$LAUNCHD_PATH" 2>&1; then
            echo "Service installed and started successfully"
        else
            echo "Note: Service may already be loaded. Check status with: $0 status"
        fi
        ;;
        
    uninstall)
        echo "Uninstalling Nexus_3 service..."
        launchctl unload "$LAUNCHD_PATH" 2>/dev/null
        rm -f "$LAUNCHD_PATH"
        echo "Service uninstalled"
        ;;
        
    start)
        echo "Starting Nexus_3 service..."
        if launchctl list | grep -q "$PLIST_NAME"; then
            launchctl start "$PLIST_NAME"
            echo "Service start command sent"
        else
            echo "Service not loaded. Run: $0 install"
        fi
        ;;
        
    stop)
        echo "Stopping Nexus_3 service..."
        if launchctl list | grep -q "$PLIST_NAME"; then
            launchctl stop "$PLIST_NAME"
            echo "Service stop command sent"
        else
            echo "Service not loaded"
        fi
        ;;
        
    restart)
        echo "Restarting Nexus_3 service..."
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        echo "Nexus_3 service status:"
        if launchctl list | grep "$PLIST_NAME"; then
            echo ""
            # Check if API is responding
            if curl -s http://localhost:8100/health > /dev/null 2>&1; then
                echo "API Status: ✅ Running on port 8100"
            else
                echo "API Status: ❌ Not responding on port 8100"
            fi
        else
            echo "Service not loaded in launchctl"
        fi
        ;;
        
    logs)
        echo "=== Nexus_3 Logs ==="
        if [ -f "/Users/bard/Code/nexus_3/logs/nexus.log" ]; then
            tail -f /Users/bard/Code/nexus_3/logs/nexus.log
        else
            echo "Log file not found. Service may not have started yet."
        fi
        ;;
        
    errors)
        echo "=== Nexus_3 Error Logs ==="
        if [ -f "/Users/bard/Code/nexus_3/logs/nexus-error.log" ]; then
            tail -f /Users/bard/Code/nexus_3/logs/nexus-error.log
        else
            echo "Error log file not found."
        fi
        ;;
        
    *)
        echo "Usage: $0 {install|uninstall|start|stop|restart|status|logs|errors}"
        exit 1
        ;;
esac
