# ═══════════════════════════════════════════════════════════════
#  Adaptive Auth System — AWS Free-Tier Deployment Script
#  Run: .\deploy_aws.ps1
# ═══════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"

# ── Configuration ──
$APP_NAME = "adaptive-auth-system"
$ENV_NAME = "adaptive-auth-prod"
$REGION = "us-east-1"
$DB_INSTANCE = "adaptive-auth-db"
$DB_NAME = "adaptiveauth"
$DB_USER = "auth_user"
$DB_PASS = "AuthDev2026Pass"
$CACHE_ID = "adaptive-auth-cache"
$S3_BUCKET = "adaptive-auth-models-$(Get-Random -Minimum 10000 -Maximum 99999)"
$ALARM_EMAIL = ""

Write-Host ""
Write-Host "  ═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ☁️  Adaptive Auth — AWS Free-Tier Deployment" -ForegroundColor Cyan
Write-Host "  ═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# ── Pre-flight Checks ──
Write-Host "  [1/8] Pre-flight checks..." -ForegroundColor Yellow

try {
    aws sts get-caller-identity | Out-Null
    Write-Host "    ✅ AWS CLI configured" -ForegroundColor Green
}
catch {
    Write-Host "    ❌ AWS CLI not configured. Run 'aws configure' first." -ForegroundColor Red
    exit 1
}

try {
    eb --version | Out-Null
    Write-Host "    ✅ EB CLI installed" -ForegroundColor Green
}
catch {
    Write-Host "    ❌ EB CLI not installed. Run 'pip install awsebcli' first." -ForegroundColor Red
    exit 1
}

# ── Step 1: Billing Alarm ($1 threshold) ──
Write-Host ""
Write-Host "  [2/8] Setting up billing alarm..." -ForegroundColor Yellow

if (-not $ALARM_EMAIL) {
    $ALARM_EMAIL = Read-Host "    Enter email for billing alerts"
}

# Create SNS topic for billing alerts
$topicArn = aws sns create-topic --name "billing-alarm" --region $REGION --query "TopicArn" --output text
Write-Host "    📧 SNS topic created: $topicArn" -ForegroundColor Gray

# Subscribe email
aws sns subscribe --topic-arn $topicArn --protocol email --notification-endpoint $ALARM_EMAIL --region $REGION | Out-Null
Write-Host "    📧 Check your email ($ALARM_EMAIL) and CONFIRM the subscription!" -ForegroundColor Yellow

# Create CloudWatch billing alarm at $1
aws cloudwatch put-metric-alarm `
    --alarm-name "BillingAlarm-1USD" `
    --alarm-description "Alert when AWS charges exceed 1 USD" `
    --metric-name EstimatedCharges `
    --namespace "AWS/Billing" `
    --statistic Maximum `
    --period 21600 `
    --threshold 1 `
    --comparison-operator GreaterThanThreshold `
    --dimensions "Name=Currency,Value=USD" `
    --evaluation-periods 1 `
    --alarm-actions $topicArn `
    --region "us-east-1" 2>$null

Write-Host "    ✅ Billing alarm set at $1 USD" -ForegroundColor Green

# ── Step 2: S3 Bucket ──
Write-Host ""
Write-Host "  [3/8] Creating S3 bucket for ML models..." -ForegroundColor Yellow

aws s3 mb "s3://$S3_BUCKET" --region $REGION 2>$null
Write-Host "    ✅ S3 bucket: $S3_BUCKET" -ForegroundColor Green

# Upload model files
if (Test-Path "adaptive_auth_model.pkl") {
    aws s3 cp adaptive_auth_model.pkl "s3://$S3_BUCKET/adaptive_auth_model.pkl"
    aws s3 cp label_encoders.pkl "s3://$S3_BUCKET/label_encoders.pkl"
    Write-Host "    ✅ ML models uploaded to S3" -ForegroundColor Green
}
else {
    Write-Host "    ⚠️  Model files not found — will train at build time" -ForegroundColor Yellow
}

# Upload chart images if they exist
if (Test-Path "confusion_matrix.png") {
    aws s3 cp confusion_matrix.png "s3://$S3_BUCKET/confusion_matrix.png"
    aws s3 cp feature_importance.png "s3://$S3_BUCKET/feature_importance.png"
    Write-Host "    ✅ Chart images uploaded" -ForegroundColor Green
}

# ── Step 3: RDS PostgreSQL (Free Tier) ──
Write-Host ""
Write-Host "  [4/8] Creating RDS PostgreSQL (db.t3.micro — free tier)..." -ForegroundColor Yellow

$dbExists = aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE --region $REGION 2>$null
if (-not $dbExists) {
    aws rds create-db-instance `
        --db-instance-identifier $DB_INSTANCE `
        --db-instance-class "db.t3.micro" `
        --engine postgres `
        --engine-version "15" `
        --master-username $DB_USER `
        --master-user-password $DB_PASS `
        --allocated-storage 20 `
        --no-multi-az `
        --no-auto-minor-version-upgrade `
        --backup-retention-period 0 `
        --region $REGION `
        --publicly-accessible | Out-Null
    Write-Host "    ⏳ RDS instance creating (takes 5-10 minutes)..." -ForegroundColor Yellow
}
else {
    Write-Host "    ✅ RDS instance already exists" -ForegroundColor Green
}

