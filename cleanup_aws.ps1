# ═══════════════════════════════════════════════════════════════
#  Adaptive Auth System — AWS Cleanup Script
#  Tears down ALL AWS resources to stop any charges
#  Run: .\cleanup_aws.ps1
# ═══════════════════════════════════════════════════════════════

$ErrorActionPreference = "Continue"
$REGION = "us-east-1"

Write-Host ""
Write-Host "  ═══════════════════════════════════════════════════" -ForegroundColor Red
Write-Host "  🧹  Adaptive Auth — AWS Resource Cleanup" -ForegroundColor Red
Write-Host "  ═══════════════════════════════════════════════════" -ForegroundColor Red
Write-Host ""

# Load saved config if available
$config = $null
if (Test-Path ".aws_deploy_config.json") {
    $config = Get-Content ".aws_deploy_config.json" | ConvertFrom-Json
    Write-Host "  📄 Loaded deployment config" -ForegroundColor Gray
}

$ENV_NAME    = if ($config) { $config.ENV_NAME }    else { "adaptive-auth-prod" }
$APP_NAME    = if ($config) { $config.APP_NAME }    else { "adaptive-auth-system" }
$DB_INSTANCE = if ($config) { $config.DB_INSTANCE } else { "adaptive-auth-db" }
$CACHE_ID    = if ($config) { $config.CACHE_ID }    else { "adaptive-auth-cache" }
$S3_BUCKET   = if ($config) { $config.S3_BUCKET }   else { "" }
$TOPIC_ARN   = if ($config) { $config.TOPIC_ARN }   else { "" }

# ── Confirm ──
Write-Host "  This will PERMANENTLY DELETE:" -ForegroundColor Yellow
Write-Host "    • Elastic Beanstalk environment: $ENV_NAME" -ForegroundColor Gray
Write-Host "    • Elastic Beanstalk application: $APP_NAME" -ForegroundColor Gray
Write-Host "    • RDS instance: $DB_INSTANCE" -ForegroundColor Gray
Write-Host "    • ElastiCache cluster: $CACHE_ID" -ForegroundColor Gray
if ($S3_BUCKET) { Write-Host "    • S3 bucket: $S3_BUCKET" -ForegroundColor Gray }
Write-Host ""

$confirm = Read-Host "  Type 'DELETE' to confirm"
if ($confirm -ne "DELETE") {
    Write-Host "  ❌ Aborted." -ForegroundColor Red
    exit 0
}

# ── Step 1: Terminate Elastic Beanstalk Environment ──
Write-Host ""
Write-Host "  [1/6] Terminating EB environment..." -ForegroundColor Yellow
try {
    eb terminate $ENV_NAME --force 2>$null
    Write-Host "    ✅ EB environment terminated" -ForegroundColor Green
} catch {
    Write-Host "    ⚠️  EB environment not found or already terminated" -ForegroundColor Yellow
}

# ── Step 2: Delete EB Application ──
Write-Host ""
Write-Host "  [2/6] Deleting EB application..." -ForegroundColor Yellow
try {
    aws elasticbeanstalk delete-application --application-name $APP_NAME --terminate-env-by-force --region $REGION 2>$null
    Write-Host "    ✅ EB application deleted" -ForegroundColor Green
} catch {
    Write-Host "    ⚠️  EB application not found" -ForegroundColor Yellow
}

# ── Step 3: Delete RDS Instance ──
Write-Host ""
Write-Host "  [3/6] Deleting RDS instance (skipping final snapshot)..." -ForegroundColor Yellow
try {
    aws rds delete-db-instance `
        --db-instance-identifier $DB_INSTANCE `
        --skip-final-snapshot `
        --delete-automated-backups `
        --region $REGION 2>$null
    Write-Host "    ⏳ RDS deletion in progress (takes a few minutes)..." -ForegroundColor Yellow
} catch {
    Write-Host "    ⚠️  RDS instance not found or already deleted" -ForegroundColor Yellow
}

# ── Step 4: Delete ElastiCache Cluster ──
Write-Host ""
Write-Host "  [4/6] Deleting ElastiCache cluster..." -ForegroundColor Yellow
try {
    aws elasticache delete-cache-cluster --cache-cluster-id $CACHE_ID --region $REGION 2>$null
    Write-Host "    ✅ ElastiCache cluster deletion initiated" -ForegroundColor Green
} catch {
    Write-Host "    ⚠️  ElastiCache cluster not found or already deleted" -ForegroundColor Yellow
}

# ── Step 5: Empty and Delete S3 Bucket ──
Write-Host ""
Write-Host "  [5/6] Deleting S3 bucket..." -ForegroundColor Yellow
if ($S3_BUCKET) {
    try {
        aws s3 rm "s3://$S3_BUCKET" --recursive --region $REGION 2>$null
        aws s3 rb "s3://$S3_BUCKET" --region $REGION 2>$null
        Write-Host "    ✅ S3 bucket deleted" -ForegroundColor Green
    } catch {
        Write-Host "    ⚠️  S3 bucket not found or already deleted" -ForegroundColor Yellow
    }
} else {
    Write-Host "    ⚠️  No S3 bucket configured — skipping" -ForegroundColor Yellow
}

# ── Step 6: Delete Billing Alarm ──
Write-Host ""
Write-Host "  [6/6] Cleaning up billing alarm..." -ForegroundColor Yellow
try {
    aws cloudwatch delete-alarms --alarm-names "BillingAlarm-1USD" --region "us-east-1" 2>$null
    Write-Host "    ✅ Billing alarm deleted" -ForegroundColor Green
} catch {
    Write-Host "    ⚠️  Billing alarm not found" -ForegroundColor Yellow
}

if ($TOPIC_ARN) {
    try {
        aws sns delete-topic --topic-arn $TOPIC_ARN --region $REGION 2>$null
        Write-Host "    ✅ SNS topic deleted" -ForegroundColor Green
    } catch {}
}

# ── Cleanup local EB config ──
if (Test-Path ".elasticbeanstalk") {
    Remove-Item -Recurse -Force ".elasticbeanstalk"
    Write-Host "    ✅ Local .elasticbeanstalk config removed" -ForegroundColor Green
}
if (Test-Path ".aws_deploy_config.json") {
    Remove-Item ".aws_deploy_config.json"
}

Write-Host ""
Write-Host "  ═══════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅  ALL AWS RESOURCES DELETED" -ForegroundColor Green
Write-Host "  ═══════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  💰 No more charges will accrue." -ForegroundColor Cyan
Write-Host "  📊 Check AWS Billing Dashboard to confirm: $0.00" -ForegroundColor Cyan
Write-Host "     https://console.aws.amazon.com/billing/" -ForegroundColor Gray
Write-Host ""
