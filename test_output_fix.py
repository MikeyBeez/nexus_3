#!/usr/bin/env python3
"""
Test output capture after fix
"""
import json
import time
import urllib.request

print("Testing Nexus_3 output capture fix...")
print("=" * 50)

# Simple echo test
task = {
    "type": "generation",
    "description": "Test output capture",
    "parameters": {
        "command": "echo",
        "args": ["SUCCESS! Output capture is working!"],
        "capture_output": True
    },
    "priority": 10
}

# Submit task
req = urllib.request.Request(
    "http://localhost:8100/tasks",
    data=json.dumps(task).encode(),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())
        task_id = result['id']
        print(f"Task created: {task_id}")
except Exception as e:
    print(f"Error creating task: {e}")
    print("Make sure Nexus_3 is running on port 8100")
    exit(1)

# Wait for completion
print("Waiting for result", end="", flush=True)
for i in range(5):
    time.sleep(1)
    print(".", end="", flush=True)

    with urllib.request.urlopen(f"http://localhost:8100/tasks/{task_id}") as r:
        task_result = json.loads(r.read())
        
        if task_result['status'] in ['completed', 'failed']:
            print(f"\n\nStatus: {task_result['status']}")
            
            result = task_result.get('result', {})
            
            # Check if we have real output now
            if isinstance(result, dict) and 'stdout' in result:
                print("✅ OUTPUT CAPTURE FIXED!")
                print(f"Exit code: {result.get('exit_code', 'N/A')}")
                print(f"Stdout: {result['stdout'].strip()}")
                if result.get('stderr'):
                    print(f"Stderr: {result['stderr'].strip()}")
            else:
                print("❌ Still returning mock results")
                print(f"Result: {json.dumps(result, indent=2)}")
            break

print("\n" + "=" * 50)

# Test Python execution
print("\nTesting Python output...")
task2 = {
    "type": "generation",
    "description": "Test Python output",
    "parameters": {
        "command": "python3",
        "args": ["-c", "print('Python output works!'); print('Line 2'); import sys; print(f'Python {sys.version.split()[0]}')"],
        "capture_output": True
    },
    "priority": 10
}

req2 = urllib.request.Request(
    "http://localhost:8100/tasks",
    data=json.dumps(task2).encode(),
    headers={'Content-Type': 'application/json'}
)

with urllib.request.urlopen(req2) as r:
    result2 = json.loads(r.read())
    task_id2 = result2['id']

time.sleep(2)

with urllib.request.urlopen(f"http://localhost:8100/tasks/{task_id2}") as r:
    task_result2 = json.loads(r.read())
    result2 = task_result2.get('result', {})
    
    if result2.get('stdout'):
        print("✅ Python output captured:")
        print(result2['stdout'])
    else:
        print("❌ No Python output")