# Wait for RDS to be available
Write-Host "    ⏳ Waiting for RDS to become available..." -ForegroundColor Yellow
aws rds wait db-instance-available --db-instance-identifier $DB_INSTANCE --region $REGION
$DB_ENDPOINT = aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE --region $REGION --query "DBInstances[0].Endpoint.Address" --output text
Write-Host "    ✅ RDS ready: $DB_ENDPOINT" -ForegroundColor Green

# ── Step 4: ElastiCache Redis (Free Tier) ──
Write-Host ""
Write-Host "  [5/8] Creating ElastiCache Redis (cache.t3.micro — free tier)..." -ForegroundColor Yellow

$cacheExists = aws elasticache describe-cache-clusters --cache-cluster-id $CACHE_ID --region $REGION 2>$null
if (-not $cacheExists) {
    aws elasticache create-cache-cluster `
        --cache-cluster-id $CACHE_ID `
        --cache-node-type "cache.t3.micro" `
        --engine redis `
        --num-cache-nodes 1 `
        --region $REGION | Out-Null
    Write-Host "    ⏳ ElastiCache creating (takes 5-10 minutes)..." -ForegroundColor Yellow
}
else {
    Write-Host "    ✅ ElastiCache cluster already exists" -ForegroundColor Green
}

# Wait for ElastiCache
Write-Host "    ⏳ Waiting for ElastiCache to become available..." -ForegroundColor Yellow
aws elasticache wait cache-cluster-available --cache-cluster-id $CACHE_ID --region $REGION 2>$null
Start-Sleep -Seconds 10
$REDIS_ENDPOINT = aws elasticache describe-cache-clusters --cache-cluster-id $CACHE_ID --show-cache-node-info --region $REGION --query "CacheClusters[0].CacheNodes[0].Endpoint.Address" --output text
Write-Host "    ✅ ElastiCache ready: $REDIS_ENDPOINT" -ForegroundColor Green

# ── Step 5: Initialize Elastic Beanstalk ──
Write-Host ""
Write-Host "  [6/8] Initializing Elastic Beanstalk..." -ForegroundColor Yellow

if (-not (Test-Path ".elasticbeanstalk")) {
    eb init $APP_NAME --platform "docker" --region $REGION
    Write-Host "    ✅ EB initialized" -ForegroundColor Green
}
else {
    Write-Host "    ✅ EB already initialized" -ForegroundColor Green
}

# ── Step 6: Create/Deploy EB Environment ──
Write-Host ""
Write-Host "  [7/8] Deploying to Elastic Beanstalk (SingleInstance, t3.micro)..." -ForegroundColor Yellow

eb status $ENV_NAME 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    eb create $ENV_NAME `
        --single `
        --instance-type "t3.micro" `
        --timeout 20
}
else {
    eb deploy $ENV_NAME
}

# ── Step 7: Set Environment Variables ──
Write-Host ""
Write-Host "  [8/8] Configuring environment variables..." -ForegroundColor Yellow

$DATABASE_URL = "postgresql://${DB_USER}:${DB_PASS}@${DB_ENDPOINT}:5432/${DB_NAME}"
$REDIS_URL = "redis://${REDIS_ENDPOINT}:6379/0"

eb setenv `
    DATABASE_URL="$DATABASE_URL" `
    REDIS_URL="$REDIS_URL" `
    S3_BUCKET="$S3_BUCKET" `
    SECRET_KEY="$(New-Guid)" `
    AWS_REGION="$REGION" `
    STRIPE_SECRET_KEY="" `
    STRIPE_PUBLISHABLE_KEY="" `
    STRIPE_WEBHOOK_SECRET="" `
    -e $ENV_NAME

Write-Host ""
Write-Host "  ═══════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅  DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "  ═══════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

# Print the URL
$appUrl = eb status $ENV_NAME 2>$null | Select-String "CNAME:" | ForEach-Object { $_.ToString().Split(":")[1].Trim() }
Write-Host "  🌐  SaaS Landing:  http://$appUrl/" -ForegroundColor Cyan
Write-Host "  📖  API Docs:      http://$appUrl/api-docs" -ForegroundColor Cyan
Write-Host "  🔑  Signup:        http://$appUrl/signup" -ForegroundColor Cyan
Write-Host "  👤  Auth Demo:     http://$appUrl/login  (admin / admin123)" -ForegroundColor Cyan
Write-Host ""
Write-Host "  📊  Services Running:" -ForegroundColor Yellow
Write-Host "    • EC2:         t3.micro (free tier)" -ForegroundColor Gray
Write-Host "    • RDS:         db.t3.micro (free tier)" -ForegroundColor Gray
Write-Host "    • ElastiCache: cache.t3.micro (free tier)" -ForegroundColor Gray
Write-Host "    • S3:          $S3_BUCKET" -ForegroundColor Gray
Write-Host ""
Write-Host "  💳  Stripe: Set your keys with 'eb setenv STRIPE_SECRET_KEY=sk_...'" -ForegroundColor Yellow
Write-Host "  ⚠️  Run .\cleanup_aws.ps1 when done to avoid charges!" -ForegroundColor Yellow
Write-Host ""

# Save config for cleanup script
@{
    S3_BUCKET   = $S3_BUCKET
    DB_INSTANCE = $DB_INSTANCE
    CACHE_ID    = $CACHE_ID
    ENV_NAME    = $ENV_NAME
    APP_NAME    = $APP_NAME
    REGION      = $REGION
    TOPIC_ARN   = $topicArn
} | ConvertTo-Json | Out-File -FilePath ".aws_deploy_config.json" -Encoding UTF8
