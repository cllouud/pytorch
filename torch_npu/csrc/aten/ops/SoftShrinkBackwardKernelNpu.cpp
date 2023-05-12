#include "torch_npu/csrc/framework/utils/OpAdapter.h"
#include "torch_npu/csrc/aten/NPUNativeFunctions.h"

namespace at_npu {
namespace native {

at::Tensor& softshrink_backward_out_nocheck(
    const at::Tensor& grad_output,
    const at::Tensor& self,
    at::Scalar lambd,
    at::Tensor& grad_input) {
  OpPreparation::CheckMemory({grad_output, self}, {grad_input});
  OpCommand cmd;
  cmd.Name("SoftShrinkGrad")
      .Input(grad_output)
      .Input(self)
      .Output(grad_input)
      .Attr("lambd", lambd)
      .Run();

  return grad_input;
}

at::Tensor& NPUNativeFunctions::softshrink_backward_out(
    const at::Tensor& grad_output,
    const at::Tensor& self,
    const at::Scalar& lambd,
    at::Tensor& grad_input) {

  OpPreparation::CheckOut(
      {self, grad_output},
      grad_input,
      self);

  if (!NpuUtils::check_match(&grad_input)) {
    at::Tensor contiguousResult = NpuUtils::format_contiguous(grad_input);
    softshrink_backward_out_nocheck(grad_output, self, lambd, contiguousResult);
    NpuUtils::format_fresh_view(grad_input, contiguousResult);
  } else {
    softshrink_backward_out_nocheck(grad_output, self, lambd, grad_input);  
  }

  return grad_input;
}

at::Tensor NPUNativeFunctions::softshrink_backward(
    const at::Tensor& grad_output,
    const at::Tensor& self,
    const at::Scalar& lambd) {
  at::Tensor grad_input = OpPreparation::ApplyTensor(self);

  softshrink_backward_out_nocheck(
      grad_output, self, lambd, grad_input);

  return grad_input;
}
} // namespace native
} // namespace at_npu
