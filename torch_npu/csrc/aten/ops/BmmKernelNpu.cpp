#include "torch_npu/csrc/core/npu/register/OptionsManager.h"
#include "torch_npu/csrc/core/npu/NpuVariables.h"
#include "torch_npu/csrc/framework/utils/OpAdapter.h"
#include "torch_npu/csrc/framework/utils/CalcuOpUtil.h"
#include "torch_npu/csrc/aten/NPUNativeFunctions.h"

namespace at_npu {
namespace native {

at::Tensor& NPUNativeFunctions::bmm_out(const at::Tensor& self, const at::Tensor& mat2, at::Tensor& result) {
  at::Tensor contiguousResult = result.is_contiguous() ? result : result.contiguous();

  at::Tensor contiguousSelf = self;
  at::Tensor contiguousMat2 = mat2;
  bool isSelfT = CalcuOpUtil::IsTransposeLastTwoDims(self);
  bool isMat2T = CalcuOpUtil::IsTransposeLastTwoDims(mat2);

  if(!isSelfT){
    contiguousSelf = NpuUtils::format_contiguous_add_copy_optimize(self);
  }
  if(!isMat2T){
    contiguousMat2 = NpuUtils::format_contiguous_add_copy_optimize(mat2);
  }

  // executing the NPU operator
  OpCommand cmd;
  cmd.Name("BatchMatMul")
      .InputWithoutContiguous(contiguousSelf)
      .InputWithoutContiguous(contiguousMat2)
      .Output(contiguousResult)
      .Attr("adj_x1", isSelfT)
      .Attr("adj_x2", isMat2T)
      .Run();

  if (!result.is_contiguous()) {
    result.copy_(contiguousResult);
  }
  return result;
}

at::Tensor NPUNativeFunctions::bmm(const at::Tensor& self, const at::Tensor& mat2) {
  // calculate the output size
  auto outputSize = {self.size(0), self.size(1), mat2.size(2)};

  // construct the output tensor of the NPU
  at::Tensor result;
  bool need_nd_out = false;
  // 检查是否指定mm输出为NCHW。待NLP模型总体策略制定后删去
  if ((self.scalar_type() == at::ScalarType::Half)) {
    // check is 16-algined with high-performance
    auto isAligin = [&]() {
      return (!(static_cast<uint64_t>(self.size(1)) & 0x0000000F)) &&
             (!(static_cast<uint64_t>(self.size(2)) & 0x0000000F)) &&
             (!(static_cast<uint64_t>(mat2.size(1)) & 0x0000000F)) &&
             (!(static_cast<uint64_t>(mat2.size(2)) & 0x0000000F));
    };
    static auto mm_bmm_nd = !env::CheckMmBmmNDDisable();
    static bool is_support_nd_out = c10_npu::GetSocVersion() >= c10_npu::SocVersion::Ascend910B1;
    // There is a data trampling problem in non-aligned scenes. For the time being, only aligned scenes are supported.
    if (FormatHelper::IsBaseFormatType(self) && FormatHelper::IsBaseFormatType(mat2) &&
        mm_bmm_nd && ((is_support_nd_out && CalcuOpUtil::IsNdToNzOnTheFly(self, mat2)) ||
        (!is_support_nd_out && isAligin()))) {
      result = OpPreparation::ApplyTensorWithFormat(outputSize, self.options(), ACL_FORMAT_ND);
    } else {
      result = OpPreparation::ApplyTensorWithFormat(outputSize, self.options(), ACL_FORMAT_FRACTAL_NZ, true);
      need_nd_out = mm_bmm_nd;
    }
  } else {
    result = OpPreparation::ApplyTensorWithFormat(outputSize, self.options(), ACL_FORMAT_ND);
  }

  // calculate the output result of the NPU
  NPUNativeFunctions::bmm_out(self, mat2, result);
  if (need_nd_out) {
    result = NPUNativeFunctions::npu_format_cast(result, ACL_FORMAT_ND);
  }
  return result;
}

} // namespace native
} // namespace at
