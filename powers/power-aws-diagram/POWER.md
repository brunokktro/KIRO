---
name: "power-aws-diagram"
displayName: "AWS Diagram MCP"
description: "Generate AWS architecture diagrams, sequence diagrams, flow charts, and class diagrams using Python diagrams DSL. Creates professional diagrams from code."
keywords: ["aws-diagram", "diagrams", "architecture", "sequence-diagram", "flowchart", "class-diagram", "python-diagrams"]
author: "Bruno Lopes"
---

# AWS Diagram MCP

## Overview

Power for the AWS Diagram MCP server — generates professional diagrams using the Python `diagrams` package DSL. Supports AWS architecture diagrams, sequence diagrams, flow charts, and class diagrams.

> **Note:** This server is deprecated by awslabs in favor of the diagram agent skill in the deploy-on-aws plugin. However, it still works and is useful for standalone diagram generation.

## Available Tools

- **create_diagram** — Generate a diagram from Python diagrams DSL code
- **list_icons** — List available icons from the diagrams package (providers, services)
- **get_diagram_examples** — Get example diagram code for reference

## Supported Diagram Types

| Type | Description |
|------|-------------|
| AWS Architecture | VPC, Lambda, S3, EC2, EKS, etc. |
| Sequence Diagrams | Interaction flows between components |
| Flow Charts | Process and decision flows |
| Class Diagrams | Object-oriented class relationships |

## Quick Example

```python
from diagrams import Diagram
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.network import APIGateway

with Diagram("Serverless Application", show=False):
    api = APIGateway("API Gateway")
    function = Lambda("Function")
    database = Dynamodb("DynamoDB")
    api >> function >> database
```

## Prerequisites

- Python 3.10+ with `uvx` installed
- GraphViz installed: `brew install graphviz`

## Configuration

No additional configuration needed. Uses `uvx` to run `awslabs.aws-diagram-mcp-server`.

## Troubleshooting

### Server won't start
- Verify uvx: `which uvx`
- Verify GraphViz: `which dot` (GraphViz binary)
- Install if missing: `brew install graphviz`

### Diagram generation fails
- Check Python diagrams package is accessible via uvx
- Verify code syntax matches diagrams DSL
- Use `list_icons` to find correct icon names
