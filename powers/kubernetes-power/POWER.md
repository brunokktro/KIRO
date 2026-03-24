---
name: "kubernetes-power"
displayName: "Kubernetes Power"
description: "Complete Kubernetes cluster management with kubectl operations, Helm charts, pod logs, resource management, and troubleshooting. Control your K8s clusters from Kiro."
keywords: ["kubernetes", "k8s", "kubectl", "helm", "pods", "containers", "kubectl-commands"]
author: "Kiro Team"
---

# Kubernetes Power

## Overview

Kubernetes Power provides comprehensive cluster management capabilities, replacing the need to switch between terminal and IDE. Execute kubectl commands, manage Helm charts, inspect resources, view logs, and troubleshoot issues directly from Kiro.

Key capabilities:
- Resource management (get, describe, create, apply, delete, patch)
- Pod operations (logs, exec, port-forward)
- Helm chart management (install, upgrade, uninstall)
- Node management (cordon, drain, uncordon)
- Context switching and API resource discovery
- Rollout management for deployments
- Generic kubectl command execution

Perfect for DevOps engineers, SREs, and developers working with Kubernetes clusters.

## Onboarding

### Prerequisites
- Kubernetes cluster access
- kubectl configured with valid kubeconfig
- Helm installed (for Helm operations)
- Appropriate RBAC permissions in your clusters

### Installation

The Kubernetes MCP server works with your existing kubectl configuration. No additional setup required beyond having kubectl configured.

### Configuration

The MCP server uses your default kubeconfig (`~/.kube/config`). You can switch contexts using the `kubectl_context` tool.

## Common Workflows

### Workflow 1: List and Inspect Resources

**List Pods:**
```
Use tool: kubectl_get
Parameters:
  resourceType: "pods"
  namespace: "default"
  output: "json"
```

**Describe Pod:**
```
Use tool: kubectl_describe
Parameters:
  resourceType: "pods"
  name: "my-pod"
  namespace: "default"
```

**List with Labels:**
```
Use tool: kubectl_get
Parameters:
  resourceType: "pods"
  namespace: "production"
  labelSelector: "app=nginx,tier=frontend"
```

---

### Workflow 2: View Pod Logs

**Basic Logs:**
```
Use tool: kubectl_logs
Parameters:
  resourceType: "pod"
  name: "my-pod"
  namespace: "default"
  tail: 100
```

**Follow Logs (not recommended):**
```
Use tool: kubectl_logs
Parameters:
  resourceType: "pod"
  name: "my-pod"
  namespace: "default"
  follow: false
  timestamps: true
```

**Previous Container Logs:**
```
Use tool: kubectl_logs
Parameters:
  resourceType: "pod"
  name: "my-pod"
  namespace: "default"
  previous: true
```

---

### Workflow 3: Apply Kubernetes Manifests

**From YAML String:**
```
Use tool: kubectl_apply
Parameters:
  manifest: |
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: my-config
    data:
      key: value
  namespace: "default"
```

**From File:**
```
Use tool: kubectl_apply
Parameters:
  filename: "/path/to/manifest.yaml"
  namespace: "default"
```

---

### Workflow 4: Create Resources

**Create Namespace:**
```
Use tool: kubectl_create
Parameters:
  resourceType: "namespace"
  name: "my-namespace"
```

**Create Deployment:**
```
Use tool: kubectl_create
Parameters:
  resourceType: "deployment"
  name: "nginx-deployment"
  image: "nginx:latest"
  replicas: 3
  port: 80
  namespace: "default"
```

**Create ConfigMap:**
```
Use tool: kubectl_create
Parameters:
  resourceType: "configmap"
  name: "app-config"
  fromLiteral: ["KEY1=value1", "KEY2=value2"]
  namespace: "default"
```

---

### Workflow 5: Delete Resources

**Delete Pod:**
```
Use tool: kubectl_delete
Parameters:
  resourceType: "pod"
  name: "my-pod"
  namespace: "default"
```

**Delete by Label:**
```
Use tool: kubectl_delete
Parameters:
  resourceType: "pods"
  labelSelector: "app=old-version"
  namespace: "default"
```

---

### Workflow 6: Scale Deployments

**Scale Up/Down:**
```
Use tool: kubectl_scale
Parameters:
  resourceType: "deployment"
  name: "my-deployment"
  replicas: 5
  namespace: "default"
```

---

### Workflow 7: Manage Rollouts

**Check Rollout Status:**
```
Use tool: kubectl_rollout
Parameters:
  subCommand: "status"
  resourceType: "deployment"
  name: "my-deployment"
  namespace: "default"
```

**Restart Deployment:**
```
Use tool: kubectl_rollout
Parameters:
  subCommand: "restart"
  resourceType: "deployment"
  name: "my-deployment"
  namespace: "default"
```

**Rollback:**
```
Use tool: kubectl_rollout
Parameters:
  subCommand: "undo"
  resourceType: "deployment"
  name: "my-deployment"
  namespace: "default"
```

---

### Workflow 8: Patch Resources

**Update Image:**
```
Use tool: kubectl_patch
Parameters:
  resourceType: "deployment"
  name: "my-deployment"
  namespace: "default"
  patchType: "strategic"
  patchData: {
    "spec": {
      "template": {
        "spec": {
          "containers": [{
            "name": "app",
            "image": "myapp:v2"
          }]
        }
      }
    }
  }
```

---

### Workflow 9: Execute Commands in Pods

