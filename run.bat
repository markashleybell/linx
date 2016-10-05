@echo off
call ..\scripts\activate.bat
echo Start server on port %HTTP_PLATFORM_PORT%
call python __init__.py