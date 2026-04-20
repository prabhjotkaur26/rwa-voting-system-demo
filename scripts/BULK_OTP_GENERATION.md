# Bulk OTP Generation Script

This script generates OTPs for all voters in an election with TTL (Time-To-Live) set to the election's end time.

## Features

✅ Retrieves election details (start/end time) by election ID  
✅ Fetches all registered voters from the system  
✅ Generates unique 6-digit OTPs for each voter  
✅ Sets TTL to election end time (OTPs expire when election ends)  
✅ Batch writes OTPs to `rwa-voting-otp-prod` DynamoDB table  
✅ Dry-run mode to preview without storing  
✅ Detailed summary with success/failure statistics  

## Prerequisites

- Python 3.7+
- AWS credentials configured (via `~/.aws/credentials` or environment variables)
- IAM permissions for:
  - `dynamodb:GetItem` on `rwa-elections-prod`
  - `dynamodb:Scan` on `rwa-voters-prod`
  - `dynamodb:PutItem` on `rwa-voting-otp-prod`

## Installation

```bash
# Install boto3 if not already installed
pip install boto3
```

## Usage

### Basic Usage

Generate OTPs for an election (e.g., `motiahuys2026`):

```bash
python bulk_generate_otps.py motiahuys2026
```

### Dry Run (Preview Only)

Preview what would be done without actually storing OTPs:

```bash
python bulk_generate_otps.py motiahuys2026 --dry-run
```

### Specify AWS Region

```bash
python bulk_generate_otps.py motiahuys2026 --region us-east-1
```

## Output Example

```
================================================================================
Bulk OTP Generation for Election: motiahuys2026
================================================================================

[*] Fetching election details...
Election Name: RWA Voting 2026
Election ID: motiahuys2026
Start Time: 2026-04-18 17:00:00 UTC (IST)
End Time:   2026-04-18 17:20:00 UTC (IST)
Current Time: 2026-04-18 17:10:30 UTC (IST)

[*] Fetching voters...
Found 156 voters

[*] Generating OTPs for each voter...
Mobile Number   OTP      Status    
-----------------------------------
9876543210      234567   SUCCESS   
9876543211      567890   SUCCESS   
9876543212      123456   SUCCESS   
...

[*] Storing OTPs in DynamoDB...
✅ Stored 156 OTPs in rwa-voting-otp-prod

================================================================================
OTP Generation Summary
================================================================================
Total Voters:        156
OTPs Generated:      156
Generation Failed:   0
TTL Set To:          2026-04-18 17:20:00 UTC (IST)
Dry Run:             No
================================================================================
```

## How It Works

1. **Election Retrieval**: Fetches election details including start/end times
2. **Voter Scanning**: Retrieves all voters from the voters table
3. **OTP Generation**: Creates 6-digit random OTP for each voter
4. **TTL Configuration**: Sets TTL to the election's end time (not relative minutes)
   - When the TTL expires, DynamoDB automatically deletes the OTP record
   - This ensures OTPs are invalidated exactly when the election ends
5. **Batch Writing**: Stores all OTPs in `rwa-voting-otp-prod` table

## OTP Record Structure

```json
{
  "mobileNumber": "9876543210",
  "otp": "234567",
  "createdAt": 1713464430,
  "ttl": 1713464430,
  "attempts": 0
}
```

- **mobileNumber**: 10-digit mobile number (partition key)
- **otp**: 6-digit OTP code
- **createdAt**: Unix timestamp when OTP was generated (IST)
- **ttl**: Unix timestamp when OTP expires (election end time)
- **attempts**: Failed OTP verification attempts (starts at 0)

## Error Handling

- ✅ Validates election exists before processing
- ✅ Skips voters with missing mobile numbers
- ✅ Shows detailed failure information
- ✅ Batch writes ensure partial success handling
- ✅ Graceful exit with appropriate error codes

## Safety Features

⚠️ **Election Status Warnings**:
- Shows warning if election has already ended
- Shows warning if election hasn't started yet

🔄 **Dry-Run Mode**:
- Preview all operations without modifying data
- Useful for testing and validation

📊 **Detailed Logging**:
- Shows each voter's mobile number and OTP status
- Displays summary statistics
- Lists failed voters with reasons

## Important Notes

1. **TTL Format**: The script uses **absolute Unix timestamp** (election end time), not relative minutes. OTPs will automatically expire at the election end time.

2. **Idempotent**: Running the script multiple times will regenerate OTPs (overwrites existing records) due to `overwrite_by_pkeys` in batch writer.

3. **Performance**: Efficiently handles large voter lists with batch writing (25 items per batch).

4. **IST Timezone**: All timestamps use IST (UTC+5:30) as per system configuration.

## Troubleshooting

### AWS Credentials Error
```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```
**Solution**: Configure AWS credentials in `~/.aws/credentials` or set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` environment variables.

### Election Not Found
```
ValueError: Election 'invalid-id' not found
```
**Solution**: Verify the election ID exists by checking the DynamoDB `rwa-elections-prod` table.

### Permission Denied Errors
```
botocore.exceptions.ClientError: An error occurred (AccessDenied)
```
**Solution**: Ensure your IAM user/role has required permissions for the three DynamoDB tables.

## Examples

### Generate OTPs for upcoming election
```bash
python bulk_generate_otps.py annual-election-2026
```

### Test with dry run before actual generation
```bash
python bulk_generate_otps.py annual-election-2026 --dry-run
# Review output, then run without --dry-run
python bulk_generate_otps.py annual-election-2026
```

### Generate for different region
```bash
python bulk_generate_otps.py election-id --region ap-southeast-1
```

## Support

For issues or questions:
1. Check the error messages carefully
2. Verify election ID and voter data exist
3. Ensure AWS credentials and permissions are correct
4. Review CloudWatch Logs for detailed errors
