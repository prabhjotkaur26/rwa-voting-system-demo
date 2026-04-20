# Cost Estimation - RWA Voting System

Detailed AWS cost breakdown and optimization strategies.

## 💰 Monthly Cost Summary

For a typical election with **500 voters** casting **7 votes each** over **24 hours**:

| Service | Free Tier | Estimated Cost |
|---------|-----------|-----------------|
| Lambda | 1M invocations/month | ~$0.40 |
| DynamoDB | 25 GB storage + capacity | ~$1.50 |
| API Gateway | 1M requests/month | ~$0.00 |
| SNS (SMS) | - | ~$2.50 |
| S3 | 5 GB storage | ~$0.10 |
| CloudWatch Logs | 5 GB/month free | ~$0.00 |
| **TOTAL** | | **~$4.50/month** |

## 📊 Detailed Cost Breakdown

### 1. AWS Lambda

**Pricing Model:**
- Free Tier: 1,000,000 invocations/month + 400,000 GB-seconds/month
- Beyond: $0.0000002 per invocation, $0.0000166667 per GB-second

**Usage Estimate (500 voters):**
- OTP Send: 500 invocations
- OTP Verify: 500 invocations
- Cast Vote: 3,500 invocations (500 voters × 7 posts)
- Get Results: 100 invocations (assume 100 result checks)
- Election Management: 10 invocations
- **Total: 4,610 invocations** ✅ Free Tier

**Compute Time:**
- Average execution: 200-500ms per function
- Total compute: ~2,000 GB-seconds
- **Cost: $0.00** ✅ Within free tier

Larger election (1000 voters):
- Total invocations: 9,210
- Total compute: ~4,000 GB-seconds
- **Cost: $0.00-0.10** ✅ Still nearly free

### 2. Amazon DynamoDB

**Pricing Model (On-Demand):**
- Read: $1.25 per million
- Write: $6.25 per million
- Storage: $0.25 per GB

**Usage Estimate (500 voters, 7 posts):**

**Reads:**
- OTP lookup: 500 reads
- Candidate lookup: 3,500 reads
- Vote duplicate check: 3,500 reads
- Results query: 500+ reads
- **Total reads: ~8,000 = $0.01**

**Writes:**
- OTP store: 500 writes
- Vote store: 3,500 writes
- Election create: 1 write
- Candidates add: 35 writes
- **Total writes: ~4,036 = $0.02**

**Storage:**
- Elections: < 1 MB
- Candidates (35 total): ~0.5 MB
- Votes (3,500): ~1 MB
- OTP (temporary): ~0.2 MB
- **Total storage: ~2 MB = $0.00**

**Monthly Cost: ~$0.03** ✅ Almost free

Larger deployment scenarios:
- 1,000 voters: ~$0.10
- 10,000 voters: ~$1.00
- 100,000 voters: ~$10.00 (DynamoDB scales linearly on-demand)

### 3. Amazon API Gateway (HTTP API)

**Pricing Model:**
- Free Tier: 1,000,000 requests/month
- Beyond: $0.90 per million requests

**Usage Estimate (500 voters):**
- OTP send: 500 requests
- OTP verify: 500 requests
- Cast votes: 3,500 requests
- Results checks: 100 requests
- Admin operations: 20 requests
- **Total: 4,620 requests** ✅ **Free Tier**

**Monthly Cost: $0.00** ✅ No charge

Note: We use HTTP API (cheaper) instead of REST API (3× more expensive)

### 4. Amazon SNS (SMS)

**Pricing Model:**
- USA: $0.00645 per SMS
- India (most common): $0.0112 per SMS
- Other: Variable

**Usage Estimate (500 voters):**
- OTP messages: 500 × $0.0112 = **$5.60**
- (Assuming some retries, multiple attempts)

**Monthly Cost: ~$2.50-5.00** (excluding SMS failures/retries)

**Optimization:**
- Use email instead (free)
- Batch OTP requests
- Implement rate limiting per mobile
- Consolidate OTP messages

### 5. Amazon S3

**Pricing Model:**
- Free Tier: 5 GB storage
- Beyond: $0.023 per GB/month

**Usage Estimate:**
- Frontend HTML/CSS/JS: ~500 KB
- Static assets: ~1 MB
- **Total: ~2 MB** ✅ **Free Tier**

