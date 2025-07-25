# run_comprehensive_tests.ps1
Write-Host "Starting Comprehensive Error Handling Tests..." -ForegroundColor Green

# Start mock API in background
Write-Host "Starting mock API..." -ForegroundColor Yellow
$apiProcess = Start-Process -FilePath "python" -ArgumentList "mock_api.py" -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 5

# Function to cleanup
function Cleanup {
    Write-Host "Cleaning up..." -ForegroundColor Yellow
    if ($apiProcess -and !$apiProcess.HasExited) {
        try {
            Stop-Process -Id $apiProcess.Id -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Host "Could not stop API process" -ForegroundColor Yellow
        }
    }
}

# Register cleanup on script exit
try {
    # Run all test phases
    Write-Host "Phase 1: Unit Tests" -ForegroundColor Cyan
    try {
        $unitTestResult = & pytest test_error_handling.py -v
        if ($LASTEXITCODE -ne 0) { 
            Write-Host "Unit tests failed" -ForegroundColor Red 
        } else {
            Write-Host "Unit tests passed" -ForegroundColor Green
        }
    } catch {
        Write-Host "Error running unit tests: $($_.Exception.Message)" -ForegroundColor Red
    }

    Write-Host "Phase 2: Integration Tests" -ForegroundColor Cyan
    try {
        $integrationTestResult = & pytest test_integration_failures.py -v
        if ($LASTEXITCODE -ne 0) { 
            Write-Host "Integration tests failed" -ForegroundColor Red 
        } else {
            Write-Host "Integration tests passed" -ForegroundColor Green
        }
    } catch {
        Write-Host "Error running integration tests: $($_.Exception.Message)" -ForegroundColor Red
    }

    Write-Host "Phase 3: Stress Tests (Limited for Windows)" -ForegroundColor Cyan
    try {
        $stressTestResult = & pytest test_stress_and_performance.py -v --timeout=60
        if ($LASTEXITCODE -ne 0) { 
            Write-Host "Stress tests failed" -ForegroundColor Red 
        } else {
            Write-Host "Stress tests passed" -ForegroundColor Green
        }
    } catch {
        Write-Host "Error running stress tests: $($_.Exception.Message)" -ForegroundColor Red
    }

    Write-Host "Phase 4: Logging Validation" -ForegroundColor Cyan
    try {
        $loggingTestResult = & pytest test_logging_validation.py -v
        if ($LASTEXITCODE -ne 0) { 
            Write-Host "Logging tests failed" -ForegroundColor Red 
        } else {
            Write-Host "Logging tests passed" -ForegroundColor Green
        }
    } catch {
        Write-Host "Error running logging tests: $($_.Exception.Message)" -ForegroundColor Red
    }

    Write-Host "Phase 5: End-to-End Tests" -ForegroundColor Cyan

    # Test with valid spec
    Write-Host "Testing with valid specification..." -ForegroundColor Green
    try {
        $env:MAX_ATTEMPTS = "2"
        & python main.py
    } catch {
        Write-Host "Error in valid spec test: $($_.Exception.Message)" -ForegroundColor Red
    }

    # Test with missing spec
    Write-Host "Testing with missing specification..." -ForegroundColor Yellow
    try {
        $env:SPEC_PATH = "nonexistent.yaml"
        $env:MAX_ATTEMPTS = "2"
        & python main.py
    } catch {
        Write-Host "Error in missing spec test: $($_.Exception.Message)" -ForegroundColor Red
    }

    # Test with malformed spec
    Write-Host "Testing with malformed specification..." -ForegroundColor Yellow
    try {
        "invalid yaml content" | Out-File -FilePath "temp_malformed.yaml" -Encoding UTF8
        $env:SPEC_PATH = "temp_malformed.yaml"
        $env:MAX_ATTEMPTS = "2"
        & python main.py
        Remove-Item "temp_malformed.yaml" -ErrorAction SilentlyContinue
    } catch {
        Write-Host "Error in malformed spec test: $($_.Exception.Message)" -ForegroundColor Red
        Remove-Item "temp_malformed.yaml" -ErrorAction SilentlyContinue
    }

    Write-Host "Comprehensive testing complete!" -ForegroundColor Green

} catch {
    Write-Host "Critical error during testing: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Cleanup
}

# Reset environment variables
Remove-Item Env:SPEC_PATH -ErrorAction SilentlyContinue
Remove-Item Env:MAX_ATTEMPTS -ErrorAction SilentlyContinue

Write-Host "Test script finished." -ForegroundColor Cyan
