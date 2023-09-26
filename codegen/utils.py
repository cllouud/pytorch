# Copyright (c) 2023 Huawei Technologies Co., Ltd
# All rights reserved.
#
# Licensed under the BSD 3-Clause License  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://opensource.org/licenses/BSD-3-Clause
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import defaultdict
import os
import sys
import stat
import traceback
from typing import List, Optional, Set, Dict
import yaml

from torchgen.context import native_function_manager
from torchgen.model import (
    Arguments,
    DispatchKey,
    is_cuda_dispatch_key,
    NativeFunction,
    NativeFunctionsGroup,
    FunctionSchema,
)
from torchgen.api import cpp
from torchgen.api.translate import translate
from torchgen.api.types import Binding, CppSignatureGroup, kernel_signature
from torchgen.utils import Target
from torchgen.gen import LineLoader

GLOBAL_STRUCTURED_OP_INFO_CACHE = defaultdict(str)
GLOBAL_OPAPI_INFO_CACHE = set()

CUSTOM_YAML_NAME = "npu_native_functions_by_codegen.yaml"
FIELDS_TO_REMOVE = ["wrap_impl", "impl_name", "impl_ns", "op_api"]


def parse_npu_yaml(custom_path: str) -> Dict:
    if not os.path.exists(custom_path):
        return {}
    from io import StringIO
    f_str = StringIO()
    with open(custom_path, 'r') as f:
        for line in f:
            if ':' not in line:
                continue
            f_str.write(line)

    f_str.seek(0)
    source_es = yaml.load(f_str, Loader=LineLoader)
    return source_es


def merge_yaml(base_data, additional_data):
    """Merge two YAML data structures. If there's a conflict, the base data will take precedence."""
    map_dict = {"official": "supported"}
    key_map = lambda x: map_dict.get(x, x)
    if isinstance(base_data, dict):
        for key, value in additional_data.items():
            if key_map(key) not in base_data:
                base_data[key_map(key)] = value
            else:
                base_data[key_map(key)] = merge_yaml(base_data[key_map(key)], value)
    elif isinstance(base_data, list):
        for item in additional_data:
            if item not in base_data:
                base_data.append(item)
    return base_data


def merge_custom_yaml(pta_path, op_plugin_path):
    with open(pta_path, 'r') as pta_file:
        pta_es = yaml.safe_load(pta_file)
    with open(op_plugin_path, 'r') as op_plugin_file:
        op_es = yaml.safe_load(op_plugin_file)

    merged_yaml = merge_yaml(pta_es, op_es)
    merged_yaml_path = gen_custom_yaml_path(pta_path)
    with open(merged_yaml_path, 'w') as outfile:
        yaml.dump(merged_yaml, outfile, default_flow_style=False, width=float("inf"))
    return merged_yaml


def filed_tag(custom_es):
    for e in custom_es:
        if not isinstance(e, Dict):
            print(e)
            continue
        for field in FIELDS_TO_REMOVE:
            e.pop(field, None)
    return custom_es

def parse_opplugin_yaml(custom_path: str) -> Dict:

    source_es = parse_npu_yaml(custom_path)

    custom = source_es.pop('custom', [])
    if custom is None:
        custom = []  # Allow an empty list of supported ops
    official = source_es.pop('official', [])
    if official is None:
        official = []  # Allow an empty list of supported ops

    support_ops = custom + official

    symint = source_es.pop("symint", [])
    if symint is None:
        symint = []
    symint = [op['func'] if isinstance(op, Dict) else op for op in symint]
    symint_set = set([str(FunctionSchema.parse(op).name) for op in symint])

    global GLOBAL_STRUCTURED_OP_INFO_CACHE
    for x in support_ops:
        funcs = x.get("func", None)
        assert isinstance(funcs, str), f'not a str : {funcs}'
        func = FunctionSchema.parse(funcs)
        wrap_name = cpp.name(func)
        op_key = str(func.name)
        if op_key in symint_set:
            wrap_name += "_symint"
        cur_wrap_name = GLOBAL_STRUCTURED_OP_INFO_CACHE.get(op_key, "")
        if cur_wrap_name and cur_wrap_name != wrap_name:
            print(f"Find different wrap_name for {cur_wrap_name} and {wrap_name} between pta and opplugin, ",
                  f"with {wrap_name} being used as the actual wrap_name")
        GLOBAL_STRUCTURED_OP_INFO_CACHE[op_key] = wrap_name

    return source_es


def rename_privateuse1_dispatch_key():
    # rename DispatcherKey about PrivateUse1
    custom_backend = "NPU"
    def PrivateUse1Str(self):
        return self.name.replace("PrivateUse1", custom_backend)

    @staticmethod
    def parse(value: str) -> "DispatchKey":
        for k, v in DispatchKey.__members__.items():
            if k == value.replace(custom_backend, "PrivateUse1"):
                return v
        raise AssertionError(f"unknown dispatch key {value}")

    DispatchKey.__str__ = PrivateUse1Str
    DispatchKey.parse = parse


