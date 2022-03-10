# Copyright (c) 2020, Huawei Technologies.All rights reserved.
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

import copy

import torch
import torch_npu
import torch.nn.functional as F

from torch_npu.testing.testcase import TestCase, run_tests


class TestNonLiACFunctions(TestCase):
    def test_threshold(self):
        input1 = torch.randn(2)
        cpu_output = F.threshold(input1, threshold=1, value=2)
        input1 = input1.npu()
        npu_output = F.threshold(input1, threshold=1, value=2)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_threshold_(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.threshold_(input1, threshold=1, value=2)
        npu_output = F.threshold_(npu_input, threshold=1, value=2)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_relu(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.relu(input1)
        npu_output = F.relu(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_relu_(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.relu_(input1)
        npu_output = F.relu_(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_hardtanh(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.hardtanh(input1)
        npu_output = F.hardtanh(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_hardtanh_(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.hardtanh_(input1)
        npu_output = F.hardtanh_(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_relu6(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.relu6(input1)
        npu_output = F.relu6(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_celu(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.celu(input1)
        npu_output = F.celu(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())
      
    def test_leaky_relu(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.leaky_relu(input1)
        npu_output = F.leaky_relu(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_leaky_relu_(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.leaky_relu_(input1)
        npu_output = F.leaky_relu_(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())
      
    def test_prelu(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        weight = torch.randn(1)
        npu_weight = copy.deepcopy(weight).npu()
        cpu_output = F.prelu(input1, weight=weight)
        npu_output = F.prelu(npu_input, weight=npu_weight)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_rrelu(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.rrelu(input1)
        npu_output = F.rrelu(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_rrelu_(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.rrelu_(input1)
        npu_output = F.rrelu_(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_glu(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.glu(input1)
        npu_output = F.glu(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_gelu(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.gelu(input1)
        npu_output = F.gelu(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_tanhshrink(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.tanhshrink(input1)
        npu_output = F.tanhshrink(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_softsign(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.softsign(input1)
        npu_output = F.softsign(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_softplus(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.softplus(input1)
        npu_output = F.softplus(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_softmin(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.softmin(input1)
        npu_output = F.softmin(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_softmax(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.softmax(input1)
        npu_output = F.softmax(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_log_softmax(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.log_softmax(input1)
        npu_output = F.log_softmax(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_tanh(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.tanh(input1)
        npu_output = F.tanh(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())

    def test_sigmoid(self):
        input1 = torch.randn(2)
        npu_input = copy.deepcopy(input1).npu()
        cpu_output = F.sigmoid(input1)
        npu_output = F.sigmoid(npu_input)

        self.assertRtolEqual(cpu_output.numpy(), npu_output.cpu().numpy())


if __name__ == "__main__":
    torch.npu.set_device(0)
    run_tests()