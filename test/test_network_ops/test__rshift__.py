# Copyright (c) 2020 Huawei Technologies Co., Ltd
# Copyright (c) 2019, Facebook CORPORATION. 
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

import torch
import torch_npu
import numpy as np

from torch_npu.testing.common_utils import TestCase, run_tests
from torch_npu.testing.common_device_type import instantiate_device_type_tests
from torch_npu.testing.util_test import create_common_tensor


class TestRshift(TestCase):
    def cpu_op_exec(self, input1, input2):
        output = input1.__rshift__(input2)
        output = output.numpy()
        return output

    def npu_op_exec(self, input1, input2):
        output = input1.__rshift__(input2)
        output = output.to("cpu")
        output = output.numpy()
        return output

    def test_rshift_tensor(self, device):
        format_list = [0]
        shape_list = [(256, 32, 56)]
        shape_format = [
            [np.int32, i, j] for i in format_list for j in shape_list
        ]
        for item in shape_format:
            cpu_input1, npu_input1 = create_common_tensor(item, 0, 100)
            cpu_input2 = torch.tensor([1]).to(torch.int32)
            npu_input2 = cpu_input2.npu()
            cpu_output = self.cpu_op_exec(cpu_input1, cpu_input2)
            npu_output = self.npu_op_exec(npu_input1, npu_input2)
            cpu_output = cpu_output.astype(npu_output.dtype)
            self.assertRtolEqual(cpu_output, npu_output)

    def test_rshift_scalar(self, device):
        format_list = [0]
        shape_list = [(256, 32, 56)]
        shape_format = [
            [np.int32, i, j] for i in format_list for j in shape_list
        ]
        for item in shape_format:
            cpu_input1, npu_input1 = create_common_tensor(item, 0, 100)
            cpu_input2 = torch.tensor(1).to(torch.int32)
            npu_input2 = cpu_input2.npu()
            cpu_output = self.cpu_op_exec(cpu_input1, cpu_input2)
            npu_output = self.npu_op_exec(npu_input1, npu_input2)
            cpu_output = cpu_output.astype(npu_output.dtype)
            self.assertRtolEqual(cpu_output, npu_output)

instantiate_device_type_tests(TestRshift, globals(), except_for='cpu')
if __name__ == "__main__":
    run_tests()
