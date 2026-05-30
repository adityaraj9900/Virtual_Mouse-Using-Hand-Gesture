"""PyInstaller hook for mediapipe — collects model files and hidden imports."""

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

datas = collect_data_files("mediapipe")
binaries = collect_dynamic_libs("mediapipe")

hiddenimports = [
    "mediapipe.python._framework_bindings",
    "mediapipe.python.solutions",
    "mediapipe.python.solutions.hands",
    "mediapipe.python.solutions.drawing_utils",
    "mediapipe.python.solutions.drawing_styles",
    "google.protobuf",
    "google.protobuf.descriptor",
    "google.protobuf.descriptor_pool",
    "google.protobuf.reflection",
    "google.protobuf.symbol_database",
    "google.protobuf.timestamp_pb2",
]