**Monthly Cost: $0.00**

**Bandwidth:**
- Free Tier: 100 GB egress per month
- Typical usage: ~100 MB (500 voters × 200KB each)
- **Cost: $0.00**

### 6. CloudWatch Logs

**Pricing Model:**
- Free Tier: 5 GB/month
- Beyond: $0.50 per GB

**Usage Estimate (500 voters):**
- Log volume: ~50 MB (10 logs × 4,610 invocations)
- **Cost: $0.00** ✅ **Free Tier**

Larger deployments:
- 1,000 voters: ~100 MB (still free)
- 100,000 voters: ~10 GB (beyond free tier, ~$2.25/month)

## 📈 Scaling Cost Analysis

| Voters | Duration | Lambda | DynamoDB | SNS | API Gateway | **Total** |
|--------|----------|--------|----------|-----|-------------|-----------|
| 100 | 1 week | $0.00 | $0.00 | $0.50 | $0.00 | **$0.50** |
| 500 | 24 hours | $0.00 | $0.03 | $2.50 | $0.00 | **$2.53** |
| 1,000 | 24 hours | $0.00 | $0.10 | $5.00 | $0.00 | **$5.10** |
| 5,000 | 24 hours | $0.10 | $0.50 | $25.00 | $0.00 | **$25.60** |
| 10,000 | 24 hours | $0.20 | $1.00 | $50.00 | $0.00 | **$51.20** |

## 💡 Cost Optimization Strategies

### 1. Minimize SNS Costs (Biggest Expense)

**Single OTP per voter:**
- Don't resend OTPs unless explicitly requested
- Increase OTP validity to 10 minutes
- **Savings: 20-30%**

**Use Email instead of SMS:**
```python
# Recommended for internal RWAs
import boto3
ses = boto3.client('ses')
ses.send_email(
    Source='voting@rwa.com',
    Destination={'ToAddresses': [email]},
    Message={
        'Subject': {'Data': 'Your OTP'},
        'Body': {'Text': f'OTP: {otp}'}
    }
)
# Free for first 200 emails/day
```
- **Savings: 99%** (email is free for most use cases)

**Implement rate limiting:**
```python
# Max 1 OTP send per mobile number per 1 minute
# Max 3 OTP send attempts per 24 hours
```
- **Savings: 40-50%**

### 2. Optimize DynamoDB

**Current: On-Demand Pricing**
- Good for unpredictable workloads
- Scales automatically

**Alternative: Provisioned Capacity**
```hcl
# For predictable 500 voter elections
billing_mode = "PROVISIONED"
read_capacity_units = 5
write_capacity_units = 5
# Cost: ~$2.50/month vs $0.03 for this workload
# But cheaper at scale (>100K requests)
```

**Archive old data:**
- Move elections > 6 months old to S3
- Reduces storage costs
- Improves query performance

**Disable Point-in-Time Recovery:**
```hcl
point_in_time_recovery {
  enabled = false  # Saves ~20% of DynamoDB cost
}
```

### 3. API Gateway Optimization

Already using HTTP API (cheapest option at $0.90/M vs $3.50/M for REST API)

**Additional savings:**
- Enable caching for results endpoint
- Compress responses
- **Potential savings: 10-20%**

### 4. Lambda Optimization

**Current: 256 MB, 30 second timeout**

**For cost reduction:**
```hcl
lambda_memory = 128  # Reduces cost by ~50%
lambda_timeout = 10  # Typical execution ~2-3s
```
- **Savings: 40-50%**
- Trade-off: Slightly longer execution

**Use Lambda Layers:**
- Reuse dependencies across functions
- Reduces package size
- Slight performance improvement

### 5. S3 Frontend Optimization

**Use CloudFront (CDN):**
```hcl
module "cloudfront" {
  # Add CDN in front of S3
  # Caches static assets globally
  # Reduces egress costs
}
```
- **Savings: 20-30% on bandwidth**
- Free tier includes adequate CDN

## 🎯 Cost Reduction Plan

### Phase 1: Setup (This Deployment)
- **Cost**: ~$3-5/month (500 voters)
- Status: Optimal for free tier

### Phase 2: Scale to 1,000 Voters
- Implement email OTP (instead of SMS)
- Enable scheduling (election during specific hour)
- **Expected Cost**: ~$1-2/month

