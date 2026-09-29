@echo off
setlocal EnableExtensions
title Swift-1.5 Qwen3.8-27B MTP 150K 8bit-KV :5678

rem ============================================================================
rem Swift15-27B-MTP-150K.bat
rem 150K single-slot profile of Swift15-27B-MTP.bat (same model, runtime, port).
rem ASCII ONLY - Korean chars break cmd parsing (CP949).
rem
rem Changes vs Swift15-27B-MTP.bat
rem   - CTX 150000 on ONE slot (-np 1). The old file split 131072 over 2 slots,
rem     so one request only got 64K. MTP is a single-stream speedup anyway.
rem   - 8-bit KV cache: -ctk q8_0 -ctv q8_0. llama.cpp has NO fp8 KV type
rem     (allowed: f32 f16 bf16 q8_0 q4_0 q4_1 iq4_nl q5_0 q5_1). q8_0-q8_0
rem     flash-attn kernels are in the default CUDA build too (GGML_CUDA_FA_QUANTS
rem     default = q4_0-q4_0;q8_0-q8_0;f16-f16;bf16-bf16), so stock build works.
rem   - MTP draft KV set explicitly with -ctkd/-ctvd. It defaults to f16, and
rem     -ctk/-ctv do NOT change it.
rem   - Vision off by default (VISION=0). MTP skips image batches, and the
rem     mmproj takes VRAM that the 150K KV needs. VISION=1 loads it.
rem   - OOM auto-fallback. If the server dies with out-of-memory, the next start
rem     uses a smaller KV mode:  q8 -> q8k4v (build-faq only) -> q4 -> q4ub1k
rem     and it stops after q4ub1k instead of looping.
rem   - A startup failure that is not OOM (bad flag, bad file) stops with the
rem     last log lines instead of restarting forever.
rem
rem llama.cpp has no --gpu-memory-utilization. VRAM = weights + KV (-c, -ctk/-ctv)
rem + MTP KV (-ctkd/-ctvd) + compute buffers (-b/-ub) + DeltaNet state
rem (-np x spec-draft-n-max). --fit off keeps llama.cpp from changing -c/-ngl.
rem
rem Estimated KV at 150000 tokens (Qwen3.8-27B: 16 full-attention layers,
rem 4 KV heads, head_dim 256; the 48 DeltaNet layers keep a fixed state):
rem   main KV : q8_0/q8_0 4980 MiB, q8_0/q4_0 3809 MiB, q4_0/q4_0 2637 MiB
rem   MTP KV  : q8_0 311 MiB, q4_0 165 MiB, f16 586 MiB
rem ============================================================================

set "HOST=127.0.0.1"
set "PORT=5678"
set "MODEL_DIR=D:\LM-Studio\models\ajgazin\Swift-1.5-Qwen3.8-27B-Uncensored-Dynamic-MTP-GGUF"
set "ORCA_DIR=D:\LM-Studio\models\RentedNoodle\Qwen3.8-27B-OrcaRouter-GSQ-RCO-IQ3_XXS-Uncensored"
set "LOG=D:\llama.cpp\swift15_150k_server.log"

rem ---- knobs -----------------------------------------------------------------
set "CTX=150000"
set "NSLOT=1"
rem MTP draft depth. 2 = old file. Try 3 and compare with Swift15-bench.bat.
set "SPEC_N=2"
rem 1 = load the vision projector (costs VRAM; q8 may then not fit)
set "VISION=0"
rem first KV mode to try: q8 / q8k4v / q4 / q4ub1k
if not defined KV_MODE set "KV_MODE=q8"
set "VRAM_MIN=23000"

rem ---- pick runtime: FA_ALL_QUANTS build first, stock build as fallback ----
set "LLAMA=D:\llama.cpp\src_mtp\build-faq\bin\llama-server.exe"
set "FAQ=1"
if not exist "%LLAMA%" (
  set "FAQ="
  set "LLAMA=D:\llama.cpp\src_mtp\build\bin\Release\llama-server.exe"
)

