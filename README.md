# RWA Voting System - AWS Serverless Architecture

Complete, production-ready serverless voting system for conducting RWA (Resident Welfare Association) elections using AWS.

## 🎯 Core Features

- **Mobile OTP Authentication**: SMS-based voter verification using AWS SNS
- **Multi-Election Support**: Manage multiple simultaneous elections
- **7-Post Elections**: Support for standard RWA roles
- **Secure Voting**: Prevent duplicate voting with DynamoDB conditional writes
- **Live Results Dashboard**: Polling-based real-time vote counting
- **Admin Management**: Create elections, manage candidates
- **Cost Optimized**: Designed to stay within AWS Free Tier limits
- **Serverless Architecture**: No infrastructure management required

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                            │
│                   (S3 Static Website / SPA)                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (HTTP API)                       │
│                    (Cost-optimized, no WebSockets)                │
└────────┬───────┬──────────┬─────────┬──────────┬────────┬────────┘
         │       │          │         │          │        │
         ▼       ▼          ▼         ▼          ▼        ▼
    ┌────┐ ┌────┐  ┌───────┐  ┌───────┐  ┌──────┐  ┌──────┐
    │Send│ │Veri│  │Cast   │  │Get    │  │Create│  │Add   │
    │OTP │ │OTP │  │Vote   │  │Result │  │Elec  │  │Candi │
    │    │ │    │  │       │  │s      │  │tion  │  │dates │
    └────┘ └────┘  └───────┘  └───────┘  └──────┘  └──────┘
     │      │         │         │        │           │
     └──────┴─────────┴─────────┴────────┴───────────┘
                      │
        ┌─────────────┼──────────────┐
        ▼             ▼              ▼
    ┌────────┐  ┌──────────┐  ┌──────────┐
    │  SNS   │  │DynamoDB  │  │CloudWatch│
    │(SMS)   │  │(4 Tables)│  │(Logs)    │
    └────────┘  └──────────┘  └──────────┘

AWS Services:
  - Lambda (Python 3.11)
  - API Gateway (HTTP API)
  - DynamoDB (On-demand pricing)
  - SNS (SMS delivery)
  - S3 (Frontend hosting)
  - CloudWatch (Monitoring)
```

## 📋 API Endpoints

### Authentication
- `POST /auth/send-otp` - Send OTP to mobile number
- `POST /auth/verify-otp` - Verify OTP and get auth token

### Voting
- `POST /vote/cast-vote` - Cast a vote for a candidate

### Results
- `GET /results/{electionId}` - Get live election results

### Admin
- `POST /admin/elections` - Create new election
- `POST /admin/candidates` - Add candidates to a post

## 📦 Project Structure

```
rwa-voting-system/
├── terraform/
│   ├── main.tf                    # Main configuration
│   ├── providers.tf               # AWS provider settings
│   ├── variables.tf               # Input variables
│   ├── outputs.tf                 # Output values
│   ├── terraform.tfvars           # Variable values (create locally)
│   └── modules/
│       ├── iam/                   # IAM roles and policies
│       ├── lambda/                # Lambda function definitions
│       ├── dynamodb/              # DynamoDB table schemas
│       ├── api_gateway/           # API Gateway configuration
│       ├── sns/                   # SNS topic setup
│       └── s3/                    # S3 frontend hosting
├── lambda/
│   ├── lib/
│   │   ├── utils.py              # Utility functions
│   │   └── aws_clients.py        # AWS service wrappers
│   ├── functions/
│   │   ├── send_otp/             # Send OTP Lambda
│   │   ├── verify_otp/           # Verify OTP Lambda
│   │   ├── cast_vote/            # Cast vote Lambda
│   │   ├── get_results/          # Get results Lambda
│   │   ├── create_election/      # Create election Lambda
│   │   └── add_candidates/       # Add candidates Lambda
│   └── .build/                   # Build artifacts (auto-generated)
├── frontend/
│   ├── index.html                # Main HTML file
│   ├── style.css                 # Styling
│   ├── app.js                    # Main application logic
│   └── admin.html                # Admin panel
├── docs/
│   ├── API_DESIGN.md             # comprehensive API documentation
│   ├── DEPLOYMENT_GUIDE.md       # Step-by-step deployment
│   ├── ARCHITECTURE.md           # Architecture details
│   ├── COST_ESTIMATION.md        # Cost analysis
│   └── TESTING.md                # Testing instructions
├── tests/
│   └── test_scenarios.sh         # Integration test scripts
├── .gitignore
├── README.md                      # This file
├── LICENSE
└── CONTRIBUTING.md
```

## 📚 Documentation

See the following files for detailed information:

1. **[DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - Step-by-step deployment instructions
2. **[API_DESIGN.md](docs/API_DESIGN.md)** - Complete API specification
3. **[TESTING.md](docs/TESTING.md)** - Testing procedures and examples
4. **[COST_ESTIMATION.md](docs/COST_ESTIMATION.md)** - AWS cost breakdown
5. **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Architecture and data design details

## 🚀 Quick Start

### Prerequisites
- AWS Account (uses Free Tier)
- Terraform (v1.0+)
- AWS CLI (v2.0+)
- Python 3.11 (for local development)
- Node.js (optional, for frontend development)

### Deployment

1. **Clone and configure**
```bash
cd c:\PythonWork\rwa-voting-system
aws configure  # Configure AWS credentials
```

2. **Update variables**
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your region and settings
```

