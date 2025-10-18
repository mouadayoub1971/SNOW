# Valyrion RAG - Deployment Guide

Complete guide for deploying Valyrion RAG architecture on AWS using Terraform.

## Prerequisites

### Required Tools
- [ ] AWS CLI v2 installed and configured
- [ ] Terraform >= 1.5.0 installed
- [ ] Docker installed
- [ ] Python 3.10+ installed
- [ ] Git installed

### AWS Account Setup
- [ ] AWS account with admin access
- [ ] IAM user with programmatic access
- [ ] AWS CLI configured with credentials
- [ ] Billing alerts configured

### API Keys
- [ ] OpenAI API key (from platform.openai.com)
- [ ] Finnhub API key (from finnhub.io - free tier)

## Step 1: Initial Setup

### 1.1 Configure AWS Credentials

```bash
# Configure AWS CLI
aws configure

# Test connection
aws sts get-caller-identity
```

### 1.2 Create Terraform Backend

```bash
# Create S3 bucket for Terraform state
aws s3 mb s3://valyrion-terraform-state --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket valyrion-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name valyrion-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### 1.3 Store Secrets in AWS Secrets Manager

```bash
# Store OpenAI API key
aws secretsmanager create-secret \
  --name valyrion/openai-api-key \
  --secret-string "sk-your-openai-api-key" \
  --region us-east-1

# Store Finnhub API key
aws secretsmanager create-secret \
  --name valyrion/finnhub-api-key \
  --secret-string "your-finnhub-api-key" \
  --region us-east-1

# Store database passwords
aws secretsmanager create-secret \
  --name valyrion/postgres-password \
  --secret-string "$(openssl rand -base64 32)" \
  --region us-east-1

aws secretsmanager create-secret \
  --name valyrion/opensearch-password \
  --secret-string "$(openssl rand -base64 32)" \
  --region us-east-1
```

## Step 2: Configure Terraform

### 2.1 Create terraform.tfvars

```bash
cd terraform/environments/dev
```

Create `terraform.tfvars`:

```hcl
# Environment
environment = "dev"
aws_region  = "us-east-1"

# Networking
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

# API Configuration
api_instance_count = 2

# Worker Configuration
worker_instance_count = 2

# Database Configuration
enable_multi_az              = false  # Set to true for production
postgres_instance_class      = "db.t4g.large"
postgres_allocated_storage   = 100
redis_node_type              = "cache.r6g.large"
opensearch_instance_type     = "r6g.large.search"
opensearch_instance_count    = 2

# API Keys (from Secrets Manager)
openai_api_key  = "stored-in-secrets-manager"
finnhub_api_key = "stored-in-secrets-manager"
```

### 2.2 Initialize Terraform

```bash
terraform init
```

Expected output:
```
Initializing the backend...
Initializing modules...
Initializing provider plugins...
Terraform has been successfully initialized!
```

### 2.3 Validate Configuration

```bash
terraform validate
```

## Step 3: Plan Infrastructure

### 3.1 Review Plan

```bash
terraform plan -out=tfplan
```

This will show:
- Resources to be created
- Estimated costs
- Dependencies

Review carefully:
- VPC and networking (subnets, NAT gateway, security groups)
- Databases (RDS, ElastiCache, OpenSearch)
- Compute (ECS cluster, task definitions)
- Storage (S3 bucket)
- Load balancer

### 3.2 Estimate Costs

Use AWS Pricing Calculator or:

```bash
# Install Infracost (optional)
brew install infracost  # macOS
# or: curl -fsSL https://raw.githubusercontent.com/infracost/infracost/master/scripts/install.sh | sh

# Generate cost estimate
infracost breakdown --path . --terraform-plan-flags "-out=tfplan"
```

Expected dev environment cost: ~$400-600/month

## Step 4: Deploy Infrastructure

**⚠️ WARNING: This will create real AWS resources and incur costs!**

### 4.1 Apply Terraform

```bash
terraform apply tfplan
```

This will:
1. Create VPC and networking (5-10 mins)
2. Create databases (15-20 mins)
3. Create ECS cluster and services (5 mins)
4. Create S3 bucket
5. Configure security groups

Total time: ~30-40 minutes

### 4.2 Verify Deployment

```bash
# Get outputs
terraform output

# Expected outputs:
# vpc_id
# alb_dns_name
# postgres_endpoint
# redis_endpoint
# opensearch_endpoint
# s3_bucket_name
```

### 4.3 Test Connectivity

```bash
# Test ALB (should return 404 until app is deployed)
curl http://$(terraform output -raw alb_dns_name)

# Test databases (from bastion or within VPC)
# PostgreSQL
psql -h $(terraform output -raw postgres_endpoint) -U valyrion_admin -d valyrion

# Redis
redis-cli -h $(terraform output -raw redis_endpoint)
```

## Step 5: Build and Deploy Application

### 5.1 Build Docker Images

```bash
cd ../../../  # Return to project root

# Build API image
docker build -t valyrion-api -f docker/Dockerfile.api .

# Build worker image
docker build -t valyrion-worker -f docker/Dockerfile.worker .
```

### 5.2 Push to ECR

```bash
# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=us-east-1

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Create ECR repositories
aws ecr create-repository --repository-name valyrion-api --region $AWS_REGION
aws ecr create-repository --repository-name valyrion-worker --region $AWS_REGION

# Tag and push API image
docker tag valyrion-api:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/valyrion-api:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/valyrion-api:latest

