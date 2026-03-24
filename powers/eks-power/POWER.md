---
name: "eks-power"
displayName: "EKS Power"
description: "Comprehensive AWS EKS cluster management including cluster operations, node groups, add-ons, access entries, and pod identity associations. Full EKS lifecycle management from Kiro."
keywords: ["eks", "eks-cluster", "nodegroup", "fargate", "pod-identity", "managed-nodes", "eks-addon"]
author: "AWS Labs"
---

# EKS Power

## Overview

EKS Power provides complete AWS EKS cluster management capabilities, enabling you to create, configure, and manage EKS clusters without leaving your development environment. Handle cluster lifecycle, node groups, Fargate profiles, add-ons, and access management directly from Kiro.

Key capabilities:
- Cluster management (create, update, delete, describe)
- Node group operations (managed and self-managed)
- Fargate profile management
- EKS add-ons (install, update, remove)
- Access entries and policies
- Pod identity associations
- Cluster insights and recommendations
- VPC and networking configuration

Perfect for platform engineers, DevOps teams, and cloud architects managing EKS infrastructure.

## Onboarding

### Prerequisites
- AWS account with EKS permissions
- AWS CLI configured with credentials
- IAM permissions for EKS operations
- VPC and networking knowledge

### Installation

The EKS MCP server works with your AWS CLI configuration. Ensure your AWS credentials are properly configured.

### Configuration

The MCP server uses your default AWS credentials and region. You can specify different regions per operation.

## Common Workflows

### Workflow 1: Create EKS Cluster

**Goal:** Create a new EKS cluster

**Example:**
```
Use tool: create_cluster
Parameters:
  name: "my-eks-cluster"
  region: "us-east-1"
  version: "1.31"
  roleArn: "arn:aws:iam::123456789012:role/EKSClusterRole"
  resourcesVpcConfig: {
    "subnetIds": ["subnet-abc123", "subnet-def456"],
    "securityGroupIds": ["sg-xyz789"],
    "endpointPublicAccess": true,
    "endpointPrivateAccess": true
  }
```

**Key Parameters:**
- `name`: Cluster name (unique in region)
- `version`: Kubernetes version (1.28, 1.29, 1.30, 1.31)
- `roleArn`: IAM role for cluster
- `resourcesVpcConfig`: VPC configuration

---

### Workflow 2: List and Describe Clusters

**List All Clusters:**
```
Use tool: list_clusters
Parameters:
  region: "us-east-1"
```

**Describe Specific Cluster:**
```
Use tool: describe_cluster
Parameters:
  name: "my-eks-cluster"
  region: "us-east-1"
```

---

### Workflow 3: Update Cluster Configuration

**Update Kubernetes Version:**
```
Use tool: update_cluster_version
Parameters:
  name: "my-eks-cluster"
  region: "us-east-1"
  version: "1.31"
```

**Update Cluster Config:**
```
Use tool: update_cluster_config
Parameters:
  name: "my-eks-cluster"
  region: "us-east-1"
  resourcesVpcConfig: {
    "endpointPublicAccess": false,
    "endpointPrivateAccess": true
  }
```

---

### Workflow 4: Create Node Group

**Goal:** Add managed node group to cluster

**Example:**
```
Use tool: create_nodegroup
Parameters:
  clusterName: "my-eks-cluster"
  nodegroupName: "standard-nodes"
  region: "us-east-1"
  subnets: ["subnet-abc123", "subnet-def456"]
  nodeRole: "arn:aws:iam::123456789012:role/EKSNodeRole"
  scalingConfig: {
    "minSize": 2,
    "maxSize": 10,
    "desiredSize": 3
  }
  instanceTypes: ["t3.medium", "t3.large"]
  diskSize: 20
  amiType: "AL2_x86_64"
```

**AMI Types:**
- `AL2_x86_64` - Amazon Linux 2
- `AL2_x86_64_GPU` - Amazon Linux 2 with GPU
- `AL2_ARM_64` - Amazon Linux 2 ARM
- `BOTTLEROCKET_x86_64` - Bottlerocket
- `BOTTLEROCKET_ARM_64` - Bottlerocket ARM

---

### Workflow 5: Manage Node Groups

**List Node Groups:**
```
Use tool: list_nodegroups
Parameters:
  clusterName: "my-eks-cluster"
  region: "us-east-1"
```