def get_torchgen_dir():
    # get path of torchgen, then get tags.yaml and native_functions.yaml
    try:
        import torchgen
        return os.path.dirname(os.path.abspath(torchgen.__file__))
    except Exception:
        _, _, exc_traceback = sys.exc_info()
        frame_summary = traceback.extract_tb(exc_traceback)[-1]
        return os.path.dirname(frame_summary.filename)


# This function is to add profiler information for each operator, which is later extended in the official
def gen_unstructured(
    self, f: NativeFunction, g: Optional[NativeFunctionsGroup] = None
) -> Optional[str]:
    with native_function_manager(f):
        inplace_meta = False
        gets_out_inplace_wrapper = False
        if not self.backend_index.has_kernel(f):
            return None
        if f.manual_kernel_registration:
            return None

        if (
            self.target is Target.REGISTRATION
            and not self.selector.is_native_function_selected(f)
        ):
            return None

        sig = self.wrapper_kernel_sig(f)

        name = sig.name()
        returns_type = sig.returns_type().cpp_type()
        args = sig.arguments()
        args_str = ", ".join(a.defn() for a in args)

        # See Note [Direct dispatch bindings]
        cpp_sig_group = CppSignatureGroup.from_native_function(
            f, method=False, fallback_binding=False
        )

        if self.target is Target.NAMESPACED_DECLARATION:
            result = ""
            for cpp_sig in cpp_sig_group.signatures(symint=self.symint):
                result += f"TORCH_API {cpp_sig.decl()};\n"
            return result
        elif self.target is Target.NAMESPACED_DEFINITION:

            def generate_defn(cpp_sig: CppSignature) -> str:
                return f"""
{cpp_sig.defn()} {{
return {sig.name()}({', '.join(e.expr for e in translate(cpp_sig.arguments(), sig.arguments()))});
}}
"""

            result = ""
            for cpp_sig in cpp_sig_group.signatures(symint=self.symint):
                result += generate_defn(cpp_sig)
            return result

        elif self.target is Target.ANONYMOUS_DEFINITION:
            # short circuit for inplace_meta
            if inplace_meta:
                assert f.func.arguments.self_arg is not None
                self_arg_name = f.func.arguments.self_arg.argument.name
                return f"""
{returns_type} {name}({args_str}) {{
TORCH_CHECK_NOT_IMPLEMENTED({self_arg_name}.is_meta(),
"Cannot inplace into non-meta tensor with meta tensor argument");
return {self_arg_name};
}}
"""

            # short circuit for generated inplace/out wrappers
            if gets_out_inplace_wrapper:
                return self.gen_out_inplace_wrapper(f, g)

            metadata = self.backend_index.get_kernel(f)
            if metadata is None:
                return None
            if self.class_method_name is None:
                impl_name = f"{metadata.cpp_namespace}::{metadata.kernel}"
            else:
                impl_name = f"{metadata.cpp_namespace}::{self.class_method_name}::{metadata.kernel}"
            kernel_sig = kernel_signature(f, self.backend_index)

            args_exprs_str = ", ".join(
                e.expr
                for e in translate(
                    sig.arguments(), kernel_sig.arguments(), method=False
                )
            )

            device_check = "  // No device check\n"
            # Backends that require device guards presumably also require device checks.
            if self.backend_index.device_guard:
                device_check_args = itertools.chain(
                    f.func.arguments.out, f.func.arguments.flat_positional
                )
                device_check = RegisterDispatchKey.gen_device_check(
                    f.device_check, list(device_check_args), name
                )

            device_guard = "// DeviceGuard omitted"  # default
            record_func_def = """
#ifndef BUILD_LIBTORCH
torch_npu::profiler::NPURecordFunction guard;
#endif 
"""
            if f.device_guard and self.backend_index.device_guard:
                has_tensor_options = any(
                    isinstance(a, TensorOptionsArguments)
                    for a in f.func.arguments.non_out
                )
                if has_tensor_options:
                    # kernel is creating a tensor
                    device_guard = """
const DeviceGuard device_guard(device_or_default(device));"""

                    # CUDA requires special handling
                    if is_cuda_dispatch_key(self.backend_index.dispatch_key):
                        device_guard = (
                            f"globalContext().lazyInitCUDA();\n{device_guard}"
                        )
                else:
                    # kernel is operating on existing tensors

                    # There is precedence for which argument we use to do
                    # device guard.  This describes the precedence order.
                    self_arg = (
                        [f.func.arguments.self_arg.argument]
                        if f.func.arguments.self_arg is not None
                        else []
                    )
                    candidate_args = itertools.chain(
                        self_arg,
                        f.func.arguments.out,
                        f.func.arguments.flat_positional,
                    )

                    # Only tensor like arguments are eligible
                    device_of = next(
                        (
                            f"{a.name}"
                            for a in candidate_args
                            if a.type.is_tensor_like()
                        ),
                        None,
                    )
                    if device_of is not None:
                        device_guard = f"const OptionalDeviceGuard device_guard(device_of({device_of}));"
            op_key = str(f.func.name)
            if enable_opplugin():
                if op_key in GLOBAL_STRUCTURED_OP_INFO_CACHE:
                    impl_name = f"op_plugin::{GLOBAL_STRUCTURED_OP_INFO_CACHE[op_key]}"

            if is_opapi(op_key) and not is_op_valid(op_key):
                op_api_impl_name = f"{metadata.cpp_namespace}::NPUNativeOpApiFunctions::{metadata.kernel}"
                tensor_check_str = ""
                tensor_check_list = []
                for a in args:
                    if a.argument.type.is_tensor_like():
                        tensor_check_list.append(f"at_npu::native::FormatHelper::IsOpInputBaseFormat({a.name})")
                if tensor_check_list:
                    tensor_check_str = f" && {' && '.join(tensor_check_list)}"
                return_code = f"""\
if (at_npu::native::env::CheckJitDisable(){tensor_check_str}) {{
        return {op_api_impl_name}({args_exprs_str});
    }} else {{
        return {impl_name}({args_exprs_str});
    }}
"""
            else:
                return_code = f"""\
    return {impl_name}({args_exprs_str});
"""

            return f"""\
namespace {{

{returns_type} {name}({args_str}) {{
{device_check}

{device_guard}
{record_func_def}
{return_code}
}}

}} // anonymous namespace
"""

        elif self.target is Target.REGISTRATION:
            if f.manual_kernel_registration or self.skip_dispatcher_op_registration:
                return None
            else:
                payload = f"TORCH_FN({name})"
                return f'm.impl("{f.func.name}",\n{payload});\n'
        else:
            assert_never(self.target)


