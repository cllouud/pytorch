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

import torch
import torch_npu

from torch_npu.testing.common_utils import TestCase, run_tests
from torch_npu.testing.common_device_type import instantiate_device_type_tests

class TestNmsRotated(TestCase):
    def npu_op_exec(self, det, score):
        output1, output2 = torch_npu.npu_nms_rotated(det.npu(), score.npu(), 0.2, 0, -1, 1)
        return output1, output2

    def test_nms_rotated_float32(self, device):
        det = torch.tensor([[1.0382e+03, 3.1657e+02, 1.1556e+03, 4.4303e+02, 2.3674e+00],
                            [1.1503e+03, 3.0598e+02, 1.2602e+03, 4.3456e+02, 3.2729e-01],
                            [1.1508e+03, 3.0652e+02, 1.2607e+03, 4.3472e+02, 5.1713e-01],
                            [1.1518e+03, 3.0781e+02, 1.2622e+03, 4.3448e+02, 3.9718e-01],
                            [1.1748e+03, 3.0202e+02, 1.2859e+03, 4.3915e+02, 1.8112e+00],
                            [1.1711e+03, 3.0480e+02, 1.2868e+03, 4.3551e+02, 2.1171e+00],
                            [1.1673e+03, 3.0675e+02, 1.2889e+03, 4.3194e+02, 2.5968e+00],
                            [1.2741e+03, 3.0181e+02, 1.3823e+03, 4.3036e+02, 2.0379e+00],
                            [1.2741e+03, 3.0286e+02, 1.3836e+03, 4.2940e+02, 2.2072e+00],
                            [1.2733e+03, 3.0382e+02, 1.3855e+03, 4.2846e+02, 2.0921e+00],
                            [1.2935e+03, 3.0517e+02, 1.3961e+03, 4.3137e+02, 2.9583e+00],
                            [1.4076e+03, 3.2173e+02, 1.4930e+03, 4.2714e+02, 2.6099e+00],
                            [1.4097e+03, 3.2496e+02, 1.4934e+03, 4.2651e+02, 3.0967e+00],
                            [1.4097e+03, 3.2569e+02, 1.4935e+03, 4.2632e+02, 2.5553e+00],
                            [1.0279e+03, 3.1883e+02, 1.1412e+03, 4.4646e+02, 1.2030e+00],
                            [1.0275e+03, 3.1776e+02, 1.1408e+03, 4.4641e+02, 1.2732e+00],
                            [1.0289e+03, 3.1694e+02, 1.1407e+03, 4.4510e+02, 9.4897e-01],
                            [1.0372e+03, 3.1233e+02, 1.1477e+03, 4.4521e+02, 1.4125e+00],
                            [1.0370e+03, 3.1564e+02, 1.1487e+03, 4.4317e+02, 1.6109e+00],
                            [1.0367e+03, 3.1682e+02, 1.1510e+03, 4.4020e+02, 1.4112e+00]])
        score = torch.tensor([0.9910, 0.9854, 0.9972, 0.9930, 0.4282, 0.5092, 0.6532, 0.9965, 0.9989,
                              0.9976, 0.3144, 0.9874, 0.9980, 0.9967, 0.9698, 0.9824, 0.9474, 0.9856, 0.9964, 0.9926])

        expect_output1 = torch.tensor([8, 12, 2, 18], dtype=torch.int32)
        expect_output2 = torch.tensor([4], dtype=torch.int32)
        npu_output1, npu_output2 = self.npu_op_exec(det, score)
        self.assertRtolEqual(expect_output1, npu_output1.cpu())
        self.assertRtolEqual(expect_output2, npu_output2.cpu())

instantiate_device_type_tests(TestNmsRotated, globals(), except_for='cpu')
if __name__ == "__main__":
    run_tests()