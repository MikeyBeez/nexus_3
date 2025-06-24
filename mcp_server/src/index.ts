#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';

// Nexus API configuration
const NEXUS_API_URL = process.env.NEXUS_API_URL || 'http://localhost:8100';

// Tool definitions
const TOOLS = [
  {
    name: 'create_task',
    description: 'Create a new task in Nexus',
    inputSchema: {
      type: 'object',
      properties: {
        type: {
          type: 'string',
          enum: ['analysis', 'generation', 'transformation', 'orchestration'],
          description: 'Type of task'
        },
        description: {
          type: 'string',
          description: 'Task description'
        },
        parameters: {
          type: 'object',
          description: 'Task parameters'
        },
        priority: {
          type: 'number',
          minimum: 1,
          maximum: 10,
          default: 5
        }
      },
      required: ['type', 'description']
    }
  },
  {
    name: 'get_task',
    description: 'Get task status and details',
    inputSchema: {
      type: 'object',
      properties: {
        task_id: {
          type: 'string',
          description: 'Task ID'
        }
      },
      required: ['task_id']
    }
  },
  {
    name: 'list_tasks',
    description: 'List tasks with optional status filter',
    inputSchema: {
      type: 'object',
      properties: {
        status: {
          type: 'string',
          enum: ['pending', 'running', 'completed', 'failed', 'cancelled'],
          description: 'Filter by status'
        },
        limit: {
          type: 'number',
          default: 10
        }
      }
    }
  },
  {
    name: 'orchestrate',
    description: 'Orchestrate a complex goal across services',
    inputSchema: {
      type: 'object',
      properties: {
        goal: {
          type: 'string',
          description: 'Goal to achieve'
        },
        context: {
          type: 'object',
          description: 'Additional context'
        },
        max_steps: {
          type: 'number',
          default: 10
        }
      },
      required: ['goal']
    }
  },
  {
    name: 'check_health',
    description: 'Check Nexus system health',
    inputSchema: {
      type: 'object',
      properties: {}
    }
  }
];

// Create MCP server
const server = new Server(
  {
    name: 'nexus-mcp',
    version: '0.1.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Handle tool listing
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: TOOLS,
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'create_task': {
        const response = await axios.post(`${NEXUS_API_URL}/tasks`, args);
        return {
          content: [
            {
              type: 'text',
              text: `Task created: ${response.data.id}\nStatus: ${response.data.status}\nMessage: ${response.data.message}`
            }
          ]
        };
      }

      case 'get_task': {
        if (!args || !args.task_id) {
          throw new Error('task_id is required');
        }
        const response = await axios.get(`${NEXUS_API_URL}/tasks/${args.task_id}`);
        const task = response.data;
        return {
          content: [
            {
              type: 'text',
              text: `Task ${task.id}:\nType: ${task.type}\nStatus: ${task.status}\nDescription: ${task.description}\nCreated: ${task.created_at}\n${task.result ? 'Result: ' + JSON.stringify(task.result, null, 2) : ''}`
            }
          ]
        };
      }

      case 'list_tasks': {
        const params = new URLSearchParams();
        if (args?.status) params.append('status', String(args.status));
        if (args?.limit) params.append('limit', String(args.limit));
        
        const response = await axios.get(`${NEXUS_API_URL}/tasks?${params}`);
        const tasks = response.data;
        
        const taskList = tasks.map((t: any) => 
          `- ${t.id} [${t.type}]: ${t.description} (${t.status})`
        ).join('\n');
        
        return {
          content: [
            {
              type: 'text',
              text: `Tasks (${tasks.length}):\n${taskList || 'No tasks found'}`
            }
          ]
        };
      }

      case 'orchestrate': {
        const response = await axios.post(`${NEXUS_API_URL}/orchestrate`, args);
        const orch = response.data;
        
        const steps = orch.steps.map((s: any) => 
          `Step ${s.step_number}: ${s.action} via ${s.service} - ${s.status}`
        ).join('\n');
        
        return {
          content: [
            {
              type: 'text',
              text: `Orchestration ${orch.id}:\nGoal: ${orch.goal}\nStatus: ${orch.status}\n\nSteps:\n${steps}`
            }
          ]
        };
      }

      case 'check_health': {
        const response = await axios.get(`${NEXUS_API_URL}/health`);
        const health = response.data;
        
        const services = health.services.map((s: any) => 
          `- ${s.name}: ${s.status} (${s.healthy ? 'healthy' : 'unhealthy'})`
        ).join('\n');
        
        return {
          content: [
            {
              type: 'text',
              text: `Nexus Health:\nStatus: ${health.status}\nVersion: ${health.version}\nUptime: ${Math.round(health.uptime_seconds)}s\n\nServices:\n${services}`
            }
          ]
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error: any) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error.response?.data?.detail || error.message}`
        }
      ]
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Nexus MCP server started');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