# Tag and push worker image
docker tag valyrion-worker:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/valyrion-worker:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/valyrion-worker:latest
```

### 5.3 Update ECS Task Definitions

Edit `terraform/modules/ecs-service/main.tf` to use ECR images, then:

```bash
cd terraform/environments/dev
terraform plan
terraform apply
```

### 5.4 Verify Deployment

```bash
# Get ALB DNS
ALB_DNS=$(terraform output -raw alb_dns_name)

# Test health endpoint
curl http://$ALB_DNS/health

# Expected response:
# {"status":"healthy","timestamp":1234567890.123}
```

## Step 6: Initialize Databases

### 6.1 Install pgvector Extension

```bash
# Connect to PostgreSQL
POSTGRES_HOST=$(terraform output -raw postgres_endpoint)
psql -h $POSTGRES_HOST -U valyrion_admin -d valyrion

# Install extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

# Verify
\dx
```

### 6.2 Create Database Schema

```bash
# Run migrations (if using Alembic)
alembic upgrade head

# Or manually create tables
psql -h $POSTGRES_HOST -U valyrion_admin -d valyrion < schema.sql
```

### 6.3 Initialize Qdrant Collection

The collection is created automatically on first connection, or manually:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(host="your-qdrant-host", port=6333)

client.create_collection(
    collection_name="valyrion_documents",
    vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
)
```

### 6.4 Initialize Neo4j Schema

```bash
# Connect to Neo4j
NEO4J_URI=$(terraform output -raw neo4j_uri)  # If deployed
cypher-shell -a $NEO4J_URI -u neo4j -p your_password

# Create constraints and indexes
CREATE CONSTRAINT company_ticker IF NOT EXISTS FOR (c:Company) REQUIRE c.ticker IS UNIQUE;
CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;
CREATE INDEX document_date IF NOT EXISTS FOR (d:Document) ON (d.filing_date);
```

## Step 7: Ingest Initial Data

### 7.1 Run Ingestion Script

```bash
# Set environment variables
export POSTGRES_HOST=$(cd terraform/environments/dev && terraform output -raw postgres_endpoint)
export REDIS_HOST=$(cd terraform/environments/dev && terraform output -raw redis_endpoint)
export QDRANT_HOST=your-qdrant-host  # From EC2 or cloud
# ... other variables

# Run ingestion
python scripts/ingest_sec_filings.py
```

### 7.2 Monitor Ingestion

```bash
# Check CloudWatch Logs
aws logs tail /ecs/valyrion-worker --follow

# Check database
psql -h $POSTGRES_HOST -U valyrion_admin -d valyrion -c "SELECT COUNT(*) FROM documents;"

# Check Qdrant
curl http://your-qdrant-host:6333/collections/valyrion_documents
```

## Step 8: Configure Monitoring

### 8.1 Create CloudWatch Dashboard

```bash
# Dashboard is created by Terraform, or manually:
aws cloudwatch put-dashboard \
  --dashboard-name valyrion-dev \
  --dashboard-body file://cloudwatch-dashboard.json
```

### 8.2 Set Up Alarms

```bash
# Example: High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name valyrion-high-error-rate \
  --alarm-description "Alert when error rate exceeds 5%" \
  --metric-name ErrorRate \
  --namespace Valyrion \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 5.0 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:valyrion-alerts
```

## Step 9: Test End-to-End

### 9.1 Submit Test Query

```bash
ALB_DNS=$(cd terraform/environments/dev && terraform output -raw alb_dns_name)

curl -X POST http://$ALB_DNS/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What was Apple'\''s revenue in Q4 2023?",
    "filters": {"company": "AAPL"}
  }'
```

### 9.2 Verify Response

Expected response structure:
```json
{
  "answer": "...",
  "sources": [...],
  "confidence": 0.85,
  "latency_ms": 1234
}
```

## Step 10: Production Deployment

### 10.1 Create Production Environment

```bash
# Copy dev environment
cp -r terraform/environments/dev terraform/environments/prod

# Update terraform.tfvars for production:
# - enable_multi_az = true
# - Larger instance types
# - More instances
```

### 10.2 Deploy to Production

```bash
cd terraform/environments/prod
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### 10.3 Blue/Green Deployment

For zero-downtime deployments:
1. Create new task definition version
2. Update ECS service
3. ECS gradually shifts traffic
4. Monitor for errors
5. Rollback if needed

## Troubleshooting

### Issue: Terraform Apply Fails

**Solution**: Check AWS quotas
```bash
aws service-quotas list-service-quotas --service-code ec2
```

### Issue: Cannot Connect to Databases

**Solution**: Check security groups
```bash
aws ec2 describe-security-groups --group-ids sg-xxxxx
```

### Issue: High Costs

**Solution**: Use Spot instances for workers
```hcl
# In ECS task definition
capacity_provider_strategy {
  capacity_provider = "FARGATE_SPOT"
  weight           = 1
}
```

## Cleanup

**⚠️ WARNING: This will delete all resources and data!**

```bash
cd terraform/environments/dev

# Destroy infrastructure
terraform destroy

# Delete Terraform state bucket
aws s3 rb s3://valyrion-terraform-state --force

# Delete DynamoDB table
aws dynamodb delete-table --table-name valyrion-terraform-locks
```

## Next Steps

- [ ] Set up CI/CD pipeline (GitHub Actions, AWS CodePipeline)
- [ ] Configure custom domain (Route 53, ACM certificate)
- [ ] Enable AWS WAF for security
- [ ] Set up disaster recovery (cross-region replication)
- [ ] Implement cost optimization (Reserved Instances, Savings Plans)

## References

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Architecture Documentation](./architecture.md)
- [Implementation Tasks](../TASKS.md)
