@echo off
@REM set /p PROTO_SRC="proto SOURCE path(file name included without extension): "
@REM set /p PROTO_DEST="proto DESTINATION path: "
@REM set PROTO_DEST=%1

:: Estilo de uso del comando  -------> compile-to-python <proto-file-name> <destination-folder>     ||| [default <proto-file-name>: *(todos los .proto del directorio actual)] [default <destination-folder>: generated_grpc]

if "%~1"=="" (
    set PROTO_SRC=*
) else (
    set PROTO_SRC=%~1
)
if "%~2"=="" (
    set PROTO_DEST=generated_grpc
) else (
    set PROTO_DEST=%~2
)

echo "Installing required packages..."
python -m pip install --upgrade pip
python -m pip install grpcio grpcio-tools

echo "Creating directory..."
mkdir %PROTO_DEST%

echo "Generating gRPC Python code..."
python -m grpc_tools.protoc --proto_path=. --python_out=./%PROTO_DEST% --pyi_out=./%PROTO_DEST% --grpc_python_out=./%PROTO_DEST% *.proto
EXIT /B 0