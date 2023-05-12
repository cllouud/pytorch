#include "torch_npu/csrc/framework/utils/OpAdapter.h"
#include "torch_npu/csrc/aten/NPUNativeFunctions.h"

namespace at_npu {
namespace native {


at::Tensor& NPUNativeFunctions::adaptive_max_pool2d_backward_out(
    const at::Tensor& grad_output,
    const at::Tensor& self,
    const at::Tensor& indices,
    at::Tensor& grad_input) {
  auto inputsize = self.sizes();
  c10::SmallVector<int64_t, N> input_size;
  if (inputsize.size() == 3) {
      c10::SmallVector<int64_t, N> size = { inputsize[1], inputsize[2] };
      input_size = at::IntArrayRef(size);
  } else if (inputsize.size() == 4) {
      c10::SmallVector<int64_t, N> size = { inputsize[2], inputsize[3] };
      input_size = at::IntArrayRef(size);
  }
  c10::SmallVector<int64_t, N> output_size = {
      grad_output.size(grad_output.dim() - 2),
      grad_output.size(grad_output.dim() - 1)};

  if (input_size[0] % output_size[0] == 0 && input_size[1] % output_size[1] == 0) {
      int64_t kernel_size[2];
      int64_t stride[2];
      int64_t padding[2];
      int64_t strideH = input_size[0] / output_size[0];
      int64_t strideW = input_size[1] / output_size[1];
      int64_t kernel_sizeH = input_size[0] - (output_size[0] - 1) * strideH;
      int64_t kernel_sizeW = input_size[1] - (output_size[1] - 1) * strideW;
      stride[0] = strideH;
      stride[1] = strideW;
      kernel_size[0] = kernel_sizeH;
      kernel_size[1] = kernel_sizeW;
      padding[0] = padding[1] = 0;
      c10::SmallVector<int64_t, N> kernelSize = {1, kernel_size[0], kernel_size[1], 1};
      c10::SmallVector<int64_t, N> stridesSize = {1, stride[0], stride[1], 1};
      c10::SmallVector<int64_t, N> paddings = {1, padding[0], padding[1], 1};
      c10::SmallVector<int64_t, N> dilations = {1, 1, 1, 1};
      bool ceil_mode = false;
      OpCommand cmd;
      cmd.Name("MaxPoolGradWithArgmaxV1")
          .Input(self, "x", ACL_FORMAT_NCHW)
          .Input(grad_output, "grad", ACL_FORMAT_NCHW)
          .Input(indices, "argmax", ACL_FORMAT_NCHW, "uint16")
          .Output(grad_input, "y", ACL_FORMAT_NCHW)
          .Attr("ksize", kernelSize)
          .Attr("strides", stridesSize)
          .Attr("pads", paddings)
          .Attr("dilations", dilations)
          .Attr("ceil_mode", ceil_mode)
          .Run();
    } else {
        // H and W can not be divided, temporarily reported error processing
        AT_ERROR("H and W must be divisible");
    }
    return grad_input;
}

at::Tensor NPUNativeFunctions::adaptive_max_pool2d_backward(
    const at::Tensor& grad_output,
    const at::Tensor& self,
    const at::Tensor& indices) {
  TORCH_CHECK(
      (self.dim() == 3 || self.dim() == 4),
      "non-empty 3D or 4D (batch mode) tensor expected for input");
  at::Tensor grad_input = OpPreparation::ApplyTensorWithFormat(self, ACL_FORMAT_NC1HWC0);
  NPUNativeFunctions::adaptive_max_pool2d_backward_out(grad_output, self, indices, grad_input);
  return grad_input;
}


} // namespace native
} // namespace at_npu