**Run Command:**
```
Use tool: exec_in_pod
Parameters:
  name: "my-pod"
  namespace: "default"
  command: ["ls", "-la", "/app"]
```

**Check Environment:**
```
Use tool: exec_in_pod
Parameters:
  name: "my-pod"
  namespace: "default"
  command: ["env"]
```

---

### Workflow 10: Port Forwarding

**Forward Port:**
```
Use tool: port_forward
Parameters:
  resourceType: "pod"
  resourceName: "my-pod"
  localPort: 8080
  targetPort: 80
  namespace: "default"
```

**Stop Port Forward:**
```
Use tool: stop_port_forward
Parameters:
  id: "port-forward-id"
```

---

### Workflow 11: Helm Chart Management

**Install Chart:**
```
Use tool: install_helm_chart
Parameters:
  name: "my-release"
  chart: "nginx"
  repo: "https://charts.bitnami.com/bitnami"
  namespace: "default"
  values: {
    "replicaCount": 3,
    "service": {
      "type": "LoadBalancer"
    }
  }
```

**Upgrade Chart:**
```
Use tool: upgrade_helm_chart
Parameters:
  name: "my-release"
  chart: "nginx"
  namespace: "default"
  values: {
    "replicaCount": 5
  }
```

**Uninstall Chart:**
```
Use tool: uninstall_helm_chart
Parameters:
  name: "my-release"
  namespace: "default"
```

---

### Workflow 12: Node Management

**Cordon Node:**
```
Use tool: node_management
Parameters:
  operation: "cordon"
  nodeName: "node-1"
```

**Drain Node:**
```
Use tool: node_management
Parameters:
  operation: "drain"
  nodeName: "node-1"
  confirmDrain: true
  ignoreDaemonsets: true
  deleteLocalData: false
```

**Uncordon Node:**
```
Use tool: node_management
Parameters:
  operation: "uncordon"
  nodeName: "node-1"
```

---

### Workflow 13: Context Management

**List Contexts:**
```
Use tool: kubectl_context
Parameters:
  operation: "list"
```

**Get Current Context:**
```
Use tool: kubectl_context
Parameters:
  operation: "get"
```

**Switch Context:**
```
Use tool: kubectl_context
Parameters:
  operation: "set"
  name: "production-cluster"
```

---

### Workflow 14: Discover API Resources

**List Available Resources:**
```
Use tool: list_api_resources
```

**Filter by API Group:**
```
Use tool: list_api_resources
Parameters:
  apiGroup: "apps"
```

---

### Workflow 15: Get Resource Documentation

**Explain Resource:**
```
Use tool: explain_resource
Parameters:
  resource: "pods"
```

**Explain Nested Field:**
```
Use tool: explain_resource
Parameters:
  resource: "pods.spec.containers"
  recursive: true
```

## Troubleshooting

### Connection Refused

**Problem:** "Unable to connect to the server"
**Cause:** Cluster unreachable or kubeconfig invalid
**Solution:**
1. Verify cluster is running: `kubectl cluster-info`
2. Check kubeconfig is valid
3. Verify network connectivity
4. Check if context is correct

---

### Permission Denied

**Problem:** "Forbidden" or "User cannot..."
**Cause:** Insufficient RBAC permissions
**Solution:**
1. Check your user permissions
2. Verify service account has required roles
3. Contact cluster admin for access
4. Review RBAC policies

---

### Pod Not Found

**Problem:** "pods 'name' not found"
**Cause:** Pod doesn't exist or wrong namespace
**Solution:**
1. List pods to verify name: `kubectl_get`
2. Check namespace is correct
3. Verify pod hasn't been deleted
4. Check if using correct context

---

### Image Pull Errors

**Problem:** "ImagePullBackOff" or "ErrImagePull"
**Cause:** Cannot pull container image
**Solution:**
1. Verify image name and tag are correct
2. Check image registry is accessible
3. Verify image pull secrets if private registry
4. Check network policies allow registry access

---

### CrashLoopBackOff

**Problem:** Pod keeps restarting
**Cause:** Application crashes on startup
**Solution:**
1. Check pod logs: `kubectl_logs` with `previous: true`
2. Describe pod for events: `kubectl_describe`
3. Verify environment variables and config
4. Check resource limits aren't too restrictive
5. Exec into pod if it stays up long enough

## Best Practices

- Always specify namespace explicitly to avoid confusion
- Use labels for organizing and selecting resources
- Check rollout status before considering deployment complete
- Use `describe` to get detailed resource information and events
- Tail logs with reasonable line limits (avoid large outputs)
- Use `dryRun: true` to preview changes before applying
- Cordon nodes before draining for maintenance
- Use Helm for complex application deployments
- Keep contexts organized with descriptive names
- Use resource quotas and limits in production
- Regular backup of critical resources
- Monitor resource usage with `kubectl top` (via generic command)
- Use namespaces to isolate environments
- Apply manifests from version control, not ad-hoc strings

## Configuration

**No additional configuration required** - works with your existing kubectl setup.

**Kubeconfig Location:**
Default: `~/.kube/config`

**Context Management:**
Use `kubectl_context` tool to switch between clusters.

## MCP Config Placeholders

**No placeholders needed** - the Kubernetes MCP server uses your existing kubectl configuration automatically.

The mcp.json configuration works as-is with the standard npm package.

---

**Package:** `mcp-server-kubernetes`
**MCP Server:** kubernetes