3. **Deploy infrastructure**
```bash
terraform init
terraform plan
terraform apply
```

4. **Note the outputs**
```bash
terraform output  # Save the API endpoint and other outputs
```

5. **Deploy (or upload) frontend**
```bash
aws s3 cp frontend/ s3://your-bucket-name/ --recursive
```

## 🔐 Security Features

- **OTP-based Authentication**: Mobile number verified via SMS
- **Single-use OTP**: OTP deleted after successful verification
- **Conditional Writes**: Prevent duplicate voting using DynamoDB
- **Input Validation**: All inputs sanitized and validated
- **IAM Least Privilege**: Lambda functions have minimal required permissions
- **Data Anonymity**: No direct mapping between voter identity and vote
- **TTL on Sensitive Data**: OTP automatically expires
- **CORS Protected**: API Gateway CORS configuration

## 💰 Cost Estimation

**Monthly Cost (for small to medium elections):**
- DynamoDB: ~$1-5 (Free Tier: 25 GB storage, 25 read/write capacity units)
- Lambda: ~$0.20 (Free Tier: 1M invocations, 400,000 GB-secondsmonth)
- SNS SMS: $0.50-2.00 per 100 OTPs sent
- API Gateway: ~$0 (Free Tier: 1M requests/month)
- S3: ~$0.50 (Free Tier: 5 GB storage)

**Total: Typically $1-10/month for elections with 100-1000 voters**

See [COST_ESTIMATION.md](docs/COST_ESTIMATION.md) for detailed breakdown.

## 🧪 Testing

### Quick Test (5 minutes)

```bash
# Set API endpoint
export API_ENDPOINT="https://your-api-id.execute-api.ap-south-1.amazonaws.com/prod"

# 1. Create election
curl -X POST $API_ENDPOINT/admin/elections \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "test-election-2024",
    "electionName": "Test Election",
    "description": "Test election for verification",
    "startTime": 1707859200,
    "endTime": 1707945600
  }'

# 2. Add candidates
curl -X POST $API_ENDPOINT/admin/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "electionId": "test-election-2024",
    "postId": "1",
    "candidates": [
      {"candidateId": "candidate-1", "candidateName": "John Doe"},
      {"candidateId": "candidate-2", "candidateName": "Jane Smith"}
    ]
  }'

# 3. Send OTP
curl -X POST $API_ENDPOINT/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "9876543210"}'

# 4. Verify OTP (check logs for OTP in test mode)
curl -X POST $API_ENDPOINT/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"mobileNumber": "9876543210", "otp": "123456"}'

# 5. Cast vote
curl -X POST $API_ENDPOINT/vote/cast-vote \
  -H "Content-Type: application/json" \
  -d '{
    "mobileNumber": "9876543210",
    "electionId": "test-election-2024",
    "postId": "1",
    "candidateId": "candidate-1"
  }'

# 6. Get results
curl -X GET $API_ENDPOINT/results/test-election-2024
```

