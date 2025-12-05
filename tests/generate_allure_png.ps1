# ----------------------------
# Run tests and generate Allure JSON
# ----------------------------
pytest tests/ --alluredir=reports/allure -v

# ----------------------------
# Generate HTML report
# ----------------------------
allure generate reports/allure -o reports/allure-report --clean

# ----------------------------
# Take a screenshot of the report as PNG using Chrome headless
# ----------------------------
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$htmlReport = "$PWD\reports\allure-report\index.html"
$pngReport  = "$PWD\reports\allure-report\AllureReport.png"

Start-Process $chrome "--headless --disable-gpu --screenshot=$pngReport --window-size=1920,1080 file:///$htmlReport" -Wait

Write-Host "Allure report saved as PNG: $pngReport"