def arguments(
    arguments: Arguments,
    *,
    faithful: bool,
    symint: bool = False,
    method: bool,
    cpp_no_default_args: Set[str],
) -> List[Binding]:
    args: List[Union[Argument, TensorOptionsArguments, SelfArgument]] = []
    args.extend(arguments.non_out)
    args.extend(arguments.out)
    return [
        r.no_default() if faithful else r
        for a in args
        for r in cpp.argument(
            a,
            faithful=faithful,
            symint=symint,
            method=method,
            has_tensor_options=arguments.tensor_options is not None,
            cpp_no_default_args=cpp_no_default_args,
        )
    ]


def add_header_to_template_file():
    torchgen_path = get_torchgen_dir()
    template_dir = os.path.join(torchgen_path, "packaged/ATen/templates/DispatchKeyNativeFunctions.h")
    with open(template_dir, "r") as file:
        template_content = file.read()
    if "#include <ATen/ATen.h>" not in template_content:
        template_content = template_content.replace("#include <ATen/Tensor.h>",
                                                    "#include <ATen/Tensor.h>\n#include <ATen/ATen.h>")
        with os.fdopen(os.open(template_dir, os.O_WRONLY, stat.S_IWUSR | stat.S_IRUSR), "w") as file:
            file.write(template_content)


def enable_opplugin() -> bool:
    # enable op_plugin, if path of third_party/op-plugin is valid.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    op_plugin_path = os.path.join(base_dir, '../third_party/op-plugin/op_plugin')
    return os.path.exists(op_plugin_path)


def is_op_valid(op_key: str) -> bool:
    return True if op_key in GLOBAL_STRUCTURED_OP_INFO_CACHE else False


def get_opplugin_wrap_name(func) -> str:
    op_key = str(func.func.name) if type(func) is NativeFunction else func
    return GLOBAL_STRUCTURED_OP_INFO_CACHE.get(op_key, None)


def gen_custom_yaml_path(original_path, codegen_yaml_filename=CUSTOM_YAML_NAME):
    new_path = os.path.join(os.path.dirname(original_path), codegen_yaml_filename)
    return new_path


def update_opapi_info(op_info):
    global GLOBAL_OPAPI_INFO_CACHE
    if isinstance(op_info, str):
        return
    elif isinstance(op_info, dict):
        if op_info.get("op_api", False):
            GLOBAL_OPAPI_INFO_CACHE.add(op_info.get("func").split("(")[0])
    else:
        print(f"Warning: Unsupported parameter types, only str and dict is supported, but input is {type(op_info)}")


def is_opapi(op_key):
    global GLOBAL_OPAPI_INFO_CACHE
    return op_key in GLOBAL_OPAPI_INFO_CACHE