See [TESTING.md](docs/TESTING.md) for comprehensive testing guide.

## 📊 Database Schema

### Votes Table
```
PK: electionId#postId (String)
SK: mobileNumber (String)

Attributes:
- candidateId: String
- timestamp: Number (Unix timestamp)

GSI:
- electionId: For querying all votes in an election
```

### OTP Table
```
PK: mobileNumber (String)

Attributes:
- otp: String (6 digits)
- createdAt: Number
- ttl: Number (Unix timestamp, expires automatically)
- attempts: Number (failed attempt counter)
```

### Candidates Table
```
PK: electionId#postId (String)
SK: candidateId (String)

Attributes:
- candidateName: String
- electionId: String
- postId: String
- createdAt: Number
```

### Elections Table
```
PK: electionId (String)

Attributes:
- electionName: String
- description: String
- startTime: Number (Unix timestamp)
- endTime: Number (Unix timestamp)
- createdAt: Number
- status: String (scheduled, ongoing, completed)
- resultsVisible: Boolean
```

## 🛠️ Advanced Configuration

### Environment Variables

Create `terraform.tfvars` file:

```hcl
aws_region               = "ap-south-1"
environment              = "prod"
project_name             = "rwa-voting"
sns_topic_name           = "voting-otp-topic"
lambda_timeout           = 30
lambda_memory            = 256
otp_expiry_minutes       = 5
dynamodb_read_capacity   = "PAY_PER_REQUEST"
dynamodb_write_capacity  = "PAY_PER_REQUEST"
api_throttling_burst_limit = 5000
api_throttling_rate_limit  = 2000
enable_cors              = true
allowed_origins          = ["*"]
```

### Custom OTP Length

Edit `lambda/lib/utils.py`:
```python
def generate_otp(length: int = 6) -> str:
    # Change default length from 6 to desired value
    return ''.join(random.choices(string.digits, k=length))
```

## 🐛 Troubleshooting

### OTP Not Received
1. Check AWS SNS is configured in correct region
2. Verify mobile number format is correct
3. Check SNS SMS sandbox (if in sandbox mode)
4. Review Lambda logs in CloudWatch

### Duplicate Vote Errors
1. Clear browser cache (might be sending duplicate requests)
2. Check if voter already voted for that post
3. Review DynamoDB items for conflicts

### API Returns 500 Errors
1. Check CloudWatch Logs for Lambda function errors
2. Verify environment variables are set correctly
3. Check DynamoDB table names in environment

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more solutions.

## 📈 Performance Optimization

- **DynamoDB**: On-demand pricing for cost efficiency
- **Lambda Runtime**: Python 3.11 (latest and fastest)
- **Caching**: Frontend implements 5-10 second polling interval
- **No Streams**: Results computed on-demand to save costs
- **Minimal Logging**: Only essential logs stored

## 🔄 CI/CD Pipeline

Optional GitHub Actions workflow included in `.github/workflows/`.

```bash
# Enable GitHub Actions
# 1. Configure AWS credentials in GitHub Secrets
# 2. Push to main branch
# 3. Automatic terraform plan and apply
```

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.

## 📞 Support

For issues, questions, or feature requests:
1. Check existing GitHub issues
2. Review documentation in `/docs` folder
3. Create new GitHub issue with detailed description

## ⚠️ Disclaimer

This system is designed for small to medium-scale RWA elections (100-1000 voters). For larger deployments, consider:
- Vertical scaling of Lambda functions
- DynamoDB provisioned capacity or DAX cache
- CloudFront CDN for frontend
- Additional security measures

## 🚀 Future Enhancements

- [ ] Result export to CSV/PDF
- [ ] Email notifications
- [ ] Voter list bulk upload
- [ ] Admin authentication
- [ ] Multi-language support
- [ ] Rate limiting per IP
- [ ] Biometric voter verification
- [ ] End-to-end encryption for votes

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Maintained by**: RWA Tech Team