### Phase 3: Enterprise (10,000+ Voters)
- Migrate to provisioned DynamoDB
- Add CloudFront CDN
- Implement caching strategy
- **Expected Cost**: ~$20-30/month

## 💳 AWS Free Tier Benefits

**Always Active (12 months free for new accounts):**
- Lambda: 1M invocations/month ✅
- DynamoDB: 25 GB storage + 25 RCU + 25 WCU ✅
- API Gateway: 1M requests/month ✅
- CloudWatch: 5 GB logs/month ✅
- Data Transfer: 100 GB/month ✅

**Always Free (No time limit):**
- S3: 5 GB storage ✅
- CloudWatch: Basic monitoring ✅
- SNS: 100 SMS/month ✅ (regional, India not included)

**This System:**
- Stays within free tier for 500 voters ✅
- Only paid component: SNS SMS ($0.0112/message India)

## 📊 Monthly Cost Projection

**Scenario 1: Small RWA (200 voters)**
```
Lambda:       $0.00
DynamoDB:     $0.00
API Gateway:  $0.00
SNS (SMS):    $1.00 (assuming re-sends)
S3:           $0.00
CloudWatch:   $0.00
─────────────────────
Monthly Cost: ~$1.00
Annual Cost:  ~$12.00
```

**Scenario 2: Medium RWA (500 voters)**
```
Lambda:       $0.00
DynamoDB:     $0.05
API Gateway:  $0.00
SNS (SMS):    $2.50
S3:           $0.00
CloudWatch:   $0.00
─────────────────────
Monthly Cost: ~$2.55
Annual Cost:  ~$30.60
```

**Scenario 3: Large RWA (1,000 voters)**
```
Lambda:       $0.05
DynamoDB:     $0.10
API Gateway:  $0.00
SNS (SMS):    $5.00
S3:           $0.00
CloudWatch:   $0.00
─────────────────────
Monthly Cost: ~$5.15
Annual Cost:  ~$61.80
```

**Scenario 4: Multiple Elections (Weekly for 500 voters)**
```
Lambda:       $0.00
DynamoDB:     $0.20
API Gateway:  $0.00
SNS (SMS):    $10.00
S3:           $0.00
CloudWatch:   $0.00
─────────────────────
Monthly Cost: ~$10.20
Annual Cost:  ~$122.40
```

## 🚨 Cost Optimization Checklist

- [ ] Using HTTP API (not REST API)
- [ ] DynamoDB on-demand pricing
- [ ] OTP expires automatically (TTL enabled)
- [ ] Logging only essential events
- [ ] No unnecessary data replication
- [ ] S3 versioning disabled (optional)
- [ ] VPC endpoints not used (cost savings)
- [ ] Lambda layer for shared code (if >1 function)
- [ ] Result queries computed on-demand (no streams)
- [ ] Email OTP considered instead of SMS
- [ ] Rate limiting implemented
- [ ] CloudWatch logs retention set to 7 days

## 💰 Estimated Annual Costs

### If using recommended optimizations:
- **500 voter elections**: $30-50/year ✅
- **1000 voter elections**: $60-100/year ✅
- **Multiple elections/month**: $100-200/year ✅

### Worst case (no optimization):
- **500 voter elections**: $30-50/year (SMS still dominates)
- **10,000 voter elections**: $600/year

## 📞 Ways to Reduce Costs Further

1. **Use Email instead of SMS** - Save 99%
2. **Batch Operations** - Reduce API calls
3. **Cache Results** - Save read operations
4. **Archive Elections** - Reduce storage
5. **Use Reserved Capacity** - If > 100K request/month
6. **Consolidate Elections** - Schedule during windows

## ⚠️ Cost Alerts

Set up AWS billing alerts to avoid surprises:

```bash
# AWS Budgets
aws budgets create-budget \
  --account-id 123456789 \
  --budget '{
    "BudgetName": "RWA Voting Monthly",
    "BudgetLimit": {"Amount": "50", "Unit": "USD"},
    "TimeUnit": "MONTHLY"
  }'
```

---

**Last Updated**: 2024
**Calculation Date**: 2024
**Pricing Region**: US (ap-south-1)

*Note: Prices may vary by region. SNS SMS costs are significantly higher for India (highest option). For large-scale deployments, contact AWS sales for volume discounts.*
