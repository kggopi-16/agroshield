import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType

# Path to your original 97MB model
model_fp32 = r'backend\models\best1.onnx'

# Path for the new compressed model
model_int8 = 'model_quantized.onnx'

# Apply dynamic INT8 quantization
quantize_dynamic(
    model_input=model_fp32, 
    model_output=model_int8, 
    weight_type=QuantType.QInt8  # Quantizes float32 weights to 8-bit integers
)

print(f"Quantization complete! Saved to {model_int8}")