**Describe Node Group:**
```
Use tool: describe_nodegroup
Parameters:
  clusterName: "my-eks-cluster"
  nodegroupName: "standard-nodes"
  region: "us-east-1"
```

**Update Node Group:**
```
Use tool: update_nodegroup_config
Parameters:
  clusterName: "my-eks-cluster"
  nodegroupName: "standard-nodes"
  region: "us-east-1"
  scalingConfig: {
    "minSize": 3,
    "maxSize": 15,
    "desiredSize": 5
  }
```

**Delete Node Group:**
```
Use tool: delete_nodegroup
Parameters:
  clusterName: "my-eks-cluster"
  nodegroupName: "old-nodes"
  region: "us-east-1"
```

---

### Workflow 6: Fargate Profile Management

**Create Fargate Profile:**
```
Use tool: create_fargate_profile
Parameters:
  clusterName: "my-eks-cluster"
  fargateProfileName: "app-profile"
  region: "us-east-1"
  podExecutionRoleArn: "arn:aws:iam::123456789012:role/EKSFargatePodRole"
  subnets: ["subnet-abc123", "subnet-def456"]
  selectors: [
    {
      "namespace": "production",
      "labels": {
        "app": "web"
      }
    }
  ]
```

**List Fargate Profiles:**
```
Use tool: list_fargate_profiles
Parameters:
  clusterName: "my-eks-cluster"
  region: "us-east-1"
```

**Delete Fargate Profile:**
```
Use tool: delete_fargate_profile
Parameters:
  clusterName: "my-eks-cluster"
  fargateProfileName: "old-profile"
  region: "us-east-1"
```

---

### Workflow 7: EKS Add-ons Management

**List Available Add-ons:**
```
Use tool: describe_addon_versions
Parameters:
  region: "us-east-1"
```

**Install Add-on:**
```
Use tool: create_addon
Parameters:
  clusterName: "my-eks-cluster"
  addonName: "vpc-cni"
  region: "us-east-1"
  addonVersion: "v1.18.0-eksbuild.1"
  resolveConflicts: "OVERWRITE"
```

**Common Add-ons:**
- `vpc-cni` - VPC CNI networking
- `coredns` - CoreDNS
- `kube-proxy` - Kube-proxy
- `aws-ebs-csi-driver` - EBS CSI driver
- `aws-efs-csi-driver` - EFS CSI driver
- `amazon-cloudwatch-observability` - CloudWatch observability

**Update Add-on:**
```
Use tool: update_addon
Parameters:
  clusterName: "my-eks-cluster"
  addonName: "vpc-cni"
  region: "us-east-1"
  addonVersion: "v1.18.1-eksbuild.1"
  resolveConflicts: "OVERWRITE"
```

**Delete Add-on:**
```
Use tool: delete_addon
Parameters:
  clusterName: "my-eks-cluster"
  addonName: "old-addon"
  region: "us-east-1"
```

---

### Workflow 8: Access Entry Management

**Create Access Entry:**
```
Use tool: create_access_entry
Parameters:
  clusterName: "my-eks-cluster"
  principalArn: "arn:aws:iam::123456789012:user/developer"
  region: "us-east-1"
  type: "STANDARD"
  kubernetesGroups: ["developers"]
```

**List Access Entries:**
```
Use tool: list_access_entries
Parameters:
  clusterName: "my-eks-cluster"
  region: "us-east-1"
```

**Associate Access Policy:**
```
Use tool: associate_access_policy
Parameters:
  clusterName: "my-eks-cluster"
  principalArn: "arn:aws:iam::123456789012:user/developer"
  policyArn: "arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy"
  region: "us-east-1"
  accessScope: {
    "type": "cluster"
  }
```

**Delete Access Entry:**
```
Use tool: delete_access_entry
Parameters:
  clusterName: "my-eks-cluster"
  principalArn: "arn:aws:iam::123456789012:user/old-user"
  region: "us-east-1"
```

---

### Workflow 9: Pod Identity Associations

**Create Pod Identity Association:**
```
Use tool: create_pod_identity_association
Parameters:
  clusterName: "my-eks-cluster"
  namespace: "production"
  serviceAccount: "app-service-account"
  roleArn: "arn:aws:iam::123456789012:role/AppRole"
  region: "us-east-1"
```

