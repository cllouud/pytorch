// Copyright (c) 2020 Huawei Technologies Co., Ltd
// All rights reserved.
//
// Licensed under the BSD 3-Clause License  (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at_npu
//
// https://opensource.org/licenses/BSD-3-Clause
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef __PULGIN_NATIVE_NPU_UTILS_OP_TEMPLATE__
#define __PULGIN_NATIVE_NPU_UTILS_OP_TEMPLATE__

#include <functional>

#include "torch_npu/csrc/framework/OpCommandBase.h"
#include "torch_npu/csrc/framework/utils/OpPreparation.h"

namespace at_npu
{
  namespace native
  {

    class OpCommand : public OpCommandBase<OpCommand>
    {
    public:
      using FUNC_TYPE = std::function<std::tuple<bool, at::Tensor &>(void)>;
      OpCommand &InputWithFunc(const FUNC_TYPE &func);
      OpCommand &Inputs(const at::TensorList &inputs);
      OpCommand &InputPair(const at::Tensor &npu_input, const at::Tensor &cpu_input);
    }; // class OpCommand

  } // namespace native
} // namespace at_npu

#endif