echo =====================================================================
echo Swift-1.5 Qwen3.8-27B UD-Q4_K_S + MTP - 150K ctx, 1 slot, 8-bit KV
echo RTX 3090 GPU0 only - llama.cpp src_mtp
echo =====================================================================
echo.

if not exist "%LLAMA%" (
  echo [ERROR] llama-server.exe not found: %LLAMA%
  pause
  exit /b 1
)
if not exist "%MODEL_DIR%" (
  echo [ERROR] model folder not found: %MODEL_DIR%
  pause
  exit /b 1
)
if defined FAQ (
  echo [ENGINE] build-faq - all K/V type pairs available
) else (
  echo [ENGINE] stock build - q8k4v mode will be skipped
)

rem ---- pick model: Swift-1.5 Q4_K_S first, any Swift-1.5 GGUF as fallback ----
set "MODEL="
if exist "%MODEL_DIR%\*Swift-1.5*UD-Q4_K_S*.gguf" for %%f in ("%MODEL_DIR%\*Swift-1.5*UD-Q4_K_S*.gguf") do set "MODEL=%%~ff"
if not defined MODEL if exist "%MODEL_DIR%\*Swift-1.5*.gguf" for %%f in ("%MODEL_DIR%\*Swift-1.5*.gguf") do set "MODEL=%%~ff"
if not defined MODEL (
  echo [ERROR] no Swift-1.5 .gguf under %MODEL_DIR%
  pause
  exit /b 1
)
for %%z in ("%MODEL%") do echo [MODEL ] %%~nz  ^(%%~zz bytes^)

rem ---- vision projector (only when VISION=1) --------------------------------
set "MMPROJ_ARG="
if not "%VISION%"=="1" goto VISION_DONE
if exist "%MODEL_DIR%\mmproj-BF16.gguf" (
  set "MMPROJ_ARG=--mmproj "%MODEL_DIR%\mmproj-BF16.gguf""
  echo [VISION] mmproj-BF16.gguf
) else if exist "%ORCA_DIR%\mmproj-Qwen3.8-27B-BF16.gguf" (
  set "MMPROJ_ARG=--mmproj "%ORCA_DIR%\mmproj-Qwen3.8-27B-BF16.gguf""
  echo [VISION] mmproj-Qwen3.8-27B-BF16.gguf from OrcaRouter folder - same base
) else (
  echo [VISION] no mmproj found - starting text-only
)
:VISION_DONE
if not "%VISION%"=="1" echo [VISION] off - text-only, VRAM kept for the 150K KV cache

rem ---- port must be free ------------------------------------------------
netstat -ano | findstr /c:":%PORT% " | findstr /c:"LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo [ERROR] port %PORT% already listening - close the other Swift/OrcaRouter window first.
  pause
  exit /b 1
)

rem ---- VRAM sanity check (warning only) ----------------------------------
set "FREE_MB=0"
for /f %%m in ('powershell -NoProfile -Command "(nvidia-smi -i 0 --query-gpu=memory.free --format=csv,noheader,nounits | Measure-Object -Sum).Sum" 2^>nul') do set "FREE_MB=%%m"
if not "%FREE_MB%"=="0" if %FREE_MB% LSS %VRAM_MIN% (
  echo [WARN  ] only %FREE_MB% MiB VRAM free on GPU0.
  echo          150K mode wants about %VRAM_MIN% MiB free.
  timeout /t 8 /nobreak >nul
) else (
  if not "%FREE_MB%"=="0" echo [VRAM  ] %FREE_MB% MiB free on GPU0 - OK
)

echo.
echo Web UI after startup:  http://%HOST%:%PORT%
echo Log file            :  %LOG%
echo Speed test          :  run Swift15-bench.bat after the server is up
echo.

for %%d in ("%LLAMA%") do cd /d "%%~dpd"

set "CUDA_DEVICE_ORDER=PCI_BUS_ID"
set "CUDA_VISIBLE_DEVICES=0"

:START
call :SETMODE
if errorlevel 1 goto END_FAIL
echo [KV    ] KV_MODE=%KV_MODE% : %KVARGS% -ub %UBATCH%
echo [CTX   ] %CTX% tokens on %NSLOT% slot - MTP draft n-max %SPEC_N%
if exist "%LOG%" del /q "%LOG%" >nul 2>&1