**List Pod Identity Associations:**
```
Use tool: list_pod_identity_associations
Parameters:
  clusterName: "my-eks-cluster"
  region: "us-east-1"
```

**Delete Pod Identity Association:**
```
Use tool: delete_pod_identity_association
Parameters:
  clusterName: "my-eks-cluster"
  associationId: "a-abc123xyz"
  region: "us-east-1"
```

---

### Workflow 10: Get Cluster Insights

**Goal:** Get recommendations and insights for cluster

**Example:**
```
Use tool: list_insights
Parameters:
  clusterName: "my-eks-cluster"
  region: "us-east-1"
```

**Describe Specific Insight:**
```
Use tool: describe_insight
Parameters:
  clusterName: "my-eks-cluster"
  id: "insight-id-123"
  region: "us-east-1"
```

---

### Workflow 11: Delete Cluster

**Goal:** Remove EKS cluster (after removing node groups)

**Steps:**
1. Delete all node groups first
2. Delete Fargate profiles
3. Delete cluster

**Example:**
```
Use tool: delete_cluster
Parameters:
  name: "my-eks-cluster"
  region: "us-east-1"
```

## Troubleshooting

### Cluster Creation Fails

**Problem:** Cluster creation fails or times out
**Cause:** Various IAM, VPC, or quota issues
**Solution:**
1. Verify IAM role has required permissions
2. Check VPC and subnets are valid
3. Ensure security groups allow required traffic
4. Verify service quotas aren't exceeded
5. Check CloudFormation stack events for details

---

### Node Group Won't Create

**Problem:** Node group creation fails
**Cause:** IAM, subnet, or instance type issues
**Solution:**
1. Verify node IAM role has required policies
2. Check subnets have available IPs
3. Verify instance types are available in AZs
4. Ensure AMI type matches instance architecture
5. Check service quotas for EC2 instances

---

### Add-on Installation Fails

**Problem:** Add-on won't install or update
**Cause:** Version incompatibility or conflicts
**Solution:**
1. Check add-on version is compatible with cluster version
2. Use `resolveConflicts: "OVERWRITE"` to replace existing
3. Review add-on documentation for requirements
4. Check IAM permissions for add-on
5. Verify no conflicting self-managed add-ons

---

### Access Denied Errors

**Problem:** "AccessDenied" or permission errors
**Cause:** Insufficient IAM permissions
**Solution:**
1. Verify AWS credentials are configured
2. Check IAM user/role has EKS permissions
3. Review IAM policies for required actions
4. Ensure cluster role trust policy is correct
5. Check access entries are properly configured

---

### Fargate Pods Not Scheduling

**Problem:** Pods not running on Fargate
**Cause:** Selector mismatch or profile issues
**Solution:**
1. Verify Fargate profile selectors match pod labels
2. Check namespace matches profile
3. Ensure pod execution role is correct
4. Verify subnets have available IPs
5. Check Fargate service quotas

## Best Practices

- Use managed node groups over self-managed when possible
- Enable both public and private endpoint access initially
- Use multiple subnets across AZs for high availability
- Tag all resources for cost tracking and organization
- Use latest stable Kubernetes version
- Enable control plane logging for troubleshooting
- Use Pod Identity over IRSA for new workloads
- Implement least privilege access with access entries
- Use Fargate for serverless workloads
- Keep add-ons updated to latest compatible versions
- Use instance types with sufficient resources
- Enable cluster insights for recommendations
- Use security groups to control traffic
- Implement proper IAM roles and policies
- Monitor cluster health and metrics
- Plan node group updates carefully
- Use launch templates for advanced node configuration
- Implement proper backup and disaster recovery

## Configuration

**No additional configuration required** - works with your AWS CLI credentials.

**AWS Credentials:**
- Default: Uses AWS CLI default profile
- Region: Specify per operation or use default

**Required IAM Permissions:**
- eks:* (for cluster operations)
- iam:PassRole (for creating clusters and node groups)
- ec2:* (for VPC and networking)
- Additional permissions for specific operations

## MCP Config Placeholders

**No placeholders needed** - the EKS MCP server uses your existing AWS credentials automatically.

The mcp.json configuration works as-is with the standard package.

**Note:** Ensure your AWS credentials have appropriate EKS permissions before using this power.

---

**Package:** `awslabs.eks-mcp-server@latest`
**MCP Server:** awslabs.eks-mcp-server
