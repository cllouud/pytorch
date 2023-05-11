from torch.serialization import register_package

from .module import apply_module_patch
from .tensor_methods import add_tensor_methods
from .serialization import save, load, _npu_tag, _npu_deserialize
from .storage import add_storage_methods
from .combine_tensors import npu_combine_tensors, get_part_combined_tensor, is_combined_tensor_valid

serialization_patches = [
    ["save", save],
    ["load", load],
]

register_package(30, _npu_tag, _npu_deserialize)
