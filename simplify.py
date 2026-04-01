import onnx
from onnxsim import simplify

model = onnx.load(r"C:\Users\acer\Downloads\agrosheild\backend\models\best1.onnx")
model_simp, check = simplify(model)

onnx.save(model_simp, r"C:\Users\acer\Downloads\agrosheild\backend\models\best1_simplified.onnx")