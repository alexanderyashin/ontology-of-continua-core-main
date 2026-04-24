@echo off
set TARGET=%1
if "%TARGET%"=="" set TARGET=release-check
if "%TARGET%"=="release-check" python -m release_machine evaluate --release oc_core_1_3_2 --channel all --mode dry-run && exit /b %ERRORLEVEL%
if "%TARGET%"=="release-build" python -m release_machine package --release oc_core_1_3_2 --channel all --no-publish && exit /b %ERRORLEVEL%
if "%TARGET%"=="release-test" python simulations/run_all.py --write-report && python -m unittest discover release_machine/tests && exit /b %ERRORLEVEL%
if "%TARGET%"=="release-package" python -m release_machine package --release oc_core_1_3_2 --channel all --no-publish && exit /b %ERRORLEVEL%
if "%TARGET%"=="shit-control" python -m release_machine shit-control --release oc_core_1_3_2 --channel all --max-iterations 5 && exit /b %ERRORLEVEL%
echo Unknown target %TARGET%
exit /b 2