"%LLAMA%" ^
 -m "%MODEL%" %MMPROJ_ARG% ^
 --alias Swift-1.5-Qwen3.8-27B-Uncensored-Dynamic-MTP-UD-Q4_K_S ^
 --host %HOST% --port %PORT% ^
 -ngl 99 -sm none -mg 0 ^
 -c %CTX% -b %BATCH% -ub %UBATCH% -np %NSLOT% -t 8 ^
 --flash-attn on %KVARGS% ^
 --jinja ^
 --reasoning-budget 256 ^
 --reasoning-budget-message "Considering the limited time by the user, I have to give the solution based on the thinking directly now." ^
 --spec-type draft-mtp --spec-draft-n-max %SPEC_N% --spec-draft-backend-sampling ^
 --fit off ^
 --temp 1.0 --top-k 20 --top-p 0.95 --min-p 0 --repeat-penalty 1.0 ^
 --log-file "%LOG%"

echo.
if not exist "%LOG%" (
  echo [ERROR] server exited before it wrote %LOG%
  echo         Read the messages above - usually an unknown argument or a missing DLL.
  goto END_FAIL
)
findstr /i /c:"out of memory" /c:"failed to allocate" /c:"unable to allocate" "%LOG%" >nul 2>&1
if errorlevel 1 goto NOT_OOM

set "OOM_FROM=%KV_MODE%"
set "KV_MODE=%NEXT_MODE%"
if /i "%KV_MODE%"=="stop" (
  echo [ERROR] out of VRAM even in the smallest 150K mode q4ub1k.
  echo         Close other programs on GPU0, or lower CTX at the top of this file.
  goto END_FAIL
)
echo [OOM   ] KV_MODE=%OOM_FROM% did not fit - retrying with KV_MODE=%KV_MODE% in 5 sec
timeout /t 5 /nobreak >nul
goto START

:NOT_OOM
rem never reached "listening on" = startup error that a restart will not fix
findstr /c:"listening on" "%LOG%" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] server stopped during startup - not an out-of-memory error.
  echo         Last lines of the log - paste them into the chat:
  powershell -NoProfile -Command "Get-Content -Tail 20 -LiteralPath '%LOG%'"
  goto END_FAIL
)

:RESTART_SAME
echo [RESTART] server exited - restarting in 5 sec (Ctrl+C to stop)
timeout /t 5 /nobreak >nul
goto START

:END_FAIL
echo.
echo Log file: %LOG%
pause
exit /b 1

rem ---- KV modes: sets KVARGS, BATCH, UBATCH and the OOM fallback NEXT_MODE ----
:SETMODE
set "BATCH=2048"
set "UBATCH=2048"
if /i "%KV_MODE%"=="q8" (
  set "KVARGS=-ctk q8_0 -ctv q8_0 -ctkd q8_0 -ctvd q8_0"
  if defined FAQ (set "NEXT_MODE=q8k4v") else (set "NEXT_MODE=q4")
  exit /b 0
)
if /i "%KV_MODE%"=="q8k4v" (
  if not defined FAQ (
    echo [KV    ] q8k4v needs build-faq - using q4 instead
    set "KV_MODE=q4"
    goto SETMODE
  )
  set "KVARGS=-ctk q8_0 -ctv q4_0 -ctkd q8_0 -ctvd q8_0"
  set "NEXT_MODE=q4"
  exit /b 0
)
if /i "%KV_MODE%"=="q4" (
  set "KVARGS=-ctk q4_0 -ctv q4_0 -ctkd q4_0 -ctvd q4_0"
  set "NEXT_MODE=q4ub1k"
  exit /b 0
)
if /i "%KV_MODE%"=="q4ub1k" (
  set "KVARGS=-ctk q4_0 -ctv q4_0 -ctkd q4_0 -ctvd q4_0"
  set "BATCH=1024"
  set "UBATCH=1024"
  set "NEXT_MODE=stop"
  exit /b 0
)
echo [ERROR] unknown KV_MODE=%KV_MODE% - use q8, q8k4v, q4 or q4ub1k
exit /b 1
