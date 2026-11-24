# Cài Tesseract OCR trên Windows + dữ liệu tiếng Việt
$ErrorActionPreference = "Stop"

Write-Host "=== CÀI OCR LOCAL CHO TRỢ LÝ THỊ GIÁC AI ===" -ForegroundColor Cyan

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "Không tìm thấy winget. Hãy cài App Installer/Windows Package Manager trước." -ForegroundColor Red
    exit 1
}

Write-Host "1/3 Cài Tesseract OCR..." -ForegroundColor Yellow
winget install --id UB-Mannheim.TesseractOCR -e --accept-package-agreements --accept-source-agreements

$paths = @(
    "C:\Program Files\Tesseract-OCR",
    "C:\Program Files (x86)\Tesseract-OCR"
)
$tessDir = $paths | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $tessDir) {
    Write-Host "Không tìm thấy thư mục Tesseract sau khi cài. Hãy mở terminal mới rồi chạy lại script." -ForegroundColor Red
    exit 1
}

Write-Host "2/3 Tải dữ liệu OCR tiếng Việt..." -ForegroundColor Yellow
$langDir = Join-Path $tessDir "tessdata"
New-Item -ItemType Directory -Force -Path $langDir | Out-Null
$vie = Join-Path $langDir "vie.traineddata"
$eng = Join-Path $langDir "eng.traineddata"
Invoke-WebRequest -Uri "https://github.com/tesseract-ocr/tessdata_fast/raw/main/vie.traineddata" -OutFile $vie
if (-not (Test-Path $eng)) {
    Invoke-WebRequest -Uri "https://github.com/tesseract-ocr/tessdata_fast/raw/main/eng.traineddata" -OutFile $eng
}

Write-Host "3/3 Hoàn tất." -ForegroundColor Green
Write-Host "Tesseract: $tessDir\tesseract.exe"
Write-Host "OCR tiếng Việt: $vie"
Write-Host "Hãy đóng/mở lại VS Code Terminal rồi chạy: pip install -r requirements.txt